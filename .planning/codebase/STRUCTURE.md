# Codebase Structure

**Analysis Date:** 2026-06-22

## Directory Layout

```
heart_failure_data_analysis/
├── src/                        # Reusable Python analysis library (package)
│   ├── __init__.py             # Package marker (empty comment block)
│   ├── config.py               # All constants, paths, labels, palette
│   ├── data_loader.py          # CSV loading and subset creation
│   ├── frequency_tables.py     # fi/fri/Fi/Fri computation, Sturges bins
│   ├── descriptive_stats.py    # Descriptive measures, Pearson-2 skewness, kurtosis
│   ├── plotting.py             # Bar charts, histograms, boxplots; auto-save to output/figures/
│   └── generate_report.py      # Assemble RELATORIO.docx from output/ artefacts
│
├── notebooks/                  # Jupyter notebooks — orchestrate analysis per variable type
│   ├── 01_preprocessing.ipynb  # Data inspection, missing-value identification
│   ├── 02_qualitative.ipynb    # Qualitative variables (Sex, ChestPainType, RestingECG, ExerciseAngina, ST_Slope, FastingBS)
│   ├── 03_discrete.ipynb       # Discrete quantitative variable (Age)
│   └── 04_continuous.ipynb     # Continuous quantitative variables (RestingBP, Cholesterol, MaxHR, Oldpeak)
│
├── dataset/
│   └── raw/
│       └── heart.csv           # Source dataset — 918 rows × 12 columns; never modified
│
├── output/
│   ├── figures/                # Generated PNG charts (300 dpi); committed with .gitkeep
│   │   ├── 00_prevalencia_hd.png
│   │   ├── 02_bar_*.png        # Simple bar charts for qualitative variables
│   │   ├── 02_grouped_*.png    # Grouped bar charts (variable × HeartDisease)
│   │   ├── 03_boxplot_*.png    # Boxplots for Age (single and by group)
│   │   ├── 03_hist_*.png       # Histogram for Age faixas
│   │   ├── 04_hist_*.png       # Histograms for continuous variables
│   │   └── 04_boxplot_*_vs_HD.png  # Comparative boxplots for continuous variables
│   │
│   └── tables/                 # Generated CSV tables; committed with .gitkeep
│       ├── freq_*.csv          # Frequency tables (fi, fri, Fi, Fri)
│       ├── crosstab_*.csv      # Contingency tables (variable × HeartDisease)
│       └── desc_*.csv          # Descriptive statistics tables (global and by group)
│
├── .planning/
│   └── codebase/               # Architecture and planning documents
│
├── validate_data.py            # Standalone smoke-test script
├── requirements.txt            # Python dependency pins
├── RELATORIO.docx              # Generated final report (output artefact)
├── tables_dump.txt             # Ad-hoc data dump (informational)
├── roteiro_trabalho.pdf        # Assignment brief (reference document)
└── README.md                   # Project overview and analysis narrative
```

## Directory Purposes

**`src/`:**
- Purpose: Importable Python package containing all reusable analysis logic.
- Contains: Six modules covering configuration, data loading, statistical computation, visualisation, and report generation.
- Key files: `src/config.py` (must be read first for any new module), `src/generate_report.py` (only entry point producing a deliverable file).

**`notebooks/`:**
- Purpose: Per-analysis-block Jupyter notebooks that orchestrate calls to `src/` modules and persist results to `output/`.
- Contains: Four notebooks numbered to indicate run order.
- Key files: `notebooks/01_preprocessing.ipynb` (must run before others), `notebooks/04_continuous.ipynb` (heaviest computation).

**`dataset/raw/`:**
- Purpose: Immutable source data — never written to by any script.
- Contains: `dataset/raw/heart.csv` — 918 rows, 12 columns (Age, Sex, ChestPainType, RestingBP, Cholesterol, FastingBS, RestingECG, MaxHR, ExerciseAngina, Oldpeak, ST_Slope, HeartDisease).

**`output/figures/`:**
- Purpose: Destination for all generated PNG charts saved by `src/plotting.py` (`_save()` helper).
- Generated: Yes — by notebooks calling plotting functions with a `filename=` argument.
- Committed: Yes (with `.gitkeep` placeholder).
- Naming pattern: `<notebook_prefix>_<chart_type>_<variable>.png` (e.g., `02_grouped_Sex.png`, `04_boxplot_Cholesterol_vs_HD.png`).

**`output/tables/`:**
- Purpose: Destination for all generated CSV tables saved by notebooks via `df.to_csv(OUTPUT_TABLES / name)`.
- Generated: Yes — by notebooks.
- Committed: Yes (with `.gitkeep` placeholder).
- Naming pattern: `<type>_<variable>[_por_grupo].csv` (e.g., `freq_Sex.csv`, `desc_Age_por_grupo.csv`, `crosstab_RestingECG.csv`).

## Key File Locations

**Entry Points:**
- `src/generate_report.py`: Final deliverable generator — run via `python -m src.generate_report` after notebooks complete.
- `validate_data.py`: Data and module smoke-test — run via `python validate_data.py`.
- `notebooks/01_preprocessing.ipynb`: First notebook to run.

**Configuration:**
- `src/config.py`: All paths, variable group lists, display labels, color palette constants, figure sizes, and matplotlib style dict. Read this before creating any new module or notebook.

**Core Logic:**
- `src/data_loader.py`: `load_subsets()` — the canonical way to obtain analysis-ready DataFrames.
- `src/frequency_tables.py`: `freq_table_qualitative()`, `freq_table_classes()`, `freq_table_crosstab()`, `sturges_bins()`.
- `src/descriptive_stats.py`: `descriptive_summary()`, `descriptive_by_group()`, `pearson2_skewness()`.
- `src/plotting.py`: `bar_chart()`, `bar_chart_grouped()`, `histogram()`, `boxplot_single()`, `boxplot_comparison()`.

**Source Data:**
- `dataset/raw/heart.csv`: Only file that should ever be read by `data_loader.load_raw()`.

**Generated Artefacts:**
- `output/tables/*.csv`: Read by `src/generate_report.py`; written by notebooks.
- `output/figures/*.png`: Read by `src/generate_report.py`; written by `src/plotting.py` called from notebooks.
- `RELATORIO.docx`: Final deliverable written by `src/generate_report.py`.

**Reference Documents:**
- `requirements.txt`: Python dependencies.
- `roteiro_trabalho.pdf`: Assignment brief (not read by code).

## Naming Conventions

**Python modules:**
- `snake_case.py` — e.g., `data_loader.py`, `descriptive_stats.py`, `frequency_tables.py`.

**Python functions:**
- `snake_case` — e.g., `load_subsets()`, `freq_table_qualitative()`, `descriptive_by_group()`, `pearson2_skewness()`.
- Private helpers in `plotting.py` and `generate_report.py` use `_leading_underscore` — e.g., `_save()`, `_apply_style()`, `_shade_cell()`, `_merge_desc()`.

**Output files:**
- Tables: `<type>_<VariableName>[_por_grupo].csv` where `<type>` is `freq`, `crosstab`, or `desc`.
- Figures: `<notebook_number>_<chart_type>_<VariableName>[_vs_HD].png` where `<chart_type>` is `bar`, `grouped`, `hist`, `boxplot`.

**Notebooks:**
- `<NN>_<topic>.ipynb` with zero-padded two-digit prefix indicating run order.

**Config constants:**
- `UPPER_SNAKE_CASE` for all module-level constants in `src/config.py` — e.g., `DATA_RAW`, `QUAL_VARS`, `PALETTE_HD`, `FIGSIZE_SINGLE`.

## Where to Add New Code

**New statistical measure:**
- Implementation: `src/descriptive_stats.py` — add a new function following the pattern of `descriptive_summary()` (takes `pd.Series`, returns `pd.DataFrame` with `Medida` index).
- Register any new variable-group constants in `src/config.py`.

**New variable to analyse:**
- Add the variable name to the appropriate list in `src/config.py` (`QUAL_VARS`, or create a new group list).
- Add display label to `VAR_LABELS` and category mapping to `CAT_LABELS` in `src/config.py`.
- Call existing computation functions from the appropriate notebook; save outputs with the standard naming pattern.

**New chart type:**
- Implementation: `src/plotting.py` — add a new function following the pattern of existing functions: call `_apply_style()`, build figure, call `_save(fig, filename)` if `filename` is provided, return `(fig, ax)`.

**New frequency table variant:**
- Implementation: `src/frequency_tables.py` — add a new function that returns a `pd.DataFrame` with the standard column names.

**New analysis notebook:**
- Location: `notebooks/` — name as `<NN>_<topic>.ipynb` with the next available number prefix.
- Import pattern: `from src.config import ...` and `from src.data_loader import load_subsets`.

**Utilities / shared helpers:**
- Shared computation helpers: `src/descriptive_stats.py` or `src/frequency_tables.py`.
- Shared visualisation helpers: `src/plotting.py` (private helpers prefixed `_`).
- Constants and paths: always `src/config.py`.

## Special Directories

**`src/__pycache__/`:**
- Purpose: Python bytecode cache generated automatically.
- Generated: Yes.
- Committed: No (should be in `.gitignore`).

**`output/figures/` and `output/tables/`:**
- Purpose: Filesystem communication channel between notebook layer and report layer.
- Generated: Yes — by notebooks and `src/plotting.py`.
- Committed: Yes (artefacts are committed alongside source; `.gitkeep` files ensure directories exist in fresh clones before any notebook is run).

**`.planning/codebase/`:**
- Purpose: Architecture and planning documents for GSD tooling.
- Generated: Yes — by GSD mapper.
- Committed: Yes.

---

*Structure analysis: 2026-06-22*
