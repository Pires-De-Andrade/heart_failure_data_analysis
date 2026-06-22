# Heart Failure — Análise, Predição e Dashboard

## What This Is

Trabalho acadêmico de Probabilidade e Estatística A (UFG, 1º sem/2026) sobre o *Heart Failure Prediction Dataset* (918 pacientes, 12 variáveis, alvo binário `HeartDisease`). A base v1 entrega a **análise estatística descritiva** completa (notebooks, tabelas, figuras e `RELATORIO.docx`). A v2 estende o trabalho com um **modelo preditivo interpretável** (regressão logística) e um **dashboard interativo** (Streamlit) que apresenta a análise e expõe predição ao vivo.

## Core Value

Transformar a análise descritiva estática em uma ferramenta **interativa e preditiva** que demonstra, de forma reprodutível, quais indicadores clínicos distinguem pacientes com e sem doença cardíaca — e prevê o diagnóstico a partir deles.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- [x] Análise descritiva completa (qualitativas, discreta, contínuas) — `RELATORIO.docx`, notebooks, `output/`

### Active

<!-- Current scope. Building toward these. -->

- [ ] **PRED**: Modelo de regressão logística que prediz `HeartDisease`, avaliado e interpretado (odds-ratios)
- [ ] **DASH**: Dashboard Streamlit interativo com filtros + formulário de predição ao vivo

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Modelos de ML complexos (random forest, boosting, redes) — curso é Estatística Descritiva; logística basta e é interpretável
- Deploy em nuvem / hosting público — entrega é local (`streamlit run`) + relatório; sem custo/infra
- Reescrita da análise descritiva v1 — já validada, será reaproveitada como está

## Context

- Stack atual: Python 3, pandas, numpy, scipy, matplotlib, seaborn, jupyter
- Dados já tratados: zeros biologicamente impossíveis em `Cholesterol` (172) e `RestingBP` (1) tratados como ausentes
- Achados descritivos fortes (viram features preditivas relevantes): `ST_Slope`, `Oldpeak`, `ExerciseAngina`, `MaxHR`, `ChestPainType`, `Sex`, `Age`
- Base balanceada: 55,3% com doença / 44,7% sem
- Artefatos reutilizáveis: `output/tables/*.csv` (27), `output/figures/*.png`, `dataset/raw/heart.csv`

## Constraints

- **Tech stack**: Python only — adicionar `scikit-learn`, `joblib`, `streamlit` ao `requirements.txt`; manter pandas/matplotlib/seaborn
- **Escopo acadêmico**: parte preditiva deve ser interpretável (alinhada à estatística), não caixa-preta
- **Reprodutibilidade**: tudo roda por script/notebook a partir de `dataset/raw/heart.csv`; seeds fixas
- **Dependencies**: Fase 2 (dashboard) depende dos artefatos da Fase 1 (modelo treinado)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Regressão logística (não multi-modelo ML) | Interpretável, alinhada ao curso de estatística, odds-ratios explicáveis | — Pending |
| Streamlit (não Dash/HTML estático) | Python puro, casa com stack, rápido, suporta predição ao vivo | — Pending |
| 2 fases sequenciais (modelo → dashboard) | Dashboard consome artefatos do modelo | — Pending |

---
*Last updated: 2026-06-22 after bootstrap da v2 (predição + dashboard)*
