# Stack Research

**Domain:** SHAP explainability layer on top of scikit-learn logistic Pipeline + Streamlit dashboard
**Researched:** 2026-06-22
**Confidence:** HIGH

---

## Context: What Already Exists (Do Not Re-Research)

| Package | Current pin in requirements.txt | Installed (Python 3.11.9) |
|---------|----------------------------------|---------------------------|
| scikit-learn | `>=1.3` | Used — Pipeline, ColumnTransformer, LogisticRegression |
| matplotlib | `>=3.7` | Used — `st.pyplot`, all figures |
| streamlit | `>=1.30` | Used — dashboard, `st.pyplot`, `st.cache_resource` |
| numpy | `>=1.24` | Used throughout |
| pandas | `>=2.0` | Used throughout |
| joblib | `>=1.3` | Persists and loads the Pipeline |

The existing pipeline is a **two-step scikit-learn Pipeline**: `prep` (ColumnTransformer with median impute + StandardScaler for numerics, OneHotEncoder for categoricals) and `clf` (LogisticRegression). It is persisted at `models/logistic_model.joblib`.

---

## Recommended Stack — Additions Only

### Core Addition

| Technology | Pin for requirements.txt | Purpose | Why Recommended |
|------------|--------------------------|---------|-----------------|
| shap | `>=0.46,<0.50` | SHAP values for logistic Pipeline: global beeswarm + local waterfall | 0.46 introduced NumPy 2 support; upper bound `<0.50` keeps Python 3.9/3.10/3.11 compatibility (0.50 dropped 3.9/3.10). 0.46.0 and 0.47.x both require Python >=3.9 and have no pinned numpy upper bound in their core deps. The project runs Python 3.11.9, so any 0.46–0.49.x works. |

No other new packages are needed.

### Supporting Libraries — NOT Needed

| Library | Verdict | Reason |
|---------|---------|--------|
| streamlit-shap | Do NOT add | Last release March 2022 (v1.0.2), unmaintained. Its only purpose was wrapping interactive JS force-plots; beeswarm and waterfall are pure matplotlib. Its colorbar note ("downgrade matplotlib to 3.4.3") actively conflicts with the project's `matplotlib>=3.7` pin. |
| matplotlib (extra) | Already present | `shap[plots]` extra lists matplotlib as optional; it is already installed via the project's own pin. |

---

## Integration Pattern

### Why LinearExplainer (not KernelExplainer or Explainer auto-detect)

`shap.LinearExplainer` computes **exact** Shapley values for linear models using the closed-form `coef[i] * (x[i] - E[x[i]])`. It is fast (no sampling), deterministic (no random seed needed), and appropriate for logistic regression. KernelExplainer is model-agnostic but slow (sampling-based, O(features^2) queries); it is not needed here.

### Pipeline Extraction Pattern

`LinearExplainer` must receive the **trained linear model object** (not the full Pipeline), and the **preprocessed training data** (not raw X). The ColumnTransformer must be applied separately.

```python
import shap
import matplotlib.pyplot as plt

# Extract components from the loaded Pipeline
preprocessor = pipe.named_steps["prep"]       # ColumnTransformer
clf           = pipe.named_steps["clf"]        # LogisticRegression

# Preprocessed training background (used to anchor SHAP base values)
X_train_transformed = preprocessor.transform(X_train)  # numpy array
feature_names = list(preprocessor.get_feature_names_out())  # after one-hot

# Build explainer once (cache with @st.cache_resource in the dashboard)
masker    = shap.maskers.Independent(X_train_transformed)
explainer = shap.LinearExplainer(clf, masker=masker)

# Global SHAP values (all training or test rows)
shap_values_global = explainer(X_train_transformed)
shap_values_global.feature_names = feature_names  # attach readable names

# Local SHAP values (one patient)
x_single = preprocessor.transform(patient_df)   # shape (1, n_features)
shap_values_local = explainer(x_single)
shap_values_local.feature_names = feature_names
```

Feature names come from `preprocessor.get_feature_names_out()`, which is available in scikit-learn >= 1.0 on ColumnTransformer and returns strings like `num__Age`, `cat__ChestPainType_ATA`. These should be cleaned/renamed to human-readable labels before setting on the Explanation object.

### Rendering in Streamlit with st.pyplot

Both `shap.plots.beeswarm` and `shap.plots.waterfall` render via matplotlib and accept `show=False` to suppress the automatic `plt.show()` call. This is the documented way to capture the figure for `st.pyplot`.

```python
# Global beeswarm
fig_beeswarm, ax = plt.subplots()
shap.plots.beeswarm(shap_values_global, show=False)
st.pyplot(plt.gcf(), clear_figure=True)
plt.close("all")

# Local waterfall (single patient)
fig_waterfall, ax = plt.subplots()
shap.plots.waterfall(shap_values_local[0], show=False)
st.pyplot(plt.gcf(), clear_figure=True)
plt.close("all")
```

`plt.gcf()` retrieves the figure SHAP created internally. `clear_figure=True` resets global pyplot state after Streamlit renders it, preventing figure bleed between re-runs. `plt.close("all")` is belt-and-suspenders cleanup.

**Do NOT rely on `st.pyplot()` with no argument** — that relies on the global pyplot state and is deprecated in Streamlit (marked for removal).

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| `shap.LinearExplainer` | `shap.KernelExplainer` | Sampling-based, slow on 918 rows with 11+ features (after one-hot expansion), non-deterministic without seed; LinearExplainer gives exact values in milliseconds |
| `shap.LinearExplainer` | `shap.Explainer` (auto-detect) | Auto-detect often falls back to Permutation or Kernel explainer for Pipeline objects; extracting clf explicitly and using LinearExplainer is explicit and faster |
| `st.pyplot(fig)` | `streamlit-shap` | Unmaintained since 2022; designed for interactive JS force-plots, not beeswarm/waterfall; introduces a conflicting matplotlib pin |
| `shap>=0.46,<0.50` | `shap>=0.50` | 0.50+ requires Python 3.11+. The project runs 3.11.9 so 0.50+ would technically work, BUT 0.50 also raises minimum dependency versions per SPEC 0 (including numpy>=2). The project pins `numpy>=1.24` which allows 1.x. Staying on 0.46–0.49 avoids any risk from SPEC 0 version bumps. |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `streamlit-shap` | Last release 2022, not maintained, colorbar warning conflicts with `matplotlib>=3.7` | `st.pyplot` with `show=False` and `plt.gcf()` — fully sufficient for beeswarm/waterfall |
| `shap>=0.50` | Requires Python 3.11+; its SPEC 0 minimum dependency bump may force `numpy>=2` which can break existing notebooks in the project | Pin `<0.50` until the full project upgrades its numpy pin |
| `lime` | Different explainability paradigm (local linear approximation, less stable than SHAP), heavier install, zero synergy with existing odds-ratio analysis | SHAP LinearExplainer is already the right level of interpretability |
| Any tree-based or neural XAI package (captum, alibi) | Project is a logistic regression; all those packages add large install overhead for non-applicable model types | Only SHAP is needed |

---

## Version Compatibility Matrix

| Package | Current Pin | SHAP 0.46.x constraint | Conflict? |
|---------|------------|----------------------|-----------|
| numpy | `>=1.24` | No upper bound in core deps (0.46 added numpy 2 support) | None |
| matplotlib | `>=3.7` | Optional dep under `[plots]` extra; no version pin | None |
| scikit-learn | `>=1.3` | No version pin in core deps | None |
| streamlit | `>=1.30` | No dependency on streamlit at all | None |
| Python | 3.11.9 installed | shap 0.46–0.49: `>=3.9`; shap 0.50+: `>=3.11` | None with 0.46–0.49 |
| numba | Not currently pinned | shap 0.47: `numba>=0.54` (core dep, pulled in automatically) | Potential: see Pitfalls |

---

## Installation — Exact Change to requirements.txt

Add one line:

```
shap>=0.46,<0.50
```

Full updated requirements.txt:

```
pandas>=2.0
numpy>=1.24
matplotlib>=3.7
seaborn>=0.13
scipy>=1.11
jupyter>=1.0
notebook>=7.0
scikit-learn>=1.3
joblib>=1.3
streamlit>=1.30
shap>=0.46,<0.50
```

---

## Pitfalls — Specific to This Addition

### 1. numba is a mandatory transitive dependency of shap (not optional)
SHAP 0.46–0.47 pull in `numba` (with `>=0.54` pin in 0.47) as a **core** requirement. numba in turn requires `llvmlite` and takes ~100–200 MB. Installation may be slow or fail on restricted academic networks with binary package size limits. Mitigation: install on a reliable connection; use a pre-built wheel (pip default). Do not try to exclude numba — it is used in SHAP internals (fast computation utilities) and is not optional.

### 2. shap.plots.beeswarm creates its own internal figure — do not pre-create a fig
The pattern `fig, ax = plt.subplots()` followed by `shap.plots.beeswarm(...)` does NOT use the pre-created fig; beeswarm creates its own figure internally. Use `shap.plots.beeswarm(shap_values, show=False)` then `plt.gcf()` to capture what SHAP created. Pre-creating a figure is wasteful and confusing. Same applies to waterfall.

### 3. Feature names after ColumnTransformer are prefixed
`preprocessor.get_feature_names_out()` returns names like `num__Age`, `cat__Sex_M`, `cat__ChestPainType_ATA`. These must be stripped/renamed before being set as `shap_values.feature_names` or SHAP plots will show the internal prefixed names. Use `.replace("num__", "").replace("cat__", "")` or a config-driven mapping.

### 4. SHAP Explanation object vs. old shap_values array
SHAP >= 0.40 introduced the `Explanation` object returned by `explainer(X)`. The old API `explainer.shap_values(X)` returns a raw numpy array. For `shap.plots.waterfall` and `shap.plots.beeswarm` the **new Explanation API** (`explainer(X)`) is required. Do not use the old `shap_values()` call for these plot types.

### 5. Binary classification — SHAP returns values for class 1 only via LinearExplainer
`shap.LinearExplainer` for logistic regression returns a single set of SHAP values corresponding to log-odds for class 1 (HeartDisease = 1). This matches the project goal (explain P(HeartDisease=1)) and requires no extra handling. Beeswarm and waterfall interpret these correctly out of the box.

### 6. matplotlib backend in Streamlit
Streamlit sets matplotlib to a non-interactive backend (`Agg`). SHAP plots render using `plt.gca()` / `plt.gcf()`, which works correctly with Agg. No backend override is needed. Do not call `plt.show()` inside Streamlit; always use `st.pyplot(fig)`.

---

## Sources

- PyPI shap 0.46.0 JSON metadata (`/pypi/shap/0.46.0/json`) — requires_python `>=3.9`, numpy/matplotlib no upper bound, numba in core deps — HIGH confidence
- PyPI shap 0.47.0 JSON metadata — `numba>=0.54` confirmed — HIGH confidence
- SHAP release notes (`shap.readthedocs.io/en/latest/release_notes.html`) — v0.46 added numpy 2 support; v0.50 dropped Python 3.9/3.10 — HIGH confidence
- SHAP docs: `shap.plots.waterfall`, `shap.plots.beeswarm` (`shap.readthedocs.io`) — `show=False` returns via `plt.gca()` — HIGH confidence
- SHAP docs: `shap.LinearExplainer` (`shap.readthedocs.io`) — masker pattern for logistic regression — HIGH confidence
- Streamlit docs: `st.pyplot` (`docs.streamlit.io`) — `fig=None` deprecated; `clear_figure=True` recommended — HIGH confidence
- PyPI streamlit-shap 1.0.2 — last release March 2022, unmaintained, matplotlib<=3.4.3 conflict — HIGH confidence

---
*Stack research for: SHAP explainability on scikit-learn logistic Pipeline + Streamlit*
*Researched: 2026-06-22*
