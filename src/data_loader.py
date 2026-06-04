"""
data_loader.py — Carga e limpeza do dataset Heart Disease.

Funções:
    load_raw()     → DataFrame com 918 linhas (dados brutos)
    load_subsets() → dict com df_full, df_chol, df_bp
"""

import pandas as pd
from .config import DATA_RAW


def load_raw() -> pd.DataFrame:
    """Carrega o CSV bruto sem nenhuma transformação."""
    df = pd.read_csv(DATA_RAW)
    return df


def load_subsets() -> dict[str, pd.DataFrame]:
    """
    Retorna dicionário com três versões do dataset:

    - ``df_full``  (n=918): dataset completo, para análises que não
      envolvem Cholesterol nem RestingBP.
    - ``df_chol``  (n=746): exclui linhas com Cholesterol == 0
      (172 observações com valor biologicamente impossível).
    - ``df_bp``    (n=917): exclui linhas com RestingBP == 0
      (1 observação com pressão arterial zero).

    Decisão documentada: zeros nessas variáveis representam dados
    ausentes codificados — não são valores reais.
    """
    df_full = load_raw()

    # Cholesterol == 0 → dado ausente (172 linhas)
    df_chol = df_full[df_full["Cholesterol"] != 0].copy()

    # RestingBP == 0 → dado ausente (1 linha: paciente 55/M/NAP)
    df_bp = df_full[df_full["RestingBP"] != 0].copy()

    return {
        "df_full": df_full,
        "df_chol": df_chol,
        "df_bp": df_bp,
    }
