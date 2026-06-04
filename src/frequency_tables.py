"""
frequency_tables.py — Tabelas de frequência (fi, fri, Fi, Fri).

Funções:
    freq_table_qualitative()  → para variáveis categóricas
    freq_table_classes()      → para variáveis numéricas com classes
    freq_table_crosstab()     → cruzamento de qualitativa × HeartDisease
"""

import numpy as np
import pandas as pd


def freq_table_qualitative(
    series: pd.Series,
    sort_by_freq: bool = True,
) -> pd.DataFrame:
    """
    Tabela de frequência para variável qualitativa.

    Colunas: fi (frequência absoluta), fri (%), Fi (acumulada), Fri (% acum.)
    """
    fi = series.value_counts(sort=sort_by_freq)
    fri = (fi / fi.sum()) * 100
    Fi = fi.cumsum()
    Fri = fri.cumsum()

    table = pd.DataFrame({
        "fi": fi,
        "fri (%)": fri.round(2),
        "Fi": Fi,
        "Fri (%)": Fri.round(2),
    })
    table.index.name = series.name or "Categoria"
    return table


def freq_table_classes(
    series: pd.Series,
    bins: list | np.ndarray | None = None,
    labels: list[str] | None = None,
    k: int | None = None,
) -> pd.DataFrame:
    """
    Tabela de frequência para variável numérica com classes.

    Se ``bins`` e ``labels`` forem fornecidos, usa esses intervalos.
    Caso contrário, calcula ``k`` classes pela regra de Sturges:
        k = 1 + 3.322 × log₁₀(n)

    Colunas: fi, fri (%), Fi, Fri (%)
    """
    if bins is None:
        bins = sturges_bins(series, k)

    # Criar intervalos
    if labels is not None:
        cuts = pd.cut(series, bins=bins, labels=labels,
                       include_lowest=True, right=False)
    else:
        cuts = pd.cut(series, bins=bins, include_lowest=True, right=False)

    fi = cuts.value_counts(sort=False)
    fri = (fi / fi.sum()) * 100
    Fi = fi.cumsum()
    Fri = fri.cumsum()

    table = pd.DataFrame({
        "fi": fi,
        "fri (%)": fri.round(2),
        "Fi": Fi,
        "Fri (%)": Fri.round(2),
    })
    table.index.name = "Classe"
    return table


def sturges_k(n: int) -> int:
    """Número de classes pela regra de Sturges: k = 1 + 3.322 × log₁₀(n)."""
    return int(np.ceil(1 + 3.322 * np.log10(n)))


def sturges_bins(series: pd.Series, k: int | None = None) -> np.ndarray:
    """
    Retorna os limites das classes pela regra de Sturges.
    Útil para passar diretamente ao matplotlib/seaborn.
    """
    n = len(series)
    if k is None:
        k = sturges_k(n)
        
    min_val = series.min()
    max_val = series.max()
    epsilon = (max_val - min_val) * 1e-5 if max_val != min_val else 1e-5
    
    return np.linspace(min_val, max_val + epsilon, k + 1)


def freq_table_crosstab(
    df: pd.DataFrame,
    var: str,
    group: str = "HeartDisease",
) -> pd.DataFrame:
    """
    Tabela cruzada: variável qualitativa × HeartDisease.

    Retorna contagens absolutas e percentuais por grupo.
    """
    ct = pd.crosstab(df[var], df[group], margins=True, margins_name="Total")

    # Adicionar percentuais por coluna
    ct_pct = pd.crosstab(
        df[var], df[group], normalize="columns", margins=False
    ) * 100
    ct_pct = ct_pct.round(1)
    ct_pct.columns = [f"% {'Sem doença' if c == 0 else 'Com doença'}"
                       for c in ct_pct.columns]

    result = pd.concat([ct, ct_pct], axis=1)
    result.index.name = var
    return result
