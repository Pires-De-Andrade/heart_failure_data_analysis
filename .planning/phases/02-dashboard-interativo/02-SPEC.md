# Phase 2: Dashboard Interativo — Specification

**Created:** 2026-06-22
**Ambiguity score:** 0.13 (gate: ≤ 0.20)
**Requirements:** 5 locked

## Goal

Entregar um app **Streamlit** (`dashboard/app.py`) que apresenta a análise descritiva do dataset de forma **interativa** (filtros reativos por `Sex`, `HeartDisease` e faixa etária) e expõe um **formulário de predição ao vivo** que usa o modelo da Fase 1 para retornar P(HeartDisease) e a classe prevista.

## Background

A análise descritiva da v1 é **estática**: mora em notebooks, em 27 CSVs (`output/tables/`), em PNGs (`output/figures/`) e no `RELATORIO.docx`. Não há nenhuma camada interativa — para explorar um recorte (ex. só mulheres, ou só pacientes 50–59) seria preciso rerodar notebook. A Fase 1 produz `models/logistic_model.joblib` + métricas + odds-ratios. **Não existe** nenhum app Streamlit, e `streamlit` ainda não está em `requirements.txt`. Esta fase é a camada de apresentação/uso: empacota a análise e o modelo numa interface navegável local.

## Requirements

1. **App Streamlit executável**: Aplicação que inicia localmente.
   - Current: Não existe `dashboard/app.py` nem dependência `streamlit`
   - Target: `dashboard/app.py` que roda via `streamlit run dashboard/app.py` e abre no navegador, com navegação entre seções (sidebar ou tabs)
   - Acceptance: `streamlit run dashboard/app.py` inicia sem traceback e renderiza a página inicial com a prevalência de `HeartDisease`

2. **Filtros reativos**: Controles que recortam a amostra e atualizam as visualizações.
   - Current: Nenhuma interatividade existe; recortes exigiriam rerodar notebooks
   - Target: Widgets na sidebar (multiselect `Sex`, multiselect/toggle `HeartDisease`, slider de faixa etária) que filtram o DataFrame e recalculam as tabelas/gráficos exibidos
   - Acceptance: Alterar um filtro muda visivelmente os números/gráficos (ex. selecionar só `Sex=F` reduz o n exibido e atualiza a prevalência) sem reiniciar o app

3. **Seções da análise descritiva**: As análises da v1 reaproveitadas de forma navegável.
   - Current: Análises dispersas em notebooks e arquivos estáticos
   - Target: Seções para Visão Geral (prevalência), Qualitativas, Idade (discreta) e Contínuas, reaproveitando os artefatos de `output/` e/ou recomputando sobre o recorte filtrado
   - Acceptance: As 4 seções são acessíveis pela navegação e cada uma exibe ao menos uma tabela e um gráfico coerentes com o relatório v1

4. **Predição ao vivo**: Formulário que consome o modelo da Fase 1.
   - Current: O modelo da Fase 1 existe em disco mas não tem interface de uso
   - Target: Seção "Predição" com inputs para as features de um paciente; ao submeter, carrega `models/logistic_model.joblib` e exibe P(HeartDisease) e a classe prevista (com/sem doença)
   - Acceptance: Preencher o formulário e submeter retorna uma probabilidade em [0,1] e um rótulo de classe, sem erro, para entradas válidas

5. **Reuso de artefatos (performance)**: O app não recomputa a análise pesada a cada interação.
   - Current: N/A (não há app)
   - Target: Carregamento de dados, figuras e modelo via cache do Streamlit (`@st.cache_data`/`@st.cache_resource`); artefatos de `output/` e `models/` reutilizados
   - Acceptance: Após o primeiro load, mexer nos filtros responde sem recarregar/recomputar o modelo do zero (modelo carregado uma única vez)

## Boundaries

**In scope:**
- App Streamlit `dashboard/app.py` rodando localmente
- Filtros reativos: `Sex`, `HeartDisease`, faixa etária
- Seções descritivas: Visão Geral, Qualitativas, Idade, Contínuas
- Formulário de predição ao vivo usando o modelo da Fase 1
- Caching de dados/modelo para responsividade
- Adição de `streamlit` (e plotting interativo, se necessário) ao `requirements.txt`

**Out of scope:**
- Treino do modelo — é a Fase 1 (o dashboard só consome o `.joblib`)
- Deploy/hosting público (Streamlit Cloud, etc.) — entrega é local
- Autenticação, multiusuário, persistência de sessão — ferramenta single-user local
- Reescrita das estatísticas v1 — reaproveitadas; no máximo recomputadas sobre o recorte filtrado
- Edição/expansão do `RELATORIO.docx` — documento já entregue na v1

## Constraints

- **Dependency**: Requer os artefatos da Fase 1 (`models/logistic_model.joblib`); a fase não pode ser concluída sem a Fase 1
- **Stack**: Streamlit + pandas; reutilizar matplotlib/seaborn já no projeto (plotly opcional para interatividade nativa)
- **Execução**: roda local via `streamlit run`; sem dependência de serviço externo
- **Convenções**: ler dados de `dataset/raw/heart.csv` e artefatos de `output/`; não duplicar lógica de cálculo já validada além do necessário

## Acceptance Criteria

- [ ] `streamlit run dashboard/app.py` inicia sem traceback e mostra a prevalência inicial
- [ ] Filtros de `Sex`, `HeartDisease` e faixa etária alteram visivelmente tabelas/gráficos exibidos
- [ ] As 4 seções descritivas (Visão Geral, Qualitativas, Idade, Contínuas) são navegáveis e populadas
- [ ] O formulário de predição retorna P(HeartDisease) ∈ [0,1] + classe ao submeter features válidas
- [ ] O modelo é carregado via cache uma única vez (filtros não recarregam o modelo)
- [ ] `streamlit` consta em `requirements.txt`

## Ambiguity Report

| Dimension          | Score | Min  | Status | Notes                                              |
|--------------------|-------|------|--------|----------------------------------------------------|
| Goal Clarity       | 0.90  | 0.75 | ✓      | App + filtros + predição definidos                 |
| Boundary Clarity   | 0.92  | 0.70 | ✓      | Deploy/treino/auth explicitamente fora             |
| Constraint Clarity | 0.80  | 0.65 | ✓      | Dependência da Fase 1 e stack fixadas              |
| Acceptance Criteria| 0.82  | 0.70 | ✓      | 6 checks pass/fail                                 |
| **Ambiguity**      | 0.13  | ≤0.20| ✓      |                                                    |

## Interview Log

| Round | Perspective     | Question summary                  | Decision locked                                       |
|-------|-----------------|-----------------------------------|-------------------------------------------------------|
| —     | (auto)          | Framework do dashboard            | Streamlit (escolha do usuário)                        |
| —     | Researcher      | O que existe hoje?                | Análise estática; sem app; modelo vem da Fase 1       |
| —     | Simplifier      | Núcleo mínimo                     | App + filtros + 4 seções + form de predição           |
| —     | Boundary Keeper | O que NÃO é desta fase            | Deploy, treino, auth, reescrita das stats v1          |
| —     | Failure Analyst | O que invalida o resultado        | App não sobe; predição/erro; recompute a cada filtro  |

---

*Phase: 02-dashboard-interativo*
*Spec created: 2026-06-22 (modo --auto: decisões-chave coletadas via AskUserQuestion)*
*Next step: /gsd:discuss-phase 2 — decisões de implementação (layout, navegação, plotly vs matplotlib, inputs do form)*
