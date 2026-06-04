"""
descriptive_stats.py — Funções para cálculo de medidas descritivas.

Todas as medidas são calculadas sobre valores individuais brutos,
exceto quando explicitamente indicado (dados agrupados em classes).

Coeficiente de assimetria:
    Valor reportado → Pearson 2: AS = 3 × (média − mediana) / σ
    scipy.stats.skew() → apenas verificação interna (nunca reportado)
"""

import numpy as np
import pandas as pd
from scipy import stats as sp_stats


def pearson2_skewness(series: pd.Series) -> float:
    """
    Coeficiente de assimetria de Pearson (2ª forma):
        AS = 3 × (média − mediana) / desvio-padrão

    Este é o coeficiente reportado em todas as análises do trabalho.
    """
    mean = series.mean()
    median = series.median()
    std = series.std(ddof=1)
    if std == 0:
        return 0.0
    return 3 * (mean - median) / std


def descriptive_summary(series: pd.Series, name: str = "") -> pd.DataFrame:
    """
    Calcula todas as medidas descritivas sobre valores individuais brutos.

    Retorna DataFrame com uma coluna 'Valor' e índice com os nomes
    das medidas.

    Parâmetros
    ----------
    series : pd.Series
        Série numérica com valores individuais (não agrupados).
    name : str
        Nome da variável (para título).
    """
    n = len(series)
    mean = series.mean()
    median = series.median()
    mode_result = series.mode()
    mode_val = mode_result.iloc[0] if len(mode_result) > 0 else np.nan
    variance = series.var(ddof=1)
    std = series.std(ddof=1)
    cv = (std / mean) * 100 if mean != 0 else np.nan
    amplitude = series.max() - series.min()
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1

    # Assimetria — Pearson 2 (valor reportado)
    skew_pearson2 = pearson2_skewness(series)

    # Verificação interna — scipy.stats.skew (NÃO reportar)
    # skew_scipy = sp_stats.skew(series, bias=False)
    # Registrado apenas como verificação cruzada no código.

    # Curtose (excesso de curtose, base normal = 0)
    kurtosis = sp_stats.kurtosis(series, bias=False)

    results = {
        "n": n,
        "Média": round(mean, 4),
        "Mediana": round(median, 4),
        "Moda": round(mode_val, 4) if not np.isnan(mode_val) else "N/A",
        "Variância": round(variance, 4),
        "Desvio-padrão (σ)": round(std, 4),
        "Coef. Variação (CV%)": round(cv, 2),
        "Amplitude": round(amplitude, 4),
        "Q1 (25%)": round(q1, 4),
        "Q2 / Mediana (50%)": round(median, 4),
        "Q3 (75%)": round(q3, 4),
        "IQR (Q3 − Q1)": round(iqr, 4),
        "Assimetria (Pearson 2)": round(skew_pearson2, 4),
        "Curtose (excesso)": round(kurtosis, 4),
    }

    df = pd.DataFrame.from_dict(results, orient="index", columns=["Valor"])
    df.index.name = "Medida"
    if name:
        df.columns = [name]

    return df


def descriptive_by_group(
    df: pd.DataFrame, var: str, group: str = "HeartDisease"
) -> pd.DataFrame:
    """
    Calcula medidas descritivas separadas por grupo (HeartDisease=0/1).

    Retorna DataFrame com uma coluna por grupo.
    """
    summaries = {}
    for grp_val, grp_df in df.groupby(group):
        label = f"{'Sem doença' if grp_val == 0 else 'Com doença'}"
        s = descriptive_summary(grp_df[var], name=label)
        summaries[label] = s.iloc[:, 0]

    result = pd.DataFrame(summaries)
    result.index.name = "Medida"
    return result


def interpret_skewness(as_value: float) -> str:
    """Interpreta o coeficiente de assimetria de Pearson 2."""
    if abs(as_value) < 0.15:
        return "Distribuição aproximadamente simétrica"
    elif as_value > 0:
        return "Assimetria positiva (cauda à direita)"
    else:
        return "Assimetria negativa (cauda à esquerda)"


def interpret_kurtosis(k_value: float) -> str:
    """Interpreta a curtose (excesso, base normal = 0)."""
    if abs(k_value) < 0.5:
        return "Mesocúrtica (próxima da normal)"
    elif k_value > 0:
        return "Leptocúrtica (caudas pesadas)"
    else:
        return "Platicúrtica (caudas leves)"
