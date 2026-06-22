# Coding Conventions

**Analysis Date:** 2026-06-22

## Language

All comments, docstrings, variable labels, printed output, and user-facing strings are written in **Brazilian Portuguese**. Code identifiers (function names, variable names, module names) are in **English snake_case**, consistent with Python conventions. Dataset column names (`HeartDisease`, `RestingBP`, etc.) retain their original English casing from the CSV source.

## Naming Patterns

**Files:**
- Module names use lowercase snake_case: `data_loader.py`, `frequency_tables.py`, `descriptive_stats.py`, `plotting.py`, `generate_report.py`
- Notebooks use a numeric prefix followed by a descriptive slug: `01_preprocessing.ipynb`, `02_qualitative.ipynb`, `03_discrete.ipynb`, `04_continuous.ipynb`
- Config is centralized in a single file named `config.py`

**Functions:**
- Public functions: lowercase snake_case — `load_raw()`, `load_subsets()`, `freq_table_qualitative()`, `descriptive_summary()`, `pearson2_skewness()`, `bar_chart_grouped()`
- Private/internal helpers: single leading underscore prefix — `_apply_style()`, `_save()`, `_get_label()`, `_shade_cell()`, `_set_repeat_header()`, `_merge_desc()`
- Helper functions that compute a sub-value for a larger function use the pattern `<entity>_<action>` — `sturges_k()`, `sturges_bins()`

**Variables:**
- Local variables: lowercase snake_case — `df_full`, `df_chol`, `df_bp`, `hd_counts`, `as_pearson2`, `kurt_val`, `tick_labels`
- Loop iteration variables are short and contextual: `var`, `val`, `grp_val`, `ri`, `ci`, `bar`
- DataFrame subsets follow the pattern `df_<suffix>` where suffix describes the filter: `df_chol`, `df_bp`, `df_full`

**Constants (in `src/config.py`):**
- SCREAMING_SNAKE_CASE for all module-level constants: `DATA_RAW`, `OUTPUT_FIGURES`, `TARGET`, `QUAL_VARS`, `DISC_VAR`, `CONT_VARS`, `AGE_BINS`, `AGE_LABELS`, `COLOR_HEALTHY`, `COLOR_DISEASE`, `PALETTE_HD`, `FIGSIZE_SINGLE`, `DPI`, `MPL_STYLE`
- Dict constants use descriptive names with a category prefix: `VAR_LABELS`, `CAT_LABELS`, `PALETTE_HD`, `PALETTE_QUAL`

**Types (type hints):**
- All public `src/` functions carry type annotations on parameters and return values
- Union types use PEP 604 `X | Y` syntax (Python 3.10+): `bins: list | np.ndarray | None`, `k: int | None`
- Generic containers use built-in lowercase generics: `dict[str, pd.DataFrame]`, `list[str]`
- Return types are always annotated: `-> pd.DataFrame`, `-> float`, `-> int`, `-> dict[str, pd.DataFrame]`, `-> tuple`
- `tuple` return type is used unparameterized for `(fig, ax)` pairs: `-> tuple`

## Module Docstrings

Every `src/*.py` module opens with a triple-quoted docstring that includes:
1. A one-line description after the filename: `data_loader.py — Carga e limpeza do dataset Heart Disease.`
2. A `Funções:` block listing public functions with their signatures and a one-line Portuguese description

Example pattern (`src/data_loader.py`):
```python
"""
data_loader.py — Carga e limpeza do dataset Heart Disease.

Funções:
    load_raw()     → DataFrame com 918 linhas (dados brutos)
    load_subsets() → dict com df_full, df_chol, df_bp
"""
```

## Function Docstrings

- Public functions have Portuguese prose docstrings
- Docstrings describe what the function returns, the column names produced, and any methodological decisions
- Parameters that have non-obvious behaviour are documented with a `Parâmetros` block using NumPy-style headings:

```python
"""
Parâmetros
----------
series : pd.Series
    Série numérica com valores individuais (não agrupados).
name : str
    Nome da variável (para título).
"""
```
(`src/descriptive_stats.py`, `descriptive_summary()`)

- Private helpers (`_apply_style`, `_save`, `_get_label`) use a single-line Portuguese docstring.
- Internal computation choices that must NOT change are highlighted in the docstring: `# Verificação interna — scipy.stats.skew (NÃO reportado)` appears in `src/descriptive_stats.py` and all four notebooks.

## Import Organization

**Order within every file:**
1. Standard library (`sys`, `pathlib`)
2. Third-party data/numeric (`numpy`, `pandas`, `scipy`)
3. Third-party visualization (`matplotlib`, `seaborn`)
4. Internal package imports (relative `.` imports for `src/` modules)

**Relative imports** are used exclusively inside `src/`: `from .config import DATA_RAW`. Notebooks and `validate_data.py` use absolute `from src.<module> import ...` after manually inserting `PROJECT_ROOT` into `sys.path`.

**Selective imports** are preferred over wildcard: `from src.config import DATA_RAW, QUAL_VARS, CONT_VARS, AGE_BINS, AGE_LABELS`. Never `import *`.

**Lazy imports inside functions** appear in `src/plotting.py` only where a dependency is optional:
```python
from .frequency_tables import sturges_bins  # inside histogram()
from scipy.stats import gaussian_kde        # inside histogram()
```

## Configuration Pattern

All project-wide settings live in `src/config.py`. No magic numbers or hard-coded paths in other modules. All paths are `pathlib.Path` objects derived from `__file__`:

```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW     = PROJECT_ROOT / "dataset" / "raw" / "heart.csv"
OUTPUT_FIGURES = PROJECT_ROOT / "output" / "figures"
OUTPUT_TABLES  = PROJECT_ROOT / "output" / "tables"
```

Notebooks resolve `PROJECT_ROOT` from `Path.cwd().parent` and insert it into `sys.path` at the top of cell 2 in every notebook.

## Inline Comments

- Section dividers use `# ---...---` (70 dashes) to group logical blocks inside `config.py` and `generate_report.py`
- Section headers inside `plotting.py` use `# ===...===` (73 `=`) with a label
- Inline comments explain non-obvious domain decisions in Portuguese: `# Cholesterol == 0 → dado ausente (172 linhas)`
- Commented-out code that must stay for traceability is annotated: `# Verificação interna — scipy.stats.skew (NÃO reportar)`

## Error Handling

No formal exception handling framework is used. Errors surface as:
- `assert` statements for domain invariants in notebooks and `validate_data.py`: `assert df_full.shape[0] == 918`
- Defensive guards for mathematical edge cases: `if std == 0: return 0.0` (`src/descriptive_stats.py`), `if mean != 0` for CV
- `try/except (ValueError, TypeError)` only in the report formatter `fmt_num()` (`src/generate_report.py`) to handle non-numeric cell values
- Missing figures fall back gracefully: `doc.add_paragraph(f"[Figura ausente: {filename}]")` (`src/generate_report.py`, `add_figure()`)

## Output Conventions

**Figures:** saved as `<NN>_<type>_<VarName>.png` at 300 dpi via `_save()` in `src/plotting.py`. All plotting functions return `(fig, ax)` to allow further customization in notebooks after calling `plt.show()`.

**Tables:** saved as `<type>_<VarName>.csv` via `.to_csv()` calls directly in notebook cells. CSVs are UTF-8 encoded. When reading back in `generate_report.py`, the leading unnamed index column is dropped if present.

**Numbers:** The report formatter `fmt_num()` in `src/generate_report.py` converts floats to Brazilian decimal notation (comma as decimal separator, period as thousands separator).

## Notebook Conventions

- Each notebook begins with a markdown cell (`# NN — Title`) describing the analysis scope
- Imports and `sys.path` setup are always in the first code cell
- Every major analysis step is preceded by a `## N.M Title` markdown heading
- Assertions follow `ft.to_csv()` saves to confirm table integrity: `assert ft["fi"].sum() == n`
- `plt.show()` is called after every plot to flush the inline display

---

*Convention analysis: 2026-06-22*
