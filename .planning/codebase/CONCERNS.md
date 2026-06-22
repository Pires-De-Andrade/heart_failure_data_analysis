# Codebase Concerns

**Analysis Date:** 2026-06-22

---

## Tech Debt

**Missing dependency in `requirements.txt` — `python-docx`:**
- Issue: `src/generate_report.py` imports `from docx import Document` and six sub-modules from `python-docx`, but `python-docx` is absent from `requirements.txt`. Any fresh environment install will fail at runtime when `src/generate_report.py` is executed.
- Files: `src/generate_report.py`, `requirements.txt`
- Impact: `python -m src.generate_report` crashes with `ModuleNotFoundError: No module named 'docx'` on a clean install.
- Fix approach: Add `python-docx>=1.1` to `requirements.txt`.

**Loose version pins in `requirements.txt`:**
- Issue: All seven packages use `>=` minimum-version bounds with no upper cap or lock file (`requirements.lock`, `pip freeze` output, or `conda.yml` is absent). There is no `pyproject.toml`, `setup.cfg`, or `environment.yml` either.
- Files: `requirements.txt`
- Impact: A collaborator installing six months later may receive breaking changes from a major version bump (e.g., pandas 3.x, seaborn 0.14). Statistical output values could shift silently across versions.
- Fix approach: Pin exact versions with `==` or generate a `requirements-lock.txt` via `pip freeze > requirements-lock.txt` after validating results. Alternatively, add a `conda`/`virtualenv` snapshot.

**`validate_data.py` CWD assumption:**
- Issue: `validate_data.py` line 6 inserts `"."` (the current working directory) into `sys.path`. The script must be invoked from the repo root; running it from any other directory silently imports the wrong `src/` package or raises `ModuleNotFoundError`.
- Files: `validate_data.py` (line 6)
- Impact: Misleading failures for collaborators who `cd` into `src/` before running the script.
- Fix approach: Replace `sys.path.insert(0, ".")` with `sys.path.insert(0, str(Path(__file__).resolve().parent))` using `from pathlib import Path`.

**`src/generate_report.py` is untracked:**
- Issue: The file exists on disk and its compiled bytecode (`src/__pycache__/generate_report.cpython-311.pyc`) is present, but `git status` reports `src/generate_report.py` as an untracked file. It is the script that produces `RELATORIO.docx` (2.1 MB, committed). Any collaborator cloning the repo cannot regenerate the `.docx` without first noticing the file is missing.
- Files: `src/generate_report.py`
- Impact: Breaks reproducibility of `RELATORIO.docx`; the generation pipeline cannot be re-run from a fresh clone.
- Fix approach: `git add src/generate_report.py` and commit it.

---

## Known Bugs

**`_merge_desc` silently produces `None` values for mismatched measure labels:**
- Symptoms: When `dgg` (per-group descriptive CSV) does not contain a measure label that exists in `dg` (global descriptive CSV), the `except (IndexError, KeyError)` block sets both `sem` and `com` to `None`. `fmt_num(None)` then returns `"—"` without any log or warning.
- Files: `src/generate_report.py` lines 619–628
- Trigger: If the CSVs in `output/tables/` were generated with a different measure set (e.g., after changing `descriptive_stats.py`), silent `—` values appear in the final report tables.
- Workaround: Inspect the generated `.docx` manually for `—` placeholders in numeric columns.

**Pie chart in `notebooks/01_preprocessing.ipynb` bypasses `plotting.py`:**
- Symptoms: The prevalence chart (`00_prevalencia_hd.png`) is generated inline in the notebook using a direct `fig.savefig(PROJECT_ROOT / "output" / "figures" / "00_prevalencia_hd.png", ...)` call rather than going through `plotting._save()`. If `DPI` or style constants change in `src/config.py`, this chart will not inherit the change.
- Files: `notebooks/01_preprocessing.ipynb` (cell 15)
- Trigger: Any update to `MPL_STYLE` or `DPI` in `src/config.py`.
- Workaround: None; the chart must be manually regenerated from the notebook.

---

## Security Considerations

**No secrets present — low risk project:**
- Risk: This is a self-contained academic analysis with no API keys, credentials, or PII beyond the publicly available Kaggle dataset.
- Files: `dataset/raw/heart.csv`
- Current mitigation: The dataset is public (Kaggle: fedesoriano/heart-failure-prediction). No `.env` file exists. No cloud or external service credentials are used.
- Recommendations: No immediate action required. If the project is ever extended with external API calls, add `.env` to `.gitignore` before adding any secret.

---

## Performance Bottlenecks

**KDE density curve recomputed on every plot call:**
- Problem: `src/plotting.py` `histogram()` computes `gaussian_kde` on each invocation (line 183–186) with no caching. For large datasets this adds latency on every notebook re-run.
- Files: `src/plotting.py` lines 182–187
- Cause: The KDE object is instantiated inside the function with no memoization.
- Improvement path: Acceptable at n=918; becomes relevant only if the dataset grows to tens of thousands of rows. No immediate action required.

---

## Fragile Areas

**Committed generated outputs (`output/figures/`, `output/tables/`, `RELATORIO.docx`, `tables_dump.txt`):**
- Files: `output/figures/*.png` (19 PNG files, ~2.6 MB total on disk), `output/tables/*.csv` (22 CSV files), `RELATORIO.docx` (2.1 MB), `tables_dump.txt` (14 KB), `roteiro_trabalho.pdf` (153 KB)
- Why fragile: Every time a notebook is re-run, every PNG and CSV will differ in binary content (matplotlib renders vary by library version, OS font rendering). This will show as large diffs of binary files in `git diff`. The `.docx` is a binary artifact; it will regenerate differently across machines (e.g., different `python-docx` patch versions). Committing these artifacts bloats the repo and makes diffs meaningless.
- Safe modification: Re-run all four notebooks in order (01 → 02 → 03 → 04), then `python -m src.generate_report`. If outputs should stay committed, regenerate them all at once and commit in a single "regenerate outputs" commit.
- Test coverage: None.

**Committed compiled bytecode (.pyc) already on disk:**
- Files: `src/__pycache__/__init__.cpython-311.pyc`, `src/__pycache__/generate_report.cpython-311.pyc`
- Why fragile: `.gitignore` correctly lists `__pycache__/` and `*.pyc`, so these are not currently tracked in git (confirmed via `git ls-files --cached src/__pycache__/` returning empty). However, they are present on disk and were previously compiled from `generate_report.py` — which is itself untracked. If `generate_report.py` is later modified and committed, the stale `.pyc` file could cause confusing import behaviour on Windows where Python sometimes prefers the cached bytecode.
- Safe modification: Running `git clean -fdx src/__pycache__/` will remove the `.pyc` files safely. They are regenerated automatically by Python on next import.

**Old dataset blob permanently in git history:**
- Files: `dataset/raw/data.csv` (Wisconsin Breast Cancer dataset, 569 rows, ~124 KB) is stored as an orphaned blob in git history (`git rev-list --objects --all` commit `672b74c` and `09f7802`).
- Why fragile: The blob is a completely different dataset (breast cancer, not heart failure) that was replaced early in the project. It inflates the pack size and can cause confusion when reviewing history. It cannot be excluded via `.gitignore` (it is already removed from the working tree).
- Safe modification: Use `git filter-repo --path dataset/raw/data.csv --invert-paths` to purge it, then force-push. Only worthwhile if repo size becomes a concern; current total pack is 2.09 MiB which is manageable.

**Notebook `sys.path` injection assumes execution from within `notebooks/` directory:**
- Files: `notebooks/01_preprocessing.ipynb` (cell 2), `notebooks/02_qualitative.ipynb` (cell 1), `notebooks/03_discrete.ipynb` (cell 1), `notebooks/04_continuous.ipynb` (cell 1)
- Why fragile: Each notebook does `PROJECT_ROOT = Path.cwd().parent` which only works when the notebook's CWD is `notebooks/`. Running a notebook from VS Code's "Run All" with CWD set to the repo root will resolve `PROJECT_ROOT` as the parent of the repo root, making all `src/` imports and file paths fail.
- Safe modification: Replace `Path.cwd().parent` with `Path(__file__).resolve().parent.parent` or use `src/config.py`'s `PROJECT_ROOT` constant, which already uses `Path(__file__).resolve()` and is always correct regardless of CWD.

---

## Scaling Limits

**Hardcoded `TOTAL_N = 918` in `src/config.py`:**
- Current capacity: The constant `TOTAL_N = 918` (line 22) is set at the module level and used for narrative text in `generate_report.py`. It is not derived from the actual dataset at load time.
- Limit: If `dataset/raw/heart.csv` is replaced with a different version (more or fewer rows), `TOTAL_N` will silently report the wrong count in the generated report.
- Scaling path: Derive at runtime: `TOTAL_N = len(load_raw())` or validate it in `load_subsets()` with an assertion.

---

## Dependencies at Risk

**`python-docx` undeclared:**
- Risk: Completely absent from `requirements.txt` yet required by `src/generate_report.py`.
- Impact: `ModuleNotFoundError` on fresh install; `RELATORIO.docx` cannot be regenerated.
- Migration plan: `pip install python-docx>=1.1` and add to `requirements.txt`.

---

## Missing Critical Features

**No automated test suite:**
- Problem: The only executable validation is `validate_data.py`, which is an ad-hoc script with `assert` statements and `print` calls rather than a proper test framework. There are no `pytest` or `unittest` test files anywhere in the repository. `pytest.ini`, `setup.cfg [tool:pytest]`, and `pyproject.toml` are all absent.
- Blocks: There is no way to run `pytest` (or any CI check) to confirm that changes to `src/` modules do not break statistical outputs. The `validate_data.py` script also requires CWD to be the repo root (fragile, documented above).
- Files: `validate_data.py` (only validation file present)

**No CI/CD configuration:**
- Problem: No `.github/workflows/`, `Makefile`, or `tox.ini` exists. There is no automated pipeline to re-run `validate_data.py` on push, check requirements, or confirm notebooks execute cleanly.
- Blocks: Silent regressions can be merged without detection.

**No `Makefile` or runner script:**
- Problem: There is no documented way to reproduce the full pipeline end-to-end (run all four notebooks in order, then generate the report). A collaborator must manually run each notebook and then `python -m src.generate_report`.
- Blocks: Onboarding friction; makes reproducibility dependent on undocumented tribal knowledge.

---

## Test Coverage Gaps

**`src/frequency_tables.py` — untested edge cases:**
- What's not tested: `freq_table_classes()` with `bins=None` falls through to `sturges_bins()`. No test covers the case where `series.min() == series.max()` (constant series), which would make `epsilon` the only range. `sturges_bins()` handles this with a fallback but it is untested.
- Files: `src/frequency_tables.py` lines 83–96
- Risk: Silent wrong bin calculation for degenerate input columns.
- Priority: Low (not a concern with the current dataset).

**`src/descriptive_stats.py` — `mode_val` multimodal case:**
- What's not tested: When `series.mode()` returns multiple values (multimodal distribution), `mode_result.iloc[0]` silently returns only the first mode with no indication. No test or comment documents this design decision.
- Files: `src/descriptive_stats.py` line 50
- Risk: Reports a single mode for multimodal distributions without warning; misleading for future variables.
- Priority: Low (current variables are unimodal).

**`src/generate_report.py` — file-not-found fallback untested:**
- What's not tested: `add_figure()` has a graceful fallback (`doc.add_paragraph(f"[Figura ausente: {filename}]")`) when a PNG does not exist (line 127). No test confirms this fallback is exercised correctly and that the output document is still valid when figures are missing.
- Files: `src/generate_report.py` lines 123–136
- Risk: A missing figure produces a malformed document section with no error surfaced to the caller.
- Priority: Medium — especially relevant since outputs are committed separately and could become stale.

**`validate_data.py` — not integrated into any test runner:**
- What's not tested: The script covers only data loading, row counts, and basic frequency totals. It does not validate any computed statistical measures (mean, std, skewness, kurtosis) against expected values, and it is not invoked automatically.
- Files: `validate_data.py`
- Risk: Regressions in `descriptive_stats.py` or `frequency_tables.py` will not be caught.
- Priority: Medium.

---

*Concerns audit: 2026-06-22*
