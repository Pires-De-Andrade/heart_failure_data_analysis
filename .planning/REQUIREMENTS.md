# Requirements: Heart Failure — Predição e Dashboard

**Defined:** 2026-06-22
**Core Value:** Análise descritiva interativa + predição interpretável de `HeartDisease`

## v2 Requirements

Requisitos da extensão v2. Cada um mapeia para uma fase do roadmap.

### Modelo Preditivo (Fase 1)

- [ ] **PRED-01**: Pipeline de pré-processamento reproduzível a partir de `dataset/raw/heart.csv` (encoding de categóricas, tratamento dos zeros bio-impossíveis, split train/test estratificado com seed fixa)
- [ ] **PRED-02**: Modelo de regressão logística treinado e persistido em `models/` (joblib)
- [ ] **PRED-03**: Avaliação no test set: acurácia, precisão, recall, F1, matriz de confusão, curva ROC e AUC — salvos em `output/`
- [ ] **PRED-04**: Interpretação: tabela de coeficientes convertidos em odds-ratios por variável, com ranking de importância
- [ ] **PRED-05**: Script `src/train_model.py` executável via `python -m src.train_model`, regenerando todos os artefatos de forma determinística

### Dashboard Interativo (Fase 2)

- [ ] **DASH-01**: App Streamlit `dashboard/app.py` que roda via `streamlit run dashboard/app.py`
- [ ] **DASH-02**: Filtros reativos (Sex, HeartDisease, faixa etária) que recalculam tabelas e gráficos exibidos
- [ ] **DASH-03**: Seções da análise descritiva (prevalência, qualitativas, idade, contínuas) reaproveitando dados/figuras existentes
- [ ] **DASH-04**: Formulário de predição ao vivo: usuário insere as features → app carrega o modelo da Fase 1 e retorna P(HeartDisease) + classe prevista
- [ ] **DASH-05**: Reuso dos artefatos (`output/tables`, `output/figures`, `models/`) sem recomputar a análise pesada a cada interação

## Out of Scope

| Feature | Reason |
|---------|--------|
| Random forest / boosting / redes neurais | Curso é Estatística Descritiva; logística é interpretável e suficiente |
| Deploy/hosting público | Entrega local + relatório; sem infra |
| Autenticação / multiusuário | Ferramenta de análise single-user local |
| Reescrita da análise v1 | Já validada; reaproveitada como está |
