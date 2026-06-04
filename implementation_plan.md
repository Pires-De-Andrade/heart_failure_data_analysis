# Análise Estatística — Heart Disease Dataset

## Contexto e Pergunta de Pesquisa

**Pergunta:** Qual é o perfil clínico de pacientes com e sem diagnóstico de doença cardíaca, e quais indicadores — demográficos, hemodinâmicos e eletrocardiográficos — se mostram mais informativos para distinguir os dois grupos?

**Dataset:** 918 pacientes, 12 variáveis, combinação de 5 bases clínicas (Cleveland, Hungria, Suíça, Long Beach, Stalog).

**Prevalência:** HeartDisease=1: 508 (55,3%) | HeartDisease=0: 410 (44,7%)

---

## Dados Validados

| Métrica | Valor |
|---|---|
| Total de linhas | 918 |
| Cholesterol = 0 | 172 linhas (18,7%) |
| RestingBP = 0 | 1 linha (linha 451: `55,M,NAP,0,0,...`) |
| Sex: M / F | 725 / 193 |
| Age range | 28–77 |
| Oldpeak range | −2,6 a 6,2 |

---

## Decisões de Pré-processamento

> [!IMPORTANT]
> Estas decisões precisam ser documentadas explicitamente no relatório final.

1. **Cholesterol = 0 (172 obs):** Excluir **apenas** das análises que envolvem Cholesterol. As demais análises usam n=918. Justificativa: valor biologicamente impossível → dado ausente codificado. Imputar pela média introduziria viés artificial.

2. **RestingBP = 0 (1 obs, linha 451):** Excluir **apenas** das análises que envolvem RestingBP. Justificativa: pressão arterial zero é impossível em paciente vivo.

3. **Nenhuma outra transformação** — o dataset não tem valores nulos explícitos nem duplicatas documentadas.

---

## Estrutura do Projeto

```
prob_est_trabalho/
├── dataset/
│   ├── raw/
│   │   └── heart.csv              # (existente)
│   └── processed/                  # (vazio — mantém)
├── notebooks/
│   ├── 01_preprocessing.ipynb      # [NEW] Carga, limpeza, EDA inicial
│   ├── 02_qualitative.ipynb        # [NEW] Bloco 1 — Variáveis qualitativas
│   ├── 03_discrete.ipynb           # [NEW] Bloco 2 — Age (quantitativa discreta)
│   └── 04_continuous.ipynb         # [NEW] Bloco 3 — Variáveis quantitativas contínuas
├── src/
│   ├── __init__.py                 # [NEW]
│   ├── config.py                   # [NEW] Constantes, paths, paleta de cores
│   ├── data_loader.py              # [NEW] Funções de carga e limpeza
│   ├── descriptive_stats.py        # [NEW] Funções de medidas descritivas
│   ├── frequency_tables.py         # [NEW] Tabelas de frequência (fi, fri, Fi, Fri)
│   └── plotting.py                 # [NEW] Funções de visualização padronizadas
├── output/
│   ├── figures/                    # [NEW] PNGs exportados dos gráficos
│   └── tables/                     # [NEW] CSVs das tabelas de frequência
├── requirements.txt                # [NEW]
└── README.md                       # [NEW]
```

---

## Tecnologias

| Biblioteca | Uso |
|---|---|
| `pandas` | Manipulação de dados |
| `numpy` | Cálculos numéricos |
| `matplotlib` | Gráficos base |
| `seaborn` | Gráficos estatísticos |
| `scipy.stats` | Assimetria, curtose |
| `jupyter` | Notebooks interativos |

---

## Plano Analítico Detalhado

### Notebook 01 — Pré-processamento (`01_preprocessing.ipynb`)

- Carga do CSV e inspeção (`shape`, `dtypes`, `describe`, `info`)
- Identificação e documentação dos zeros em Cholesterol e RestingBP
- Criação de subsets filtrados:
  - `df_full` (n=918) — para análises gerais
  - `df_chol` (n=746) — excluindo Cholesterol=0
  - `df_bp` (n=917) — excluindo RestingBP=0
- Panorama geral: distribuição de HeartDisease, Sex, Age

---

### Notebook 02 — Variáveis Qualitativas (`02_qualitative.ipynb`)

**Variáveis:** `Sex`, `ChestPainType`, `RestingECG`, `ExerciseAngina`, `ST_Slope`, `FastingBS`

Para cada variável:
1. **Tabela de frequência absoluta e relativa** (geral e cruzada com HeartDisease)
2. **Gráfico de barras** — distribuição geral
3. **Gráfico de barras empilhadas/agrupadas** — cruzamento com HeartDisease
4. **Comentário analítico** à luz da pergunta de pesquisa

Distribuições observadas que merecem destaque:
- `ChestPainType`: ASY=496 (54%) — tipologia dominante, provavelmente associada a HeartDisease
- `ExerciseAngina`: N=547 vs Y=371
- `ST_Slope`: Flat=460 (50%) — forte indicador potencial

---

### Notebook 03 — Variável Quantitativa Discreta (`03_discrete.ipynb`)

**Variável:** `Age` (28–77 anos)

1. **Faixas etárias** com amplitude 10:
   - < 40 | 40–49 | 50–59 | 60–69 | ≥ 70

2. **Tabela de frequências:** fi, fri, Fi, Fri

3. **Histograma de barras** com faixas etárias

4. **Medidas descritivas:**
   - Tendência central: média, mediana, moda
   - Dispersão: desvio-padrão, variância, coeficiente de variação (CV)
   - Forma: coeficiente de assimetria (Pearson), curtose
   - Fórmulas para dados agrupados em classes

5. **Boxplot** com interpretação de quartis e outliers

6. **Boxplot comparativo** HeartDisease=0 vs HeartDisease=1

---

### Notebook 04 — Variáveis Quantitativas Contínuas (`04_continuous.ipynb`)

**Variáveis:** `RestingBP` (n=917), `Cholesterol` (n=746), `MaxHR` (n=918), `Oldpeak` (n=918)

Para cada variável:

1. **Número de classes pela regra de Sturges:**
   - k = 1 + 3,322 · log₁₀(n)
   - Para n=918: k ≈ 10,8 → 11 classes
   - Para n=746 (Cholesterol): k ≈ 10,5 → 11 classes
   - Para n=917 (RestingBP): k ≈ 10,8 → 11 classes

2. **Tabela de frequências completa:** fi, fri (%), Fi, Fri (%)

3. **Histograma com curva de densidade sobreposta**

4. **Medidas descritivas completas:**
   - Tendência central: média, mediana, moda (por fórmula de dados agrupados)
   - Dispersão: amplitude, variância, desvio-padrão, CV
   - Forma: assimetria (skewness), curtose (kurtosis)
   - Separatrizes: Q1, Q2 (mediana), Q3

5. **Boxplot comparativo** por grupo HeartDisease

> [!NOTE]
> **Oldpeak** merece atenção especial: range de −2,6 a 6,2, com muitos zeros. Distribuição assimétrica à direita com concentração no zero — produzirá medidas de assimetria interessantes para comentar no relatório.

---

## Estrutura do Relatório Final

O relatório segue a narrativa da pergunta de pesquisa, não a ordem dos notebooks:

1. **Introdução** — contexto clínico (CVD como principal causa de morte), base de dados (5 fontes), pergunta de pesquisa, decisões de pré-processamento
2. **Perfil da Amostra** — quem são os 918 pacientes? Distribuição de idade, sexo, prevalência
3. **Análise Qualitativa** — cada variável com tabela e gráfico, cruzada com HeartDisease
4. **Análise Quantitativa Discreta** — Age com faixas, tabelas, boxplot, descritivas
5. **Análise Quantitativa Contínua** — RestingBP, Cholesterol, MaxHR, Oldpeak com classes, histogramas, descritivas, boxplots comparativos
6. **Síntese e Conclusões** — quais indicadores distinguem mais os dois grupos? Perfil de risco cardíaco

---

## Open Questions

> [!IMPORTANT]
> **Formato de entrega:** O relatório final deve ser entregue em qual formato? PDF gerado a partir dos notebooks? Documento Word? Apresentação? Isso afeta como estruturamos a exportação.

> [!IMPORTANT]
> **Idioma do código:** Os comentários e nomes de funções no código devem ser em português ou inglês? Os gráficos e tabelas precisam ter labels em português para o relatório?

> [!IMPORTANT]
> **Escopo das fórmulas:** O roteiro exige que as fórmulas de medidas descritivas para dados agrupados apareçam no relatório (ex.: média para dados agrupados = Σ(xi·fi)/n)? Ou basta calcular com Python e reportar os resultados?

> [!WARNING]
> **Ambiente Python:** Você já possui Python e Jupyter instalados? Preciso verificar quais dependências estão disponíveis antes de começar a implementação.

---

## Plano de Verificação

### Testes Automatizados
- Verificar que `df_full.shape[0] == 918`
- Verificar que `df_chol.shape[0] == 746` (918 − 172)
- Verificar que `df_bp.shape[0] == 917` (918 − 1)
- Verificar que as somas de frequências relativas = 100% em cada tabela
- Verificar que Fi da última classe = n
- Cross-check: medidas descritivas calculadas manualmente vs `pandas.describe()`

### Verificação Visual
- Todos os gráficos exportados em `output/figures/` com resolução adequada (300 dpi)
- Tabelas exportadas em `output/tables/` como CSV
- Revisão visual dos boxplots para coerência com descritivas

### Verificação Narrativa
- Cada análise responde à pergunta de pesquisa?
- Cruzamento com HeartDisease está presente em todos os blocos?
- Decisões de pré-processamento estão documentadas?
