# Roadmap: Heart Failure — Predição e Dashboard

## Overview

A v1 entregou a análise estatística descritiva completa do *Heart Failure Prediction Dataset*. A v2 estende o trabalho em duas fases sequenciais: primeiro um **modelo preditivo interpretável** (regressão logística) que prevê `HeartDisease` e gera artefatos (modelo treinado, métricas, odds-ratios); depois um **dashboard interativo** (Streamlit) que apresenta a análise de forma reativa e consome o modelo para predição ao vivo.

## Phases

**Phase Numbering:**
- Integer phases (1, 2): Planned milestone work
- Decimal phases (2.1): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Modelo Preditivo** - Regressão logística que prevê HeartDisease, avaliada e interpretada
- [ ] **Phase 2: Dashboard Interativo** - App Streamlit com filtros reativos + predição ao vivo

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
- [ ] 01-01: TBD (definido em plan-phase)

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
- [ ] 02-01: TBD (definido em plan-phase)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Modelo Preditivo | 0/TBD | Not started | - |
| 2. Dashboard Interativo | 0/TBD | Not started | - |
