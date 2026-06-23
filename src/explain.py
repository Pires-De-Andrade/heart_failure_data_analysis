"""
explain.py — Explicabilidade SHAP da regressão logística (milestone v2.1).

Camada complementar aos odds-ratios: usa `shap.LinearExplainer` sobre o
classificador extraído do pipeline, no espaço transformado (pós one-hot +
padronização). Para um modelo linear, o SHAP é exato e analítico — não há
aproximação nem custo de amostragem como no `KernelExplainer`.

Decisões travadas (PROJECT.md / REQUIREMENTS.md):
    - Espaço de explicação: log-odds (mantém a aditividade de Shapley).
    - Labels legíveis ("ST_Slope = Up") em vez dos nomes internos
      pós one-hot ("cat__ST_Slope_Up").
    - Background = dados de treino transformados (mediana/expectativa do
      explainer), com seed fixa para reprodutibilidade.

Funções:
    readable_feature_names(pipe) → list[str] rótulos legíveis por coluna
    transform(pipe, X)           → ndarray no espaço do classificador
    build_explainer(pipe, X_bg)  → shap.LinearExplainer ajustado no background
    shap_values(explainer, Xt)   → shap.Explanation (log-odds)
"""

import numpy as np
import pandas as pd
import shap

from sklearn.pipeline import Pipeline

from .config import VAR_LABELS, CAT_LABELS, RANDOM_STATE


def _split_internal_name(name: str) -> tuple[str, str | None]:
    """
    Decompõe o nome interno pós-ColumnTransformer em (variável, categoria).

    Exemplos:
        "num__Age"          → ("Age", None)
        "cat__ST_Slope_Up"  → ("ST_Slope", "Up")
        "cat__Sex_F"        → ("Sex", "F")
    """
    # Remove o prefixo do transformer ("num__" / "cat__").
    _, _, rest = name.partition("__")
    if name.startswith("num__"):
        return rest, None
    # Categórica: a variável é a chave conhecida; o resto é a categoria.
    for var in CAT_LABELS:
        prefix = f"{var}_"
        if rest.startswith(prefix):
            return var, rest[len(prefix):]
    # Fallback: divide no último underscore.
    var, _, cat = rest.rpartition("_")
    return (var or rest), (cat or None)


def readable_feature_names(pipe: Pipeline) -> list[str]:
    """
    Converte os nomes pós one-hot em rótulos legíveis para os plots SHAP.

    Numéricas → rótulo curto da variável (ex: "Idade").
    Categóricas → "Variável = Categoria" com rótulos de CAT_LABELS quando
    disponíveis (ex: "Inclinação ST = Ascendente").
    """
    raw_names = list(pipe.named_steps["prep"].get_feature_names_out())
    labels = []
    for name in raw_names:
        var, cat = _split_internal_name(name)
        var_label = VAR_LABELS.get(var, var)
        if cat is None:
            labels.append(var_label)
        else:
            cat_label = CAT_LABELS.get(var, {}).get(cat, cat)
            labels.append(f"{var_label} = {cat_label}")
    return labels


def transform(pipe: Pipeline, X: pd.DataFrame) -> np.ndarray:
    """Aplica o pré-processador do pipeline, devolvendo a matriz densa."""
    Xt = pipe.named_steps["prep"].transform(X)
    return np.asarray(Xt)


def build_explainer(pipe: Pipeline, X_background: pd.DataFrame) -> shap.LinearExplainer:
    """
    Constrói o `LinearExplainer` sobre o classificador extraído do pipeline.

    O background (tipicamente o conjunto de treino transformado) define a
    expectativa de referência. Resultado em log-odds, exato para a logística.
    """
    clf = pipe.named_steps["clf"]
    Xt_bg = transform(pipe, X_background)
    # `masker` com seed fixa garante reprodutibilidade da referência.
    masker = shap.maskers.Independent(Xt_bg, max_samples=len(Xt_bg))
    return shap.LinearExplainer(clf, masker, seed=RANDOM_STATE)


def shap_values(
    explainer: shap.LinearExplainer,
    Xt: np.ndarray,
    feature_names: list[str],
) -> shap.Explanation:
    """
    Calcula a `Explanation` SHAP (log-odds) para as linhas transformadas `Xt`,
    já anexando os rótulos legíveis das features.
    """
    expl = explainer(Xt)
    expl.feature_names = feature_names
    return expl
