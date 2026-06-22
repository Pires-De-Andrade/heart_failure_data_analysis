# Phase 1: Modelo Preditivo — Specification

**Created:** 2026-06-22
**Ambiguity score:** 0.11 (gate: ≤ 0.20)
**Requirements:** 5 locked

## Goal

Treinar e avaliar uma **regressão logística** que prediz `HeartDisease` a partir das 11 features do dataset, produzindo um modelo persistido, um relatório de métricas no test set e uma tabela de odds-ratios interpretáveis — tudo regenerável por um único comando.

## Background

A v1 do projeto entrega apenas análise **descritiva**: notebooks (`01_preprocessing` … `04_continuous`), 27 tabelas em `output/tables/*.csv`, figuras em `output/figures/*.png` e `RELATORIO.docx`. **Não existe** nenhum modelo preditivo, split train/test, métrica de classificação ou pipeline sklearn. O dado bruto está em `dataset/raw/heart.csv` (918×12), já com o tratamento conhecido dos zeros bio-impossíveis em `Cholesterol` (172 registros) e `RestingBP` (1). `scikit-learn` e `joblib` ainda **não** estão em `requirements.txt`. Esta fase cria a camada preditiva do zero, reaproveitando as decisões de tratamento de dados já validadas na descritiva.

## Requirements

1. **Pipeline de pré-processamento**: Transforma `heart.csv` bruto em matriz de treino de forma reprodutível.
   - Current: Não existe pipeline sklearn; pré-processamento descritivo vive nos notebooks, sem split nem encoding para modelagem
   - Target: Função/módulo que faz encoding das categóricas (`Sex`, `ChestPainType`, `RestingECG`, `ExerciseAngina`, `ST_Slope`), trata os zeros bio-impossíveis de `Cholesterol`/`RestingBP`, e faz split estratificado treino/teste com `random_state` fixo
   - Acceptance: Rodar duas vezes produz exatamente as mesmas partições e shapes; o split é estratificado por `HeartDisease` (proporção 55/45 preservada nos dois conjuntos)

2. **Treino e persistência do modelo**: Regressão logística treinada e salva em disco.
   - Current: Nenhum modelo existe
   - Target: `LogisticRegression` treinada no conjunto de treino e persistida em `models/logistic_model.joblib` (com o pré-processador, ex. `Pipeline`/`ColumnTransformer`)
   - Acceptance: O arquivo `models/logistic_model.joblib` existe e pode ser carregado por outro processo e usado para `.predict`/`.predict_proba` em uma linha nova sem erro

3. **Avaliação no test set**: Relatório de métricas de classificação salvo como artefatos.
   - Current: Nenhuma métrica de classificação existe
   - Target: Acurácia, precisão, recall, F1, matriz de confusão e ROC/AUC calculados no test set; salvos como CSV em `output/tables/` e figuras (matriz de confusão, curva ROC) em `output/figures/`
   - Acceptance: Existem os arquivos de métricas (ex. `output/tables/pred_metrics.csv`) e as figuras `output/figures/05_confusion_matrix.png` e `output/figures/05_roc_curve.png`; AUC reportado é um número em [0,1]

4. **Interpretação por odds-ratios**: Cada variável recebe um coeficiente convertido em odds-ratio.
   - Current: Nenhuma interpretação de modelo existe
   - Target: Tabela com coeficiente, odds-ratio (exp(coef)) e ranking de importância por variável, salva em `output/tables/`
   - Acceptance: Existe `output/tables/pred_odds_ratios.csv` com uma linha por feature; variáveis apontadas como fortes na descritiva (`ST_Slope`, `Oldpeak`, `ExerciseAngina`) aparecem entre as de maior magnitude

5. **Script reprodutível**: Um comando regenera todos os artefatos da fase.
   - Current: Não existe `src/train_model.py`
   - Target: `src/train_model.py` executável via `python -m src.train_model`, que roda o pipeline → treino → avaliação → interpretação e grava todos os artefatos acima
   - Acceptance: Em um checkout limpo (após `pip install -r requirements.txt`), `python -m src.train_model` termina com código 0 e cria modelo + métricas + odds-ratios + figuras

## Boundaries

**In scope:**
- Pipeline de pré-processamento para modelagem (encoding + tratamento de zeros + split estratificado)
- Treino de **uma** regressão logística e persistência em `models/`
- Avaliação no test set (acurácia, precisão, recall, F1, matriz de confusão, ROC/AUC) com tabelas e figuras
- Tabela de odds-ratios + ranking de importância das variáveis
- Script `src/train_model.py` reprodutível
- Adição de `scikit-learn` e `joblib` ao `requirements.txt`

**Out of scope:**
- Outros modelos (árvore, random forest, boosting, redes) — decisão de projeto: manter interpretável e alinhado ao curso de estatística
- Tuning extensivo de hiperparâmetros / cross-validation aninhada — logística com configuração padrão razoável basta para o escopo acadêmico
- Dashboard / UI — é a Fase 2 (consome estes artefatos)
- Reescrita dos notebooks descritivos da v1 — reaproveitados como estão

## Constraints

- **Stack**: Python only; usar `scikit-learn` + `joblib`; manter pandas/numpy já no projeto
- **Reprodutibilidade**: `random_state` fixo em split e modelo; rodar a partir de `dataset/raw/heart.csv`
- **Tratamento de dados**: os zeros bio-impossíveis de `Cholesterol`/`RestingBP` devem ser tratados de forma consistente com a análise descritiva v1 (não usados como valor real)
- **Convenções**: artefatos seguem o padrão existente — tabelas em `output/tables/`, figuras em `output/figures/` com prefixo numérico (`05_*`)

## Acceptance Criteria

- [ ] `python -m src.train_model` termina com código 0 e regenera todos os artefatos de forma determinística
- [ ] `models/logistic_model.joblib` existe e é carregável/usável por outro script para predição
- [ ] Split é estratificado por `HeartDisease` com `random_state` fixo (mesmas partições a cada execução)
- [ ] `output/tables/pred_metrics.csv` contém acurácia, precisão, recall, F1 e AUC do test set
- [ ] `output/figures/05_confusion_matrix.png` e `output/figures/05_roc_curve.png` são gerados
- [ ] `output/tables/pred_odds_ratios.csv` tem uma linha por feature com coeficiente e odds-ratio
- [ ] `scikit-learn` e `joblib` constam em `requirements.txt`

## Ambiguity Report

| Dimension          | Score | Min  | Status | Notes                                            |
|--------------------|-------|------|--------|--------------------------------------------------|
| Goal Clarity       | 0.92  | 0.75 | ✓      | Alvo, modelo e saídas definidos                  |
| Boundary Clarity   | 0.95  | 0.70 | ✓      | Multi-modelo e dashboard explicitamente fora     |
| Constraint Clarity | 0.82  | 0.65 | ✓      | Stack, seed e tratamento de dados fixados         |
| Acceptance Criteria| 0.85  | 0.70 | ✓      | 7 checks pass/fail                               |
| **Ambiguity**      | 0.11  | ≤0.20| ✓      |                                                  |

## Interview Log

| Round | Perspective     | Question summary                  | Decision locked                                      |
|-------|-----------------|-----------------------------------|------------------------------------------------------|
| —     | (auto)          | Abordagem preditiva               | Regressão logística interpretável (escolha do usuário)|
| —     | Researcher      | O que existe hoje?                | Só descritiva; sem modelo/split/sklearn              |
| —     | Simplifier      | Núcleo mínimo                     | 1 modelo + métricas + odds-ratios + script           |
| —     | Boundary Keeper | O que NÃO é desta fase            | Multi-modelo, tuning pesado, dashboard               |
| —     | Failure Analyst | O que invalida o resultado        | Não-reprodutibilidade; modelo não-carregável         |

---

*Phase: 01-modelo-preditivo*
*Spec created: 2026-06-22 (modo --auto: decisões-chave coletadas via AskUserQuestion)*
*Next step: /gsd:discuss-phase 1 — decisões de implementação (encoding, features, threshold, layout dos artefatos)*
