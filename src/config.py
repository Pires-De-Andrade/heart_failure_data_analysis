"""
config.py — Constantes globais, caminhos e paleta de cores.

Centraliza todas as configurações para que notebooks e módulos
compartilhem os mesmos parâmetros sem duplicação.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos do projeto
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "dataset" / "raw" / "heart.csv"
OUTPUT_FIGURES = PROJECT_ROOT / "output" / "figures"
OUTPUT_TABLES = PROJECT_ROOT / "output" / "tables"
MODELS_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODELS_DIR / "logistic_model.joblib"

# ---------------------------------------------------------------------------
# Parâmetros do dataset
# ---------------------------------------------------------------------------
TARGET = "HeartDisease"           # Variável-alvo (eixo comparativo)
TOTAL_N = 918                     # Total de observações

# Variáveis qualitativas (Bloco 1)
QUAL_VARS = [
    "Sex",
    "ChestPainType",
    "RestingECG",
    "ExerciseAngina",
    "ST_Slope",
    "FastingBS",
]

# Variável quantitativa discreta (Bloco 2)
DISC_VAR = "Age"

# Variáveis quantitativas contínuas (Bloco 3)
CONT_VARS = ["RestingBP", "Cholesterol", "MaxHR", "Oldpeak"]

# ---------------------------------------------------------------------------
# Parâmetros de modelagem (Fase 1 — modelo preditivo)
# ---------------------------------------------------------------------------
# 11 features preditivas (todas as colunas exceto o alvo HeartDisease).
# Categóricas recebem one-hot encoding; numéricas são padronizadas.
MODEL_CAT_FEATURES = [
    "Sex",
    "ChestPainType",
    "RestingECG",
    "ExerciseAngina",
    "ST_Slope",
]
MODEL_NUM_FEATURES = [
    "Age",
    "RestingBP",
    "Cholesterol",
    "FastingBS",
    "MaxHR",
    "Oldpeak",
]
MODEL_FEATURES = MODEL_NUM_FEATURES + MODEL_CAT_FEATURES

# Colunas onde 0 representa dado ausente (mediana do treino imputa o valor).
ZERO_AS_MISSING = ["Cholesterol", "RestingBP"]

# Reprodutibilidade: semente única para split e modelo.
RANDOM_STATE = 42
TEST_SIZE = 0.2

# Faixas etárias para a tabela de frequências de Age
AGE_BINS = [0, 40, 50, 60, 70, float("inf")]
AGE_LABELS = ["< 40", "40–49", "50–59", "60–69", "≥ 70"]

# ---------------------------------------------------------------------------
# Rótulos legíveis para variáveis e categorias
# ---------------------------------------------------------------------------
VAR_LABELS = {
    "Sex": "Sexo",
    "ChestPainType": "Tipo de Dor Torácica",
    "RestingECG": "ECG em Repouso",
    "ExerciseAngina": "Angina Induzida por Exercício",
    "ST_Slope": "Inclinação do Segmento ST",
    "FastingBS": "Glicemia de Jejum > 120 mg/dL",
    "Age": "Idade (anos)",
    "RestingBP": "Pressão Arterial em Repouso (mmHg)",
    "Cholesterol": "Colesterol Sérico (mg/dL)",
    "MaxHR": "Frequência Cardíaca Máxima (bpm)",
    "Oldpeak": "Depressão ST (Oldpeak)",
    "HeartDisease": "Doença Cardíaca",
}

CAT_LABELS = {
    "Sex": {"M": "Masculino", "F": "Feminino"},
    "ChestPainType": {
        "TA": "Angina Típica",
        "ATA": "Angina Atípica",
        "NAP": "Dor Não-Anginosa",
        "ASY": "Assintomático",
    },
    "RestingECG": {
        "Normal": "Normal",
        "ST": "Anormalidade ST-T",
        "LVH": "Hipertrofia Ventricular Esq.",
    },
    "ExerciseAngina": {"Y": "Sim", "N": "Não"},
    "ST_Slope": {
        "Up": "Ascendente",
        "Flat": "Plano",
        "Down": "Descendente",
    },
    "FastingBS": {0: "Não (≤ 120)", 1: "Sim (> 120)"},
    "HeartDisease": {0: "Sem doença", 1: "Com doença"},
}

# ---------------------------------------------------------------------------
# Paleta de cores
# ---------------------------------------------------------------------------
# Cores principais para HeartDisease (0 = saudável, 1 = doente)
COLOR_HEALTHY = "#4CAF93"    # verde-azulado
COLOR_DISEASE = "#E05263"    # vermelho-coral

PALETTE_HD = {0: COLOR_HEALTHY, 1: COLOR_DISEASE}
PALETTE_HD_LIST = [COLOR_HEALTHY, COLOR_DISEASE]

# Paleta sequencial para gráficos de barras (qualitativas)
PALETTE_QUAL = [
    "#5B8DEE", "#F2994A", "#56CCB2", "#E05263",
    "#9B59B6", "#3498DB", "#E67E22", "#1ABC9C",
]

# ---------------------------------------------------------------------------
# Configuração global de gráficos
# ---------------------------------------------------------------------------
FIGSIZE_SINGLE = (8, 5)
FIGSIZE_WIDE = (12, 5)
FIGSIZE_COMPARE = (10, 6)
DPI = 300

# Estilo matplotlib
MPL_STYLE = {
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#CCCCCC",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.color": "#CCCCCC",
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 12,
}
