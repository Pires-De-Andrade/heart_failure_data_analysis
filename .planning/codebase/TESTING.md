# Testing Patterns

**Analysis Date:** 2026-06-22

## Test Framework

**Runner:**
- No formal test framework (pytest, unittest) is installed or configured
- `requirements.txt` lists only runtime dependencies: `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`, `jupyter`, `notebook`
- There is no `pytest.ini`, `setup.cfg`, `pyproject.toml`, `jest.config.*`, or equivalent test config file

**Validation Mechanism:**
- All correctness checking is done through `validate_data.py` at the project root, which functions as the project's single verification script
- Inline `assert` statements inside notebooks serve as cell-level sanity checks

**Run Commands:**
```bash
# Run the validation script (from project root)
python validate_data.py

# Run individual notebooks (opens browser)
jupyter notebook notebooks/01_preprocessing.ipynb
```

## Validation Script — `validate_data.py`

`validate_data.py` is the primary correctness gate for all analysis modules. It is a flat top-level script (not a test suite) that:

1. Imports all four `src/` modules
2. Exercises each public function with real data
3. Asserts known-correct numerical results
4. Prints a section-by-section progress log in Portuguese
5. Exits successfully only if all assertions pass

**Structure:**
```python
"""
Script de validação — verifica que todos os módulos funcionam
e que os cálculos produzem resultados corretos.
"""
import sys
sys.path.insert(0, ".")

from src.config import DATA_RAW, QUAL_VARS, CONT_VARS, AGE_BINS, AGE_LABELS
from src.data_loader import load_raw, load_subsets
from src.frequency_tables import freq_table_qualitative, freq_table_classes, sturges_k
from src.descriptive_stats import descriptive_summary, pearson2_skewness, descriptive_by_group

# Each section prints a numbered header then runs assertions
print("[1] Carga dos dados...")
assert df_full.shape[0] == 918, f"ERRO: df_full tem {df_full.shape[0]} linhas"
```

**Sections validated (8 total):**

| Section | What is checked |
|---------|----------------|
| [1] Carga dos dados | `load_subsets()` returns correct row counts: 918, 746, 917 |
| [2] HeartDisease | Exact value_counts: `HeartDisease=1` == 508, `HeartDisease=0` == 410 |
| [3] Tabelas de frequência qualitativas | For each of 6 `QUAL_VARS`: `fi.sum() == 918` and `fri(%).sum() ≈ 100.0` (tolerance 0.1) |
| [4] Tabela de frequências de Age | `freq_table_classes()` with `AGE_BINS`/`AGE_LABELS`: `fi.sum() == 918` |
| [5] Medidas descritivas de Age | `descriptive_summary()` executes and returns labelled rows; `pearson2_skewness()` produces a float |
| [6] Regra de Sturges | `sturges_k(918)`, `sturges_k(746)`, `sturges_k(917)` print results (no assertion — display only) |
| [7] Descritivas por grupo | `descriptive_by_group(df_full, "Age")` returns without error |
| [8] Pearson 2 para Oldpeak | `pearson2_skewness(df_full["Oldpeak"])` computes and prints sign interpretation |

**Expected terminal output on success:**
```
============================================================
VALIDAÇÃO DO PROJETO
============================================================
[1] Carga dos dados...
  ✓ df_full: 918 linhas
  ✓ df_chol: 746 linhas
  ✓ df_bp:   917 linhas
...
============================================================
TODAS AS VALIDAÇÕES PASSARAM ✓
============================================================
```

## Inline Assertions in Notebooks

Notebooks contain `assert` statements embedded in code cells immediately after computing a result. These are not tests in a test runner — they run only when the cell is executed during a notebook session.

**Pattern:**
```python
# notebooks/01_preprocessing.ipynb, cell after load_subsets()
assert df_full.shape[0] == 918, f"Esperado 918, obtido {df_full.shape[0]}"
assert df_chol.shape[0] == 746, f"Esperado 746, obtido {df_chol.shape[0]}"
assert df_bp.shape[0] == 917, f"Esperado 917, obtido {df_bp.shape[0]}"
print("\n✓ Todas as validações passaram.")
```

```python
# notebooks/04_continuous.ipynb, after each freq_table_classes() call
assert ft["fi"].sum() == n, f"Erro: soma de fi ({ft['fi'].sum()}) ≠ n ({n})"
print(f"\n✓ Soma de fi = {ft['fi'].sum()}")
```

**Where inline asserts appear:**
- `notebooks/01_preprocessing.ipynb` — dataset shape after `load_subsets()`
- `notebooks/04_continuous.ipynb` — frequency table `fi` sum equals `n` for each of 4 continuous variables

## What Is Tested

| Capability | Covered by | File |
|-----------|------------|------|
| CSV loading and row count | `validate_data.py` [1], notebook cell | `validate_data.py`, `notebooks/01_preprocessing.ipynb` |
| Subset filtering (zero-value exclusion) | `validate_data.py` [1] | `validate_data.py` |
| HeartDisease exact counts | `validate_data.py` [2] | `validate_data.py` |
| Qualitative frequency tables (fi sum, fri sum) | `validate_data.py` [3] | `validate_data.py` |
| Age class frequency table (fi sum) | `validate_data.py` [4] | `validate_data.py` |
| Descriptive statistics function execution | `validate_data.py` [5] | `validate_data.py` |
| Pearson 2 skewness computation | `validate_data.py` [5, 8] | `validate_data.py` |
| Continuous variable frequency table fi sums | Notebook asserts | `notebooks/04_continuous.ipynb` |

## What Is NOT Tested

- Plotting functions (`src/plotting.py`) — no visual or output-file assertions
- Report generation (`src/generate_report.py`) — the `.docx` output is not validated programmatically
- `sturges_k()` and `sturges_bins()` numerical values — section [6] in `validate_data.py` prints but does not assert
- `interpret_skewness()` and `interpret_kurtosis()` return values — display only, no assertion
- `descriptive_by_group()` numerical output — section [7] only confirms the function runs
- Error/edge-case branches: `std == 0` guard in `pearson2_skewness()`, `mean == 0` guard in CV, missing-figure fallback in `generate_report.py`
- CSV round-trip: tables saved in `output/tables/` are not re-read and validated by `validate_data.py`

## Mocking

Not applicable. No mocking framework or dependency injection is used. Functions take real `pd.Series` / `pd.DataFrame` objects loaded from `dataset/raw/heart.csv`.

## Fixtures and Factories

No fixture system exists. All validation uses the real dataset `dataset/raw/heart.csv` loaded via `load_subsets()`. Hardcoded expected values in assertions serve as the "expected fixture":

```python
# validate_data.py
assert df_full.shape[0] == 918
assert df_chol.shape[0] == 746
assert df_bp.shape[0] == 917
assert hd[1] == 508
assert hd[0] == 410
assert ft["fi"].sum() == 918
assert abs(ft["fri (%)"].sum() - 100.0) < 0.1
```

## Coverage

**Requirements:** None enforced. No coverage tool configured.

**Estimated coverage by module:**

| Module | Coverage | Notes |
|--------|----------|-------|
| `src/data_loader.py` | High | Both `load_raw()` and `load_subsets()` exercised in section [1] |
| `src/frequency_tables.py` | Medium | `freq_table_qualitative()`, `freq_table_classes()`, `sturges_k()` exercised; `sturges_bins()` and `freq_table_crosstab()` not directly in `validate_data.py` |
| `src/descriptive_stats.py` | Medium | `descriptive_summary()`, `pearson2_skewness()`, `descriptive_by_group()` exercised; `interpret_skewness()`, `interpret_kurtosis()` not asserted |
| `src/plotting.py` | None | Zero coverage in `validate_data.py` |
| `src/generate_report.py` | None | Zero coverage in `validate_data.py` |
| `src/config.py` | Passive | Constants are imported but their values are not individually asserted |

## Adding New Validation

To extend `validate_data.py` with a new check, follow this pattern:

```python
# N. Descriptive label
print(f"\n[N] Descriptive label in Portuguese...")
result = call_the_function(df_full["ColumnName"])
assert result == expected_value, f"ERRO: got {result}"
print(f"  ✓ Confirmation message")
```

All output uses `print()` with `✓` prefix on success lines. The final block must remain:

```python
print(f"\n{'=' * 60}")
print("TODAS AS VALIDAÇÕES PASSARAM ✓")
print(f"{'=' * 60}")
```

---

*Testing analysis: 2026-06-22*
