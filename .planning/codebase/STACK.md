# Technology Stack

**Analysis Date:** 2026-06-22

## Languages

**Primary:**
- Python 3.11.9 — all source modules, notebooks, and report generation

## Runtime

**Environment:**
- CPython 3.11.9

**Package Manager:**
- pip (implied by `requirements.txt`)
- Lockfile: absent (only `requirements.txt` with `>=` version pins)

## Frameworks

**Core:**
- pandas >= 2.0 — DataFrame operations, CSV I/O, crosstabs, `pd.cut` for binning
- numpy >= 1.24 — numeric arrays, `np.linspace`, Sturges bin calculation
- scipy >= 1.11 — `scipy.stats.kurtosis` (excess kurtosis), `scipy.stats.gaussian_kde` (density curve on histograms)

**Visualization:**
- matplotlib >= 3.7 — base plotting engine; used directly in `src/plotting.py` for bar charts, histograms, and boxplots; DPI=300, white background
- seaborn >= 0.13 — imported in `src/plotting.py` (`import seaborn as sns`); available but not currently called in any plotting function (matplotlib used directly)

**Report Generation:**
- python-docx (imported as `docx`) — builds `RELATORIO.docx` via `src/generate_report.py`; uses `Document`, `OxmlElement`, `WD_ALIGN_PARAGRAPH`, `Cm`, `Pt`, `RGBColor`; not listed explicitly in `requirements.txt` but required at runtime

**Notebook Environment:**
- jupyter >= 1.0 — notebook runner
- notebook >= 7.0 — classic Notebook UI

**Testing:**
- None (no test framework detected; `validate_data.py` is a standalone assertion script, not a pytest/unittest suite)

**Build/Dev:**
- No build system (no `setup.py`, `pyproject.toml`, `Makefile`, or `tox.ini`)

## Key Dependencies

**Critical:**
- `pandas >= 2.0` — all data loading, filtering, frequency tables, and descriptive statistics flow through DataFrames; `src/data_loader.py`, `src/frequency_tables.py`, `src/descriptive_stats.py`
- `python-docx` (undeclared) — required to run `src/generate_report.py` and produce `RELATORIO.docx`; missing from `requirements.txt`
- `scipy >= 1.11` — provides `kurtosis` (used in every `descriptive_summary` call) and `gaussian_kde` (histogram density curve)

**Infrastructure:**
- `matplotlib >= 3.7` — every plot in `src/plotting.py` uses `plt.subplots`; figures saved at 300 dpi to `output/figures/`
- `numpy >= 1.24` — Sturges bin edges via `np.linspace`; `np.ndarray` typing in `src/frequency_tables.py`

## Configuration

**Environment:**
- No `.env` file; no environment variables required
- All paths resolved programmatically via `pathlib.Path(__file__).resolve().parent.parent` in `src/config.py`
- Key path constants: `DATA_RAW`, `OUTPUT_FIGURES`, `OUTPUT_TABLES` — all defined in `src/config.py`

**Build:**
- No build config files
- Global matplotlib style applied at plot time via `plt.rcParams.update(MPL_STYLE)` (defined in `src/config.py`)

## Platform Requirements

**Development:**
- Python 3.11+
- Jupyter Notebook 7+ for interactive notebooks in `notebooks/`
- `python-docx` must be installed manually (not in `requirements.txt`)

**Production:**
- Offline/local only — no server, no deployment target
- All inputs are local files (`dataset/raw/heart.csv`); all outputs are local files (`output/figures/*.png`, `output/tables/*.csv`, `RELATORIO.docx`)

---

*Stack analysis: 2026-06-22*
