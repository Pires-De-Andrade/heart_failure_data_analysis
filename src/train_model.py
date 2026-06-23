"""
train_model.py — Treino, avaliação e interpretação da regressão logística.

Pipeline completo da Fase 1 (modelo preditivo):
    1. Carrega `dataset/raw/heart.csv` e separa features/alvo.
    2. Split estratificado treino/teste com semente fixa (reprodutível).
    3. Pré-processa (zeros bio-impossíveis → mediana, one-hot, padronização)
       e treina uma `LogisticRegression` dentro de um `Pipeline`.
    4. Avalia no test set (acurácia, precisão, recall, F1, AUC, matriz de
       confusão, curva ROC) e salva tabelas/figuras em `output/`.
    5. Converte coeficientes em odds-ratios e salva o ranking em `output/`.
    6. Persiste o pipeline completo em `models/logistic_model.joblib`.

Uso:
    python -m src.train_model

Funções:
    build_pipeline()      → Pipeline (pré-processador + LogisticRegression)
    load_xy()             → (X, y) prontos para split
    evaluate()            → dict de métricas + salva tabelas/figuras
    odds_ratios_table()   → DataFrame com coef, odds-ratio e ranking
    main()                → orquestra todo o fluxo e grava os artefatos
"""

import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import (
    DATA_RAW,
    TARGET,
    MODEL_FEATURES,
    MODEL_NUM_FEATURES,
    MODEL_CAT_FEATURES,
    ZERO_AS_MISSING,
    RANDOM_STATE,
    TEST_SIZE,
    OUTPUT_FIGURES,
    OUTPUT_TABLES,
    MODELS_DIR,
    MODEL_PATH,
    PALETTE_HD_LIST,
    COLOR_DISEASE,
    DPI,
)
from .explain import (
    readable_feature_names,
    transform,
    build_explainer,
    shap_values,
)


def load_xy() -> tuple[pd.DataFrame, pd.Series]:
    """
    Carrega o CSV bruto e devolve (X, y).

    Os zeros biologicamente impossíveis em Cholesterol/RestingBP são
    convertidos em ``NaN`` aqui — a imputação pela mediana acontece dentro
    do pipeline (ajustada só no treino, sem vazamento). Decisão consistente
    com a análise descritiva v1, que trata esses zeros como dado ausente.
    """
    df = pd.read_csv(DATA_RAW)
    X = df[MODEL_FEATURES].copy()
    for col in ZERO_AS_MISSING:
        X[col] = X[col].replace(0, np.nan)
    y = df[TARGET].astype(int)
    return X, y


def build_pipeline() -> Pipeline:
    """
    Constrói o pipeline: pré-processador + regressão logística.

    - Numéricas: imputa mediana (cobre os zeros → NaN) e padroniza.
      A padronização torna os coeficientes/odds-ratios comparáveis entre si.
    - Categóricas: one-hot encoding (drop=None para manter todas as classes
      interpretáveis no relatório de odds-ratios).
    """
    num_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    cat_pipe = Pipeline(
        steps=[
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_pipe, MODEL_NUM_FEATURES),
            ("cat", cat_pipe, MODEL_CAT_FEATURES),
        ]
    )
    model = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)
    return Pipeline(steps=[("prep", preprocessor), ("clf", model)])


def _feature_names(pipe: Pipeline) -> list[str]:
    """Nomes das features após o one-hot, na ordem usada pelo classificador."""
    return list(pipe.named_steps["prep"].get_feature_names_out())


def evaluate(pipe: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """
    Avalia o pipeline no test set e salva tabelas/figuras.

    Salva:
        output/tables/pred_metrics.csv          (acurácia, precisão, ...)
        output/tables/pred_confusion_matrix.csv (matriz de confusão)
        output/figures/05_confusion_matrix.png
        output/figures/05_roc_curve.png

    Retorna o dicionário de métricas.
    """
    y_pred = pipe.predict(X_test)
    y_proba = pipe.predict_proba(X_test)[:, 1]

    metrics = {
        "acuracia": accuracy_score(y_test, y_pred),
        "precisao": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "auc": roc_auc_score(y_test, y_proba),
        "n_test": int(len(y_test)),
    }

    # --- Tabela de métricas ---
    metrics_df = pd.DataFrame(
        {"metrica": list(metrics.keys()), "valor": list(metrics.values())}
    )
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(OUTPUT_TABLES / "pred_metrics.csv", index=False)

    # --- Matriz de confusão (tabela + figura) ---
    cm = confusion_matrix(y_test, y_pred)
    cm_df = pd.DataFrame(
        cm,
        index=["Real: Sem doença", "Real: Com doença"],
        columns=["Prev: Sem doença", "Prev: Com doença"],
    )
    cm_df.to_csv(OUTPUT_TABLES / "pred_confusion_matrix.csv")

    OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="RdPu")
    ax.set_xticks([0, 1], ["Sem doença", "Com doença"])
    ax.set_yticks([0, 1], ["Sem doença", "Com doença"])
    ax.set_xlabel("Classe prevista")
    ax.set_ylabel("Classe real")
    ax.set_title("Matriz de Confusão (test set)", fontweight="bold")
    thresh = cm.max() / 2
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j, i, f"{cm[i, j]}",
                ha="center", va="center",
                color="white" if cm[i, j] > thresh else "black",
                fontsize=14, fontweight="bold",
            )
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(OUTPUT_FIGURES / "05_confusion_matrix.png", dpi=DPI)
    plt.close(fig)

    # --- Curva ROC ---
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color=COLOR_DISEASE, lw=2, label=f"AUC = {metrics['auc']:.3f}")
    ax.plot([0, 1], [0, 1], color="#888888", lw=1, linestyle="--", label="Acaso")
    ax.set_xlabel("Taxa de falsos positivos (1 − especificidade)")
    ax.set_ylabel("Taxa de verdadeiros positivos (sensibilidade)")
    ax.set_title("Curva ROC (test set)", fontweight="bold")
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTPUT_FIGURES / "05_roc_curve.png", dpi=DPI)
    plt.close(fig)

    return metrics


def odds_ratios_table(pipe: Pipeline) -> pd.DataFrame:
    """
    Converte os coeficientes da logística em odds-ratios interpretáveis.

    Como as numéricas são padronizadas e as categóricas viram dummies, a
    magnitude de ``|coeficiente|`` é comparável entre variáveis e serve de
    medida de importância. Retorna uma linha por feature (pós one-hot),
    ordenada por importância decrescente, e salva em
    ``output/tables/pred_odds_ratios.csv``.
    """
    clf = pipe.named_steps["clf"]
    names = _feature_names(pipe)
    coefs = clf.coef_.ravel()

    df = pd.DataFrame(
        {
            "feature": names,
            "coeficiente": coefs,
            "odds_ratio": np.exp(coefs),
            "importancia_abs": np.abs(coefs),
        }
    )
    df = df.sort_values("importancia_abs", ascending=False).reset_index(drop=True)
    df.insert(0, "ranking", np.arange(1, len(df) + 1))

    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_TABLES / "pred_odds_ratios.csv", index=False)
    return df


def shap_global_artifacts(pipe: Pipeline, X_train: pd.DataFrame) -> pd.DataFrame:
    """
    Gera os artefatos SHAP globais (milestone v2.1, XAI-01/XAI-02).

    Ajusta um `LinearExplainer` no conjunto de treino transformado e calcula
    o SHAP (log-odds, exato) para todas as linhas de treino. Salva:

        output/tables/shap_global.npz   → values, base_value, data, feature_names
        output/figures/06_shap_beeswarm.png

    Os nomes de features são os rótulos legíveis ("ST_Slope = Up"), não os
    internos pós one-hot. Retorna o ranking de importância (mean |SHAP|).
    """
    import shap

    feature_names = readable_feature_names(pipe)
    explainer = build_explainer(pipe, X_train)
    Xt = transform(pipe, X_train)
    expl = shap_values(explainer, Xt, feature_names)

    # --- Persistência dos valores (consumidos pelo dashboard sem recomputar) ---
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    np.savez(
        OUTPUT_TABLES / "shap_global.npz",
        values=expl.values,
        base_value=np.asarray(expl.base_values),
        data=expl.data,
        feature_names=np.array(feature_names, dtype=object),
    )

    # --- Beeswarm global (direção + magnitude por feature) ---
    OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)
    fig = plt.figure()
    shap.plots.beeswarm(expl, show=False, max_display=len(feature_names))
    fig = plt.gcf()
    fig.suptitle("Importância SHAP (log-odds) — global", fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUTPUT_FIGURES / "06_shap_beeswarm.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)

    # --- Ranking de importância (mean |SHAP|) ---
    mean_abs = np.abs(expl.values).mean(axis=0)
    ranking = (
        pd.DataFrame({"feature": feature_names, "mean_abs_shap": mean_abs})
        .sort_values("mean_abs_shap", ascending=False)
        .reset_index(drop=True)
    )
    return ranking


def main() -> None:
    """Orquestra split → treino → avaliação → interpretação → persistência."""
    print("→ Carregando dados...")
    X, y = load_xy()
    print(f"  X: {X.shape}, prevalência y=1: {y.mean():.3f}")

    print("→ Split estratificado treino/teste (random_state fixo)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE,
    )
    print(
        f"  treino: {X_train.shape[0]} (y=1: {y_train.mean():.3f}) | "
        f"teste: {X_test.shape[0]} (y=1: {y_test.mean():.3f})"
    )

    print("→ Treinando regressão logística...")
    pipe = build_pipeline()
    pipe.fit(X_train, y_train)

    print("→ Avaliando no test set...")
    metrics = evaluate(pipe, X_test, y_test)
    for k, v in metrics.items():
        print(f"    {k:>10}: {v:.4f}" if isinstance(v, float) else f"    {k:>10}: {v}")

    print("→ Calculando odds-ratios...")
    odds = odds_ratios_table(pipe)
    print("  Top 5 variáveis por importância:")
    for _, row in odds.head(5).iterrows():
        print(
            f"    {row['ranking']}. {row['feature']:<28} "
            f"OR={row['odds_ratio']:.3f}  (coef={row['coeficiente']:+.3f})"
        )

    print("→ Gerando explicabilidade SHAP (global)...")
    shap_rank = shap_global_artifacts(pipe, X_train)
    print("  Top 5 variáveis por mean |SHAP|:")
    for i, row in shap_rank.head(5).iterrows():
        print(f"    {i + 1}. {row['feature']:<34} {row['mean_abs_shap']:.4f}")

    print("→ Persistindo modelo...")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, MODEL_PATH)
    print(f"  Modelo salvo em: {MODEL_PATH}")

    print("\n✓ Concluído. Artefatos:")
    print(f"  - {MODEL_PATH}")
    print(f"  - {OUTPUT_TABLES / 'pred_metrics.csv'}")
    print(f"  - {OUTPUT_TABLES / 'pred_confusion_matrix.csv'}")
    print(f"  - {OUTPUT_TABLES / 'pred_odds_ratios.csv'}")
    print(f"  - {OUTPUT_TABLES / 'shap_global.npz'}")
    print(f"  - {OUTPUT_FIGURES / '05_confusion_matrix.png'}")
    print(f"  - {OUTPUT_FIGURES / '05_roc_curve.png'}")
    print(f"  - {OUTPUT_FIGURES / '06_shap_beeswarm.png'}")


if __name__ == "__main__":
    main()
