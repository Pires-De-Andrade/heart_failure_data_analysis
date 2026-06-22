# Heart Failure — Análise, Predição e Dashboard

## What This Is

Trabalho acadêmico de Probabilidade e Estatística A (UFG, 1º sem/2026) sobre o *Heart Failure Prediction Dataset* (918 pacientes, 12 variáveis, alvo binário `HeartDisease`). A base v1 entrega a **análise estatística descritiva** completa (notebooks, tabelas, figuras e `RELATORIO.docx`). A v2 estende o trabalho com um **modelo preditivo interpretável** (regressão logística) e um **dashboard interativo** (Streamlit) que apresenta a análise e expõe predição ao vivo.

## Core Value

Transformar a análise descritiva estática em uma ferramenta **interativa e preditiva** que demonstra, de forma reprodutível, quais indicadores clínicos distinguem pacientes com e sem doença cardíaca — e prevê o diagnóstico a partir deles.

## Current Milestone: v2.1 Explicabilidade do Modelo (SHAP)

**Goal:** Dar destaque ao modelo preditivo no dashboard com explicabilidade SHAP — importância global e explicação por paciente — elevando o modelo ao mesmo nível de profundidade do descritivo.

**Target features:**
- SHAP global (summary/beeswarm) — importância agregada das features, complementando os odds-ratios
- SHAP local (waterfall) — explica cada predição ao vivo do dashboard
- Nova seção dedicada à explicabilidade do modelo no dashboard (paridade visual com o descritivo)
- Artefatos SHAP reprodutíveis gerados a partir do modelo treinado (seeds fixas)

**Key context:** Superfície única = dashboard Streamlit (sem relatório/notebook nesta milestone). Sem expandir avaliação (cross-val/calibração/threshold ficam fora). Logística permanece o modelo; SHAP é camada complementar. Adicionar `shap` ao `requirements.txt`.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- [x] Análise descritiva completa (qualitativas, discreta, contínuas) — `RELATORIO.docx`, notebooks, `output/`
- [x] **PRED**: Modelo de regressão logística que prediz `HeartDisease`, avaliado e interpretado (odds-ratios) — `src/train_model.py`, `models/logistic_model.joblib` (test AUC 0.933)
- [x] **DASH**: Dashboard Streamlit interativo com filtros + formulário de predição ao vivo — `dashboard/app.py`

### Active

<!-- Current scope. Building toward these. -->

- [ ] **XAI**: Explicabilidade SHAP do modelo logístico — global (importância de features) e local (waterfall por paciente)
- [ ] **XAI-DASH**: Seção de explicabilidade no dashboard com SHAP global + SHAP local na predição ao vivo

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
| Regressão logística (não multi-modelo ML) | Interpretável, alinhada ao curso de estatística, odds-ratios explicáveis | ✓ Entregue — AUC 0.933, top features ST_Slope/ChestPainType/Sex |
| Streamlit (não Dash/HTML estático) | Python puro, casa com stack, rápido, suporta predição ao vivo | ✓ Entregue — `dashboard/app.py`, 5 seções + predição |
| 2 fases sequenciais (modelo → dashboard) | Dashboard consome artefatos do modelo | ✓ Entregue — dashboard carrega o `.joblib` da Fase 1 |
| Zeros bio-impossíveis → imputação por mediana no pipeline | Mantém as 11 features e todas as linhas; mediana ajustada só no treino (sem vazamento) | ✓ Entregue |
| SHAP para explicabilidade (não só odds-ratios) | Atribuição por-instância, lida com pipeline one-hot+scaler, viz fortes (beeswarm/waterfall); odds-ratios são só globais e lineares | — Pending (v2.1) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-22 — milestone v2.1 (Explicabilidade SHAP) iniciada*
