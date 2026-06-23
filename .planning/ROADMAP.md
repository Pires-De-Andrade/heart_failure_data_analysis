# Roadmap: Heart Failure — Predição e Dashboard

## Overview

A v1 entregou a análise estatística descritiva completa do *Heart Failure Prediction Dataset*. A v2 estende o trabalho em duas fases sequenciais: primeiro um **modelo preditivo interpretável** (regressão logística) que prevê `HeartDisease` e gera artefatos (modelo treinado, métricas, odds-ratios); depois um **dashboard interativo** (Streamlit) que apresenta a análise de forma reativa e consome o modelo para predição ao vivo.

## Phases

**Phase Numbering:**
- Integer phases (1, 2): Planned milestone work
- Decimal phases (2.1): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Modelo Preditivo** - Regressão logística que prevê HeartDisease, avaliada e interpretada
- [x] **Phase 2: Dashboard Interativo** - App Streamlit com filtros reativos + predição ao vivo
- [x] **Phase 3: Explicabilidade SHAP** (milestone v2.1) - SHAP global (beeswarm/bar) + local (waterfall) no dashboard

## Phase Details

### Phase 1: Modelo Preditivo
**Goal**: Treinar e avaliar uma regressão logística que prediz `HeartDisease` a partir das 11 features, com métricas de classificação, interpretação por odds-ratios e modelo persistido para consumo posterior.
**Depends on**: Nothing (primeira fase da v2; reusa dados da v1)
**Requirements**: PRED-01, PRED-02, PRED-03, PRED-04, PRED-05
**Success Criteria** (what must be TRUE):
  1. `python -m src.train_model` roda do zero e regenera modelo + métricas + figuras de forma determinística
  2. Existe um modelo persistido em `models/` carregável por outro script
  3. Há um relatório de avaliação (acurácia, precisão, recall, F1, matriz de confusão, ROC/AUC) salvo em `output/`
  4. Há uma tabela de odds-ratios por variável, interpretável clinicamente
**Plans**: TBD

Plans:
- [x] 01-01: `src/train_model.py` — pipeline (impute mediana + one-hot + scaler) → logística → avaliação → odds-ratios → `models/logistic_model.joblib` (test AUC 0.933, acurácia 0.886)

### Phase 2: Dashboard Interativo
**Goal**: Disponibilizar um app Streamlit que apresenta a análise descritiva de forma interativa (filtros reativos) e expõe um formulário de predição ao vivo usando o modelo da Fase 1.
**Depends on**: Phase 1 (consome o modelo persistido e artefatos)
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, DASH-05
**Success Criteria** (what must be TRUE):
  1. `streamlit run dashboard/app.py` abre o app sem erros
  2. Filtros (Sex, HeartDisease, faixa etária) recalculam tabelas/gráficos exibidos
  3. As seções da análise descritiva são navegáveis e reaproveitam os artefatos existentes
  4. O formulário de predição retorna P(HeartDisease) + classe ao submeter as features
**Plans**: TBD

Plans:
- [x] 02-01: `dashboard/app.py` — app Streamlit (5 seções), filtros reativos (Sex/HeartDisease/idade), predição ao vivo consumindo o `.joblib`, dados/modelo em cache

### Phase 3: Explicabilidade SHAP (milestone v2.1)
**Goal**: Elevar o modelo preditivo ao mesmo nível de profundidade do descritivo via explicabilidade SHAP — importância global e explicação por paciente — no dashboard.
**Depends on**: Phase 1 (modelo treinado) e Phase 2 (dashboard)
**Requirements**: XAI-01, XAI-02, XAI-03, XAI-04, XAI-05, XAI-06, XAI-07
**Success Criteria** (what must be TRUE):
  1. `python -m src.train_model` gera `shap_global.npz` + `06_shap_beeswarm.png` de forma determinística (aditividade do SHAP até precisão de máquina)
  2. Plots SHAP usam rótulos legíveis ("ST_Slope = Up"), não nomes pós one-hot
  3. Dashboard tem seção "Explicabilidade" com bar global + beeswarm
  4. Predição ao vivo exibe waterfall SHAP do paciente submetido
  5. Explainer cacheado — construído uma única vez por sessão

Plans:
- [x] 03-01: `src/explain.py` (LinearExplainer + rótulos legíveis) + extensão do `train_model` (artefatos SHAP globais) + seção "Explicabilidade" e waterfall local cacheado no `dashboard/app.py`

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Modelo Preditivo | 1/1 | Complete | 2026-06-22 |
| 2. Dashboard Interativo | 1/1 | Complete | 2026-06-22 |
| 3. Explicabilidade SHAP | 1/1 | Complete | 2026-06-23 |
