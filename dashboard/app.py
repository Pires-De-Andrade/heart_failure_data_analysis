"""
app.py — Dashboard interativo (Streamlit) do Heart Failure Prediction.

Apresenta a análise descritiva da v1 de forma reativa (filtros por Sexo,
Doença Cardíaca e faixa etária) e expõe um formulário de predição ao vivo
que consome o modelo da Fase 1 (`models/logistic_model.joblib`).

Uso:
    streamlit run dashboard/app.py

Seções:
    Visão Geral · Qualitativas · Idade · Contínuas · Predição

Reaproveita `src/` (config, data_loader, frequency_tables, descriptive_stats)
e os artefatos persistidos em `models/`. Dados e modelo são carregados via
cache do Streamlit (carregados uma única vez, não a cada interação).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import streamlit as st

# Permite importar o pacote src/ ao rodar via `streamlit run`.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    TARGET,
    QUAL_VARS,
    CONT_VARS,
    DISC_VAR,
    AGE_BINS,
    AGE_LABELS,
    VAR_LABELS,
    CAT_LABELS,
    MODEL_FEATURES,
    MODEL_NUM_FEATURES,
    MODEL_CAT_FEATURES,
    MODEL_PATH,
    COLOR_HEALTHY,
    COLOR_DISEASE,
    PALETTE_HD_LIST,
)
from src.data_loader import load_raw
from src.frequency_tables import freq_table_crosstab
from src.descriptive_stats import descriptive_summary, pearson2_skewness


# ---------------------------------------------------------------------------
# Carregamento com cache (dados e modelo carregados uma única vez)
# ---------------------------------------------------------------------------
@st.cache_data
def get_data() -> pd.DataFrame:
    """Carrega o dataset bruto (cache: lido uma vez por sessão)."""
    return load_raw()


@st.cache_resource
def get_model():
    """Carrega o pipeline da Fase 1 (cache de recurso: uma única instância)."""
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


def hd_label(v: int) -> str:
    """Rótulo legível para HeartDisease (0/1)."""
    return CAT_LABELS[TARGET][int(v)]


# ---------------------------------------------------------------------------
# Filtros reativos (sidebar)
# ---------------------------------------------------------------------------
def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica os filtros da sidebar e devolve o recorte filtrado."""
    st.sidebar.header("Filtros")

    sexes = sorted(df["Sex"].unique())
    sel_sex = st.sidebar.multiselect(
        "Sexo",
        options=sexes,
        default=sexes,
        format_func=lambda s: CAT_LABELS["Sex"][s],
    )

    hd_opts = [0, 1]
    sel_hd = st.sidebar.multiselect(
        VAR_LABELS[TARGET],
        options=hd_opts,
        default=hd_opts,
        format_func=hd_label,
    )

    age_min, age_max = int(df[DISC_VAR].min()), int(df[DISC_VAR].max())
    sel_age = st.sidebar.slider(
        "Faixa etária (anos)",
        min_value=age_min,
        max_value=age_max,
        value=(age_min, age_max),
    )

    mask = (
        df["Sex"].isin(sel_sex)
        & df[TARGET].isin(sel_hd)
        & df[DISC_VAR].between(sel_age[0], sel_age[1])
    )
    out = df[mask].copy()

    st.sidebar.markdown("---")
    st.sidebar.metric("Pacientes no recorte", f"{len(out)}")
    st.sidebar.caption(f"de {len(df)} no total")
    return out


# ---------------------------------------------------------------------------
# Seção: Visão Geral
# ---------------------------------------------------------------------------
def section_overview(df: pd.DataFrame) -> None:
    st.header("Visão Geral")
    n = len(df)
    if n == 0:
        st.warning("Nenhum paciente no recorte atual. Ajuste os filtros.")
        return

    prev = df[TARGET].mean()
    c1, c2, c3 = st.columns(3)
    c1.metric("Pacientes", f"{n}")
    c2.metric("Com doença cardíaca", f"{(df[TARGET] == 1).sum()}")
    c3.metric("Prevalência", f"{prev:.1%}")

    counts = df[TARGET].value_counts().reindex([0, 1], fill_value=0)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(
        [hd_label(0), hd_label(1)],
        counts.values,
        color=PALETTE_HD_LIST,
    )
    for i, v in enumerate(counts.values):
        ax.text(i, v, str(v), ha="center", va="bottom", fontweight="bold")
    ax.set_ylabel("Nº de pacientes")
    ax.set_title("Distribuição de Doença Cardíaca")
    st.pyplot(fig)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Seção: Qualitativas
# ---------------------------------------------------------------------------
def section_qualitative(df: pd.DataFrame) -> None:
    st.header("Variáveis Qualitativas")
    if len(df) == 0:
        st.warning("Nenhum paciente no recorte atual. Ajuste os filtros.")
        return

    var = st.selectbox(
        "Variável",
        options=QUAL_VARS,
        format_func=lambda v: VAR_LABELS[v],
    )

    # Tabela de contingência variável × HeartDisease sobre o recorte filtrado.
    ct = pd.crosstab(df[var], df[TARGET])
    ct = ct.reindex(columns=[0, 1], fill_value=0)
    ct.columns = [hd_label(0), hd_label(1)]
    labels_map = CAT_LABELS.get(var, {})
    ct.index = [labels_map.get(i, i) for i in ct.index]
    ct["Total"] = ct.sum(axis=1)

    col_tab, col_fig = st.columns([1, 1])
    with col_tab:
        st.subheader("Contingência × Doença")
        st.dataframe(ct)

    with col_fig:
        st.subheader("Gráfico de barras agrupadas")
        plot_ct = ct.drop(columns="Total")
        fig, ax = plt.subplots(figsize=(6, 4))
        plot_ct.plot(kind="bar", ax=ax, color=PALETTE_HD_LIST)
        ax.set_ylabel("Nº de pacientes")
        ax.set_xlabel(VAR_LABELS[var])
        ax.set_title(f"{VAR_LABELS[var]} × Doença Cardíaca")
        ax.legend(title="")
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)


# ---------------------------------------------------------------------------
# Seção: Idade (discreta)
# ---------------------------------------------------------------------------
def section_age(df: pd.DataFrame) -> None:
    st.header("Idade (quantitativa discreta)")
    if len(df) == 0:
        st.warning("Nenhum paciente no recorte atual. Ajuste os filtros.")
        return

    desc = descriptive_summary(df[DISC_VAR], name=VAR_LABELS[DISC_VAR])
    col_tab, col_fig = st.columns([1, 1])
    with col_tab:
        st.subheader("Medidas descritivas")
        st.dataframe(desc)
        st.caption(f"Assimetria de Pearson-2: {pearson2_skewness(df[DISC_VAR]):.3f}")

    with col_fig:
        st.subheader("Frequência por faixa etária")
        faixas = pd.cut(df[DISC_VAR], bins=AGE_BINS, labels=AGE_LABELS, right=False)
        counts = faixas.value_counts().reindex(AGE_LABELS, fill_value=0)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(counts.index.astype(str), counts.values, color=COLOR_DISEASE)
        for i, v in enumerate(counts.values):
            ax.text(i, v, str(v), ha="center", va="bottom", fontweight="bold")
        ax.set_ylabel("Nº de pacientes")
        ax.set_xlabel("Faixa etária")
        ax.set_title("Distribuição etária")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)


# ---------------------------------------------------------------------------
# Seção: Contínuas
# ---------------------------------------------------------------------------
def section_continuous(df: pd.DataFrame) -> None:
    st.header("Variáveis Contínuas")
    if len(df) == 0:
        st.warning("Nenhum paciente no recorte atual. Ajuste os filtros.")
        return

    var = st.selectbox(
        "Variável",
        options=CONT_VARS,
        format_func=lambda v: VAR_LABELS[v],
    )

    # Zeros bio-impossíveis em Cholesterol/RestingBP são excluídos da descritiva,
    # consistente com a v1 (valor ausente, não real).
    series = df[var]
    if var in ("Cholesterol", "RestingBP"):
        series = series[series != 0]

    col_tab, col_fig = st.columns([1, 1])
    with col_tab:
        st.subheader("Medidas descritivas")
        st.dataframe(descriptive_summary(series, name=VAR_LABELS[var]))
        st.caption(f"n = {len(series)} (zeros ausentes excluídos quando aplicável)")

    with col_fig:
        st.subheader("Histograma e boxplot por grupo")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))
        ax1.hist(series, bins=20, color=COLOR_DISEASE, alpha=0.8, edgecolor="white")
        ax1.set_title("Histograma")
        ax1.set_xlabel(VAR_LABELS[var])
        ax1.set_ylabel("Frequência")

        groups, colors, tick_labels = [], [], []
        for hd in (0, 1):
            sub = df[df[TARGET] == hd][var]
            if var in ("Cholesterol", "RestingBP"):
                sub = sub[sub != 0]
            if len(sub) > 0:
                groups.append(sub.values)
                colors.append(PALETTE_HD_LIST[hd])
                tick_labels.append(hd_label(hd))
        if groups:
            bp = ax2.boxplot(groups, patch_artist=True, tick_labels=tick_labels)
            for patch, color in zip(bp["boxes"], colors):
                patch.set_facecolor(color)
        ax2.set_title("Por grupo")
        ax2.set_ylabel(VAR_LABELS[var])
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)


# ---------------------------------------------------------------------------
# Seção: Predição ao vivo
# ---------------------------------------------------------------------------
def section_prediction(df: pd.DataFrame) -> None:
    st.header("Predição ao Vivo")
    st.caption(
        "Preencha as características de um paciente e o modelo da Fase 1 "
        "(regressão logística) estima a probabilidade de doença cardíaca."
    )

    model = get_model()
    if model is None:
        st.error(
            "Modelo não encontrado em `models/logistic_model.joblib`. "
            "Rode antes: `python -m src.train_model`."
        )
        return

    with st.form("pred_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            age = st.number_input("Idade", 18, 100, 54)
            resting_bp = st.number_input("Pressão em repouso (mmHg)", 80, 220, 130)
            cholesterol = st.number_input("Colesterol (mg/dL)", 0, 700, 240)
            max_hr = st.number_input("Freq. cardíaca máx. (bpm)", 60, 220, 150)
        with c2:
            oldpeak = st.number_input("Oldpeak (depressão ST)", -3.0, 7.0, 1.0, step=0.1)
            fasting_bs = st.selectbox(
                "Glicemia jejum > 120", [0, 1],
                format_func=lambda v: CAT_LABELS["FastingBS"][v],
            )
            sex = st.selectbox(
                "Sexo", ["M", "F"], format_func=lambda v: CAT_LABELS["Sex"][v]
            )
        with c3:
            chest = st.selectbox(
                "Tipo de dor torácica", ["ASY", "ATA", "NAP", "TA"],
                format_func=lambda v: CAT_LABELS["ChestPainType"][v],
            )
            ecg = st.selectbox(
                "ECG em repouso", ["Normal", "ST", "LVH"],
                format_func=lambda v: CAT_LABELS["RestingECG"][v],
            )
            angina = st.selectbox(
                "Angina por exercício", ["N", "Y"],
                format_func=lambda v: CAT_LABELS["ExerciseAngina"][v],
            )
            st_slope = st.selectbox(
                "Inclinação ST", ["Up", "Flat", "Down"],
                format_func=lambda v: CAT_LABELS["ST_Slope"][v],
            )

        submitted = st.form_submit_button("Prever")

    if submitted:
        # Cholesterol == 0 → NaN (tratado como ausente, igual ao treino).
        chol_val = np.nan if cholesterol == 0 else cholesterol
        bp_val = np.nan if resting_bp == 0 else resting_bp
        row = pd.DataFrame([{
            "Age": age,
            "RestingBP": bp_val,
            "Cholesterol": chol_val,
            "FastingBS": fasting_bs,
            "MaxHR": max_hr,
            "Oldpeak": oldpeak,
            "Sex": sex,
            "ChestPainType": chest,
            "RestingECG": ecg,
            "ExerciseAngina": angina,
            "ST_Slope": st_slope,
        }])[MODEL_FEATURES]

        proba = float(model.predict_proba(row)[0, 1])
        pred = int(model.predict(row)[0])

        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.metric("P(Doença Cardíaca)", f"{proba:.1%}")
        c2.metric("Classe prevista", hd_label(pred))
        if pred == 1:
            st.error(f"Risco estimado: **{hd_label(1)}** (p = {proba:.3f})")
        else:
            st.success(f"Risco estimado: **{hd_label(0)}** (p = {proba:.3f})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="Heart Failure — Dashboard", layout="wide")
    st.title("Heart Failure — Análise & Predição")

    df = get_data()
    df_f = apply_filters(df)

    section = st.sidebar.radio(
        "Seção",
        ["Visão Geral", "Qualitativas", "Idade", "Contínuas", "Predição"],
    )

    if section == "Visão Geral":
        section_overview(df_f)
    elif section == "Qualitativas":
        section_qualitative(df_f)
    elif section == "Idade":
        section_age(df_f)
    elif section == "Contínuas":
        section_continuous(df_f)
    elif section == "Predição":
        # A predição usa entradas do formulário, não o recorte filtrado.
        section_prediction(df)


main()
