<!-- refreshed: 2026-06-22 -->
# Architecture

**Analysis Date:** 2026-06-22

## System Overview

```text
┌──────────────────────────────────────────────────────────────────┐
│                      Notebooks (Exploratory)                      │
│  `notebooks/01_preprocessing.ipynb`  `02_qualitative.ipynb`      │
│  `notebooks/03_discrete.ipynb`        `04_continuous.ipynb`      │
└────────────────────────┬─────────────────────────────────────────┘
                         │  import src.*
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                     src/ — Analysis Library                       │
├──────────────┬──────────────────┬─────────────┬──────────────────┤
│ data_loader  │ frequency_tables │ descriptive │    plotting       │
│    .py       │      .py         │  _stats.py  │     .py          │
│ `src/data_   │ `src/frequency_  │ `src/desc-  │ `src/plotting.py`│
│  loader.py`  │  tables.py`      │  riptive_   │                  │
│              │                  │  stats.py`  │                  │
└──────┬───────┴────────┬─────────┴──────┬──────┴────────┬─────────┘
       │                │                │               │
       ▼                ▼                ▼               ▼
┌──────────────────────────────────────────────────────────────────┐
│              src/config.py  (constants, paths, palette)           │
└──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Outputs                                       │
│  `output/tables/*.csv`            `output/figures/*.png`          │
└────────────────────────┬─────────────────────────────────────────┘
                         │  read by
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│              src/generate_report.py  → RELATORIO.docx             │
└──────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| config | Project-wide constants: paths, variable lists, color palette, figure sizes | `src/config.py` |
| data_loader | Load raw CSV; produce cleaned subsets (full/chol/bp) | `src/data_loader.py` |
| frequency_tables | Compute fi/fri/Fi/Fri tables for qualitative and numeric-class variables; Sturges bins | `src/frequency_tables.py` |
| descriptive_stats | Compute mean, median, mode, variance, std, CV, quartiles, Pearson-2 skewness, excess kurtosis | `src/descriptive_stats.py` |
| plotting | Render bar charts, grouped bar charts, histograms, single boxplots, comparative boxplots; save to `output/figures/` | `src/plotting.py` |
| generate_report | Assemble RELATORIO.docx from pre-computed CSVs and PNGs using python-docx | `src/generate_report.py` |
| notebooks | Orchestrate per-variable analysis: call src modules, save tables and figures | `notebooks/01_preprocessing.ipynb` … `notebooks/04_continuous.ipynb` |
| validate_data | Smoke-test assertions for row counts, fi sums, and descriptive values | `validate_data.py` |

## Pattern Overview

**Overall:** Two-phase pipeline — notebooks produce artefacts; report script consumes artefacts.

**Key Characteristics:**
- Shared library (`src/`) separates reusable logic from notebook orchestration.
- All global configuration (paths, variable names, colors, figure sizes) is centralised in `src/config.py`; no magic strings elsewhere.
- Outputs are file-system artefacts (CSV tables, PNG figures), not in-memory objects — notebooks and report script communicate through the filesystem.
- The report generation step (`src/generate_report.py`) is fully decoupled from computation: it only reads pre-existing files.

## Layers

**Configuration Layer:**
- Purpose: Single source of truth for paths, variable lists, labels, and visual style.
- Location: `src/config.py`
- Contains: `PROJECT_ROOT`, `DATA_RAW`, `OUTPUT_FIGURES`, `OUTPUT_TABLES`, variable group lists (`QUAL_VARS`, `DISC_VAR`, `CONT_VARS`), age bins, `VAR_LABELS`, `CAT_LABELS`, `PALETTE_HD`, `PALETTE_QUAL`, `MPL_STYLE`, figure size constants.
- Depends on: `pathlib.Path` only.
- Used by: every other `src/` module and all notebooks.

**Data Layer:**
- Purpose: Load raw CSV and expose clean sub-DataFrames.
- Location: `src/data_loader.py`
- Contains: `load_raw()` → unmodified DataFrame (n=918); `load_subsets()` → dict with `df_full`, `df_chol` (n=746), `df_bp` (n=917).
- Depends on: `src/config.py` for `DATA_RAW`.
- Used by: notebooks.

**Computation Layer:**
- Purpose: Stateless functions that transform a pandas Series or DataFrame into a result DataFrame.
- Location: `src/frequency_tables.py`, `src/descriptive_stats.py`
- Contains: `freq_table_qualitative`, `freq_table_classes`, `freq_table_crosstab`, `sturges_k`, `sturges_bins`, `descriptive_summary`, `descriptive_by_group`, `pearson2_skewness`, interpretation helpers.
- Depends on: `numpy`, `pandas`, `scipy.stats`; no cross-dependency between the two files.
- Used by: notebooks (which then save results to `output/tables/`).

**Visualisation Layer:**
- Purpose: Render and save standardised charts.
- Location: `src/plotting.py`
- Contains: `bar_chart`, `bar_chart_grouped`, `histogram`, `boxplot_single`, `boxplot_comparison`.
- Depends on: `matplotlib`, `seaborn`, `scipy.stats.gaussian_kde`; `src/config.py` for palette and path.
- Used by: notebooks (which call plotting functions with a `filename=` argument to trigger auto-save).

**Notebook Orchestration Layer:**
- Purpose: Drive per-analysis-block workflow — load data, call computation and plotting functions, save artefacts.
- Location: `notebooks/` (four Jupyter notebooks).
- Contains: per-variable analysis sequences; each notebook covers one variable category.
- Depends on: all `src/` modules.
- Used by: the analyst (manual run); not imported by any other code.

**Report Assembly Layer:**
- Purpose: Produce the final Word document from filesystem artefacts.
- Location: `src/generate_report.py`
- Contains: `build()` function, helper utilities (`add_table`, `add_figure`, `read_csv`, `freq_rows`, `crosstab_rows`, `desc_rows`, `_merge_desc`, `fmt_num`).
- Depends on: `python-docx`, `pandas`; reads `output/tables/*.csv` and `output/figures/*.png`.
- Used by: invoked via `python -m src.generate_report` after notebooks have run.

## Data Flow

### Primary Analysis Path (run notebooks first)

1. Raw data loaded from `dataset/raw/heart.csv` via `data_loader.load_subsets()` (`src/data_loader.py`)
2. Notebook calls computation functions in `src/frequency_tables.py` or `src/descriptive_stats.py`, passing the relevant DataFrame subset.
3. Result DataFrames are saved as CSV to `output/tables/` (e.g., `output/tables/freq_Sex.csv`, `output/tables/desc_Age.csv`).
4. Notebook calls plotting functions in `src/plotting.py` with a `filename=` argument; function saves PNG to `output/figures/` at 300 dpi.
5. Notebooks run in order: `01_preprocessing.ipynb` → `02_qualitative.ipynb` → `03_discrete.ipynb` → `04_continuous.ipynb`.

### Report Generation Path (run after notebooks)

1. `build()` in `src/generate_report.py` is invoked.
2. `read_csv(name)` reads from `output/tables/<name>`.
3. Helper functions (`freq_rows`, `crosstab_rows`, `desc_rows`, `_merge_desc`) transform CSV rows into display-ready lists, formatting numbers with Brazilian locale (`fmt_num`).
4. `add_table()` inserts a styled python-docx table; `add_figure()` embeds a PNG.
5. `doc.save()` writes `RELATORIO.docx` to the project root.

**State Management:**
- No shared in-memory state between layers. All communication happens through the filesystem (`output/tables/`, `output/figures/`). Each function receives its data as arguments.

## Key Abstractions

**Dataset Subsets:**
- Purpose: Encapsulate per-variable missing-value exclusions so notebooks never re-implement the filter logic.
- Examples: `df_full` (n=918), `df_chol` (n=746), `df_bp` (n=917), all returned by `load_subsets()` in `src/data_loader.py`.
- Pattern: dict of DataFrames keyed by descriptive name.

**Frequency Table:**
- Purpose: Uniform representation of fi/fri/Fi/Fri for any variable type.
- Examples: `src/frequency_tables.py` — `freq_table_qualitative()`, `freq_table_classes()`.
- Pattern: function returns a `pd.DataFrame` with index named after the variable and fixed column names (`fi`, `fri (%)`, `Fi`, `Fri (%)`).

**Descriptive Summary:**
- Purpose: Standard set of 14 measures always computed together.
- Examples: `descriptive_summary()` and `descriptive_by_group()` in `src/descriptive_stats.py`.
- Pattern: function returns a `pd.DataFrame` with `Medida` index and one column per group; column name is caller-provided.

**Plotting Functions:**
- Purpose: Consistent visual identity across all figures, auto-save to `output/figures/`.
- Examples: `bar_chart`, `bar_chart_grouped`, `histogram`, `boxplot_single`, `boxplot_comparison` in `src/plotting.py`.
- Pattern: each function calls `_apply_style()`, builds the figure, optionally calls `_save(fig, filename)`, returns `(fig, ax)`.

## Entry Points

**Notebook Execution:**
- Location: `notebooks/` — four `.ipynb` files.
- Triggers: Analyst runs Jupyter and executes cells manually or via `jupyter nbconvert --to notebook --execute`.
- Responsibilities: Orchestrate the full analysis pipeline for one variable category per notebook; persist all artefacts to `output/`.

**Report Generation:**
- Location: `src/generate_report.py` → `build()`.
- Triggers: `python -m src.generate_report` from project root (requires all notebooks to have completed).
- Responsibilities: Read all artefacts from `output/`, assemble styled Word document, save `RELATORIO.docx`.

**Validation Script:**
- Location: `validate_data.py`.
- Triggers: `python validate_data.py` from project root.
- Responsibilities: Import all `src/` modules, run assertion checks on row counts and statistical outputs, print pass/fail summary.

## Architectural Constraints

- **Global state:** None. All module-level objects in `src/config.py` are immutable constants (`Path`, `int`, `list`, `dict`). `src/plotting.py` modifies `plt.rcParams` via `_apply_style()` each call — this is a process-level side effect but does not persist across notebook restarts.
- **Circular imports:** None. Dependency direction is strictly: `generate_report`/notebooks → `plotting`/`frequency_tables`/`descriptive_stats` → `config`. No back-edges.
- **Threading:** Single-threaded; all processing is sequential within each notebook cell.
- **Python package:** `src/` is a package (has `src/__init__.py`); modules must be imported as `from src.config import ...` or `from .config import ...` when inside the package. `validate_data.py` adds `.` to `sys.path` to enable this from the project root.

## Anti-Patterns

### Running `generate_report.py` before notebooks

**What happens:** `read_csv(name)` raises `FileNotFoundError` because no CSVs exist in `output/tables/`.
**Why it's wrong:** The report layer depends on artefacts produced by the notebook layer; there is no guard or helpful error message.
**Do this instead:** Run all four notebooks in order (`01` through `04`) before invoking `python -m src.generate_report`. The `validate_data.py` script can serve as a quick sanity check first.

### Adding analysis logic directly in notebooks instead of `src/`

**What happens:** Duplicated computation code accumulates across notebooks; fixes must be applied in multiple places.
**Why it's wrong:** The `src/` library exists precisely to be the single location for reusable logic.
**Do this instead:** Implement new statistical functions in `src/descriptive_stats.py` or `src/frequency_tables.py` and import them in the notebook.

## Error Handling

**Strategy:** Minimal — functions assume clean input matching the contract from `load_subsets()`.

**Patterns:**
- `add_figure()` in `src/generate_report.py` degrades gracefully: if the PNG does not exist it inserts a `[Figura ausente: <filename>]` placeholder rather than raising.
- `fmt_num()` catches `ValueError`/`TypeError` and returns the raw string; `pd.isna()` check returns an em-dash for NaN values.
- `validate_data.py` uses `assert` statements to surface data-contract violations during development; no exception handling in production code paths.

## Cross-Cutting Concerns

**Logging:** `print()` statements only — in `validate_data.py` for validation output and `generate_report.py` for the final "Relatório gerado:" confirmation line.
**Validation:** Centralised in `validate_data.py`; individual modules do not self-validate.
**Authentication:** Not applicable — fully local filesystem project, no external services.

---

*Architecture analysis: 2026-06-22*
