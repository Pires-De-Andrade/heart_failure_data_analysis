# Requirements: Heart Failure — Predição e Dashboard

**Defined:** 2026-06-22
**Core Value:** Análise descritiva interativa + predição interpretável de `HeartDisease`

## v2.1 Requirements

Requisitos da milestone v2.1 — Explicabilidade do Modelo (SHAP). Cada um mapeia para uma fase do roadmap.

### Explicabilidade (XAI)

- [ ] **XAI-01**: `python -m src.train_model` gera artefatos SHAP globais reprodutíveis (`output/tables/shap_global.npz` + `output/figures/06_shap_beeswarm.png`) a partir do pipeline treinado — `LinearExplainer` sobre o `clf` extraído, dados transformados, seed fixa
- [ ] **XAI-02**: Os plots SHAP exibem nomes de features legíveis (ex: "ST_Slope = Up"), não os nomes internos pós one-hot (`cat__ST_Slope_Up`) — mapeados de `VAR_LABELS`/`CAT_LABELS`
- [ ] **XAI-03**: O usuário acessa uma seção "Explicabilidade" dedicada na navegação da sidebar do dashboard
- [ ] **XAI-04**: A seção exibe um bar chart global de importância (mean |SHAP|) por feature
- [ ] **XAI-05**: A seção exibe um beeswarm global mostrando direção + magnitude da contribuição de cada feature
- [ ] **XAI-06**: Após submeter o formulário de predição, o usuário vê um waterfall SHAP que explica a predição daquele paciente específico
- [ ] **XAI-07**: O explainer é cacheado (`@st.cache_resource`) — interações no dashboard não o recomputam

## Future Requirements

Diferenciais reconhecidos mas adiados (não na milestone atual).

### Explicabilidade — Diferenciais

- **XAI-F01**: Comparação lado a lado SHAP bar vs Odds-Ratio bar (mostra concordância/divergência das duas leituras)
- **XAI-F02**: Anotação de probabilidade no waterfall — "taxa base X% → predição Y%" via sigmoid, esclarecendo a escala log-odds
- **XAI-F03**: Labels do waterfall com valores reais do paciente (ex: "ST_Slope = Flat contribuiu +0.41")

## Out of Scope

Explicitamente excluído. Documentado para evitar scope creep.

| Feature | Reason |
|---------|--------|
| Force plot interativo (JS) | Não renderiza limpo no Streamlit; waterfall (matplotlib) entrega a mesma informação sem dependência frágil |
| `KernelExplainer` | `LinearExplainer` computa SHAP exato e analítico para a logística; Kernel é 10–100× mais lento e aproximado |
| Dependence plots | Para modelo linear são uma reta — redundantes com os coeficientes/odds-ratios |
| SHAP sobre subconjuntos filtrados | Explainer é ajustado no treino, não no filtro; recomputar por slider gera latência e amostras instáveis |
| SHAP em espaço de probabilidade (link logit) | Quebra a aditividade de Shapley; manter log-odds e anotar |
| Cross-validation / calibração / threshold tuning | Expansão de avaliação fora do escopo desta milestone (PROJECT.md) |
| Random forest / boosting / redes neurais | Curso é Estatística Descritiva; logística é interpretável e suficiente |
| Deploy/hosting público | Entrega local + relatório; sem infra |

## v2 Requirements (Validated)

Requisitos da extensão v2 — entregues e validados.

### Modelo Preditivo (Fase 1)

- [x] **PRED-01**: Pipeline de pré-processamento reproduzível a partir de `dataset/raw/heart.csv` (encoding de categóricas, tratamento dos zeros bio-impossíveis, split train/test estratificado com seed fixa)
- [x] **PRED-02**: Modelo de regressão logística treinado e persistido em `models/` (joblib)
- [x] **PRED-03**: Avaliação no test set: acurácia, precisão, recall, F1, matriz de confusão, curva ROC e AUC — salvos em `output/`
- [x] **PRED-04**: Interpretação: tabela de coeficientes convertidos em odds-ratios por variável, com ranking de importância
- [x] **PRED-05**: Script `src/train_model.py` executável via `python -m src.train_model`, regenerando todos os artefatos de forma determinística

### Dashboard Interativo (Fase 2)

- [x] **DASH-01**: App Streamlit `dashboard/app.py` que roda via `streamlit run dashboard/app.py`
- [x] **DASH-02**: Filtros reativos (Sex, HeartDisease, faixa etária) que recalculam tabelas e gráficos exibidos
- [x] **DASH-03**: Seções da análise descritiva (prevalência, qualitativas, idade, contínuas) reaproveitando dados/figuras existentes
- [x] **DASH-04**: Formulário de predição ao vivo: usuário insere as features → app carrega o modelo da Fase 1 e retorna P(HeartDisease) + classe prevista
- [x] **DASH-05**: Reuso dos artefatos (`output/tables`, `output/figures`, `models/`) sem recomputar a análise pesada a cada interação

## Traceability

Quais fases cobrem quais requisitos. Preenchido na criação do roadmap.

| Requirement | Phase | Status |
|-------------|-------|--------|
| XAI-01 | TBD | Pending |
| XAI-02 | TBD | Pending |
| XAI-03 | TBD | Pending |
| XAI-04 | TBD | Pending |
| XAI-05 | TBD | Pending |
| XAI-06 | TBD | Pending |
| XAI-07 | TBD | Pending |

**Coverage:**
- v2.1 requirements: 7 total
- Mapped to phases: 0 (TBD — roadmap)
- Unmapped: 7 ⚠️

---
*Requirements defined: 2026-06-22*
*Last updated: 2026-06-22 — milestone v2.1 (Explicabilidade SHAP) definida*
