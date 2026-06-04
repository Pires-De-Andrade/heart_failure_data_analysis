# Análise Estatística — Heart Disease Dataset

Trabalho de Probabilidade e Estatística: análise descritiva do perfil clínico
de pacientes com e sem diagnóstico de doença cardíaca.

## Pergunta de Pesquisa

> Qual é o perfil clínico de pacientes com e sem diagnóstico de doença
> cardíaca, e quais indicadores — demográficos, hemodinâmicos e
> eletrocardiográficos — se mostram mais informativos para distinguir
> os dois grupos?

## Dataset

- **Fonte:** Heart Failure Prediction Dataset (combinação de 5 bases clínicas)
- **Observações:** 918 pacientes, 12 variáveis
- **Variável-alvo:** `HeartDisease` (0 = sem doença, 1 = com doença)

## Estrutura do Projeto

```
prob_est_trabalho/
├── dataset/raw/heart.csv          # Dados brutos
├── notebooks/
│   ├── 01_preprocessing.ipynb     # Carga, limpeza, panorama geral
│   ├── 02_qualitative.ipynb       # Variáveis qualitativas
│   ├── 03_discrete.ipynb          # Age (quantitativa discreta)
│   └── 04_continuous.ipynb        # RestingBP, Cholesterol, MaxHR, Oldpeak
├── src/
│   ├── config.py                  # Constantes e paleta de cores
│   ├── data_loader.py             # Carga e subsets
│   ├── descriptive_stats.py       # Medidas descritivas (Pearson 2)
│   ├── frequency_tables.py        # Tabelas fi/fri/Fi/Fri
│   └── plotting.py                # Funções de visualização
├── output/
│   ├── figures/                   # Gráficos exportados (300 dpi)
│   └── tables/                    # Tabelas em CSV
└── requirements.txt
```

## Como executar

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar notebooks na ordem
cd notebooks
jupyter notebook
```

## Decisões de Pré-processamento

| Variável    | Problema            | Decisão                     |
|-------------|--------------------|-----------------------------|
| Cholesterol | 172 valores = 0    | Excluir dessas análises     |
| RestingBP   | 1 valor = 0        | Excluir dessa análise       |

## Coeficiente de Assimetria

Todas as análises reportam o **Pearson 2**: `AS = 3 × (média − mediana) / σ`.
O `scipy.stats.skew()` é calculado apenas como verificação interna.
