# External Integrations

**Analysis Date:** 2026-06-22

## APIs & External Services

None. This project has no network calls, HTTP clients, or external API integrations. All computation is fully offline and local.

## Data Storage

**Databases:**
- None. No database connection of any kind.

**File Storage — Input:**
- Local CSV file: `dataset/raw/heart.csv`
  - 918 rows x 12 columns
  - Source dataset: Heart Failure Prediction Dataset (Kaggle / UCI ML Repository)
  - Read exclusively via `pandas.read_csv()` in `src/data_loader.py` (`load_raw()`)
  - Path constant: `DATA_RAW` in `src/config.py`

**File Storage — Output:**
- `output/figures/` — PNG plots (300 dpi) written by `src/plotting.py` via `fig.savefig()`
  - Figures currently present: `00_prevalencia_hd.png`, `02_bar_*.png`, `02_grouped_*.png`, `03_*.png`, `04_*.png`
- `output/tables/` — CSV frequency and descriptive tables written by notebooks
  - Files currently present: `freq_*.csv`, `crosstab_*.csv`, `desc_*.csv`
- `RELATORIO.docx` — final academic report written by `src/generate_report.py` via `python-docx`

**Caching:**
- None.

## Authentication & Identity

None. No auth layer of any kind.

## Monitoring & Observability

**Error Tracking:**
- None.

**Logs:**
- Plain `print()` statements in `validate_data.py` and `src/generate_report.py` (stdout only)

## CI/CD & Deployment

**Hosting:**
- Not applicable. Local analysis project only.

**CI Pipeline:**
- None (no GitHub Actions, no CI config files).

## Environment Configuration

**Required env vars:**
- None. All paths are resolved from `__file__` using `pathlib.Path` in `src/config.py`.

**Secrets location:**
- Not applicable. No secrets needed.

## Webhooks & Callbacks

**Incoming:**
- None.

**Outgoing:**
- None.

## Dataset Origin

The source data (`dataset/raw/heart.csv`) is a public dataset derived from the combination of five clinical databases (Cleveland, Hungarian, Switzerland, Long Beach VA, Stalog). It is referenced in `generate_report.py` as:

> FEDESORIANO. Heart Failure Prediction Dataset. Kaggle, 2021.
> https://www.kaggle.com/datasets/fedesoriano/heart-failure-prediction

The file is committed to the repository and is not fetched at runtime.

## Notebook-to-Module Data Flow

Notebooks in `notebooks/` import from `src/` via `sys.path` manipulation (see `notebooks/01_preprocessing.ipynb`). No inter-process communication occurs; the flow is:

1. Notebooks read `dataset/raw/heart.csv` via `src.data_loader.load_raw()` or `load_subsets()`
2. Notebooks write computed tables to `output/tables/*.csv` via `DataFrame.to_csv()`
3. Notebooks write figures to `output/figures/*.png` via `src.plotting` functions
4. `src/generate_report.py` reads `output/tables/*.csv` and `output/figures/*.png` to assemble `RELATORIO.docx`

---

*Integration audit: 2026-06-22*
