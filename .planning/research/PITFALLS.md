# Pitfalls Research

**Domain:** SHAP explainability added to sklearn logistic regression Pipeline rendered in Streamlit
**Researched:** 2026-06-22
**Confidence:** HIGH (verified against SHAP official docs, GitHub issues, Streamlit docs, and live codebase inspection)

---

## Critical Pitfalls

### Pitfall 1: Passing the Full Pipeline to LinearExplainer Instead of the Classifier

**What goes wrong:**
`shap.LinearExplainer` accepts a linear sklearn model, not a full `Pipeline`. If you pass `pipe` (the full Pipeline from `logistic_model.joblib`), SHAP either raises an `AttributeError` (no `coef_` on Pipeline), silently falls back to a slow `KernelExplainer` path, or produces values computed in the wrong feature space — because the Pipeline expects raw `MODEL_FEATURES` columns as input, but `LinearExplainer` wants the already-transformed (post-impute / post-onehot / post-scale) feature space.

**Why it happens:**
The persisted artifact `logistic_model.joblib` is the full Pipeline object. It is natural to pass it directly. However, `LinearExplainer` requires a model with `coef_` and `intercept_` attributes, which only the inner `LogisticRegression` step has.

**How to avoid:**
Extract the classifier step explicitly:
```python
pipe = joblib.load(MODEL_PATH)
clf = pipe.named_steps["clf"]          # LogisticRegression with coef_, intercept_
preprocessor = pipe.named_steps["prep"]
X_transformed = preprocessor.transform(X_background)  # already-scaled post-OHE array

masker = shap.maskers.Independent(X_transformed, max_samples=100)
explainer = shap.LinearExplainer(clf, masker=masker)
```
The background data `X_background` must be the raw DataFrame first, transformed by the preprocessor, before being passed to the masker — so SHAP operates in the same space the classifier was trained in.

**Warning signs:**
- `AttributeError: Pipeline object has no attribute 'coef_'` when constructing the explainer
- SHAP values have shapes inconsistent with the 11 original features (because OHE expands categoricals)
- No error but the explainer silently wraps the pipeline's `predict` call — waterfall base_values are probability-space floats like 0.55 (not log-odds near 0), which means a different explainer path was selected

**Phase to address:**
Phase 2.1, Step 1 (explainer construction / `src/shap_explainer.py`). Must be verified with an assertion: `assert hasattr(explainer.model, 'coef_')` before any downstream computation.

---

### Pitfall 2: Explaining in Raw-Feature Space vs. Transformed Space — Sign and Scale Errors

**What goes wrong:**
When you pass raw `X` (pre-transform) to the explainer but give it the isolated `LogisticRegression` classifier (which was trained on scaled, one-hot-encoded data), the SHAP values will be computed for the wrong feature distribution. Signs can flip, magnitudes are off, and the background expected value is wrong because the classifier's weights were fitted on standardized numerics. The relationship `SHAP_i = coef_i * (x_i - mean_i)` breaks down entirely when `x_i` is the raw age 54 but `mean_i` is the post-scaling mean (0.0) and `coef_i` applies to the scaled value.

**Why it happens:**
The pipeline has two transformations before the classifier: (1) median imputation + StandardScaler for numerics, and (2) OneHotEncoder for categoricals. The `LogisticRegression.coef_` values operate in post-OHE, post-scale space. Passing raw data skips both transforms.

**How to avoid:**
Always call `preprocessor.transform(X)` before passing data to the explainer. For the waterfall (local explanation), pass the single patient row through `preprocessor.transform(row)` to get the transformed vector first:
```python
X_transformed_bg  = preprocessor.transform(X_train_sample)   # background
x_transformed_row = preprocessor.transform(patient_row_df)   # single patient
shap_values_local = explainer(x_transformed_row)
```
The SHAP docs explicitly state this for StandardScaler: SHAP values are computed in the space the model was trained in, and univariate transforms (like StandardScaler) do not change Shapley values — but the background data must match that space.

**Warning signs:**
- `shap_values.values` has shape `(1, 11)` instead of `(1, N_transformed_features)` — the 11 raw columns count does not match the expanded OHE feature count (~21 columns after encoding 5 categorical variables)
- `explainer.expected_value` is a large positive or negative number far from typical log-odds range (roughly -1 to +1 for a balanced dataset)
- Beeswarm feature color bars show values like `200.0` for `Cholesterol` (raw) instead of `~0.3` (scaled)

**Phase to address:**
Phase 2.1, Step 1 (explainer construction). Must be validated by: `assert X_transformed.shape[1] == len(preprocessor.get_feature_names_out())`.

---

### Pitfall 3: Feature-Name Mismatch After One-Hot Encoding — Wrong Labels on Plots

**What goes wrong:**
After `preprocessor.transform(X)`, the result is a plain NumPy array with no column names. SHAP will label features as `x0, x1, x2, ...` (or integers) in beeswarm and waterfall plots unless feature names are explicitly attached. This is especially misleading because OHE expands `ChestPainType` (4 values), `ST_Slope` (3), `RestingECG` (3), `Sex` (2), and `ExerciseAngina` (2) — the expanded array has ~21 columns, but without names the plot shows `x6, x7, x8, x9` where it should show `cat__ChestPainType_ASY`, etc.

**Why it happens:**
`LinearExplainer` receives a NumPy array as background data and has no awareness of the ColumnTransformer output names. The `Explanation` object gets `feature_names=None` and falls back to integer indices.

**How to avoid:**
Retrieve names from the fitted preprocessor and attach them to the `Explanation` object:
```python
feature_names = preprocessor.get_feature_names_out().tolist()
# produces: ['num__Age', 'num__RestingBP', ..., 'cat__Sex_F', 'cat__Sex_M', ...]

shap_values = explainer(x_transformed)
shap_values.feature_names = feature_names   # attach before plotting
```
The existing `_feature_names()` helper in `src/train_model.py` already calls `pipe.named_steps["prep"].get_feature_names_out()` — reuse it. For dashboard display, strip the `num__` / `cat__` prefixes with a dict mapping to `VAR_LABELS` for readability.

**Warning signs:**
- Waterfall plot x-axis labels are `x0, x1, x2...`
- Beeswarm y-axis shows integer feature indices
- The top feature in the beeswarm is named `x14` instead of `cat__ST_Slope_Flat`

**Phase to address:**
Phase 2.1, Step 1 (explainer construction) and Step 2 (plot rendering). Feature names must be verified as a unit test: `assert len(feature_names) == X_transformed.shape[1]`.

---

### Pitfall 4: Log-Odds vs. Probability Space Confusion in Waterfall Base Values

**What goes wrong:**
`shap.LinearExplainer` for `LogisticRegression` always returns SHAP values in **log-odds space** — this is correct and intentional, because the logistic model is additive in log-odds, not in probability. However, two failure modes arise:

1. **Displaying raw log-odds to end users**: The waterfall `base_value` will be something like `0.21` (log-odds of the class prevalence ~0.553), not `0.553` (probability). The top of the waterfall shows a final value like `2.1` (log-odds), not `87.7%`. Users see meaningless numbers.

2. **The `link` argument bug in LinearExplainer**: GitHub issue #3767 (confirmed open, targeted at 0.47.0+) shows that passing `link=shap.links.logit` to `LinearExplainer` is silently ignored — values remain in log-odds regardless. Do not rely on `link` to fix the display.

**Why it happens:**
`LogisticRegression` is linear in log-odds space. SHAP's `LinearExplainer` faithfully computes in that additive space. The `link` parameter was intended to transform output to probabilities but was not applied in `LinearExplainer` (unlike `KernelExplainer` where it works).

**How to avoid:**
Convert explicitly using `scipy.special.expit` (the sigmoid) after computing SHAP values:
```python
from scipy.special import expit

base_prob = float(expit(explainer.expected_value))
# For per-feature contributions shown as probability deltas, use:
# shap_values.values stay in log-odds for the waterfall (that's fine for relative magnitude)
# but annotate the waterfall title/axis with "log-odds contribution"

# For the dashboard probability display, show model.predict_proba() output (already computed)
# and pair it with a waterfall showing log-odds contributions — annotate clearly
```
Keep the existing `proba = float(model.predict_proba(row)[0, 1])` result as the primary probability display. The SHAP waterfall supplements it with directional contributions, not an alternative probability.

**Warning signs:**
- Waterfall `base_value` printed with 2 decimals appears as `0.21` or similar, not a `55%` prevalence figure
- User confusion: "The waterfall says the final value is 2.4 but you told me probability is 87%"
- `shap_values[0].base_values` returns a scalar near `0` (log-odds of balanced class) not near `0.5`

**Phase to address:**
Phase 2.1, Step 2 (dashboard rendering). Waterfall plots must include a visible annotation: "valores em escala log-odds; probabilidade prevista = {proba:.1%}".

---

## Integration Gotchas

### Pitfall 5: Streamlit — `force_plot` JS Not Rendering

**What goes wrong:**
`shap.plots.force()` by default generates an interactive HTML/JavaScript visualization. When passed to `st.pyplot()`, it renders as a blank white space because Streamlit's `st.pyplot()` renders matplotlib figures, not HTML blobs.

**Why it happens:**
`force_plot` (the old API) uses `shap.initjs()` + D3.js/SVG HTML output. `st.pyplot` expects a `matplotlib.figure.Figure`. Mixing the two produces nothing visible.

**How to avoid:**
Use `shap.plots.waterfall()` (the new API, always matplotlib) instead of `force_plot` for per-prediction explanations. If `force_plot` is specifically needed, either:
```python
# Option A: waterfall (recommended for this project)
shap.plots.waterfall(shap_values[0], show=False)
fig = plt.gcf()
st.pyplot(fig)
plt.close(fig)

# Option B: force_plot with matplotlib=True
st.pyplot(shap.plots.force(shap_values[0], matplotlib=True, show=False))
```
For this project, `shap.plots.waterfall` is the correct choice — it is matplotlib-native, per-prediction, and matches the academic presentation goal.

**Warning signs:**
- Section renders with no visible content, no error message
- `st.pyplot()` receives a non-Figure object (HTML string) and silently displays nothing
- The prediction form submits successfully but the explanation area stays blank

**Phase to address:**
Phase 2.1, Step 2 (dashboard rendering / `dashboard/app.py`).

---

### Pitfall 6: Matplotlib Figure Not Clearing Between Reruns — Stale Plots

**What goes wrong:**
Streamlit reruns the entire script on each widget interaction. If a matplotlib figure from a previous run is not explicitly closed, it accumulates in the pyplot figure manager. On the next run, `plt.gcf()` may return a stale figure from a prior patient prediction. The waterfall for Patient A persists on screen when Patient B is submitted.

Additionally, `shap.plots.waterfall(sv, show=True)` calls `plt.show()` internally, which in Streamlit's non-interactive backend does nothing but leaves the figure open — causing the stale-figure problem.

**How to avoid:**
Always use `show=False` and manage figures explicitly:
```python
shap.plots.waterfall(shap_values[0], show=False)
fig = plt.gcf()
st.pyplot(fig, clear_figure=True)   # clear_figure=True tells Streamlit to clf() after render
plt.close(fig)                       # belt-and-suspenders: also close explicitly
```
The existing `app.py` already follows this pattern for all other plots (e.g., `section_overview`: `st.pyplot(fig)` then `plt.close(fig)`). The SHAP section must match this exact pattern.

**Warning signs:**
- Running the prediction form twice shows two waterfall plots stacked
- The second prediction's waterfall contains features from the first patient
- Memory usage climbs with each form submission

**Phase to address:**
Phase 2.1, Step 2 (dashboard rendering). Apply the same `plt.close(fig)` discipline already established in the existing sections of `app.py`.

---

## Performance Traps

### Pitfall 7: Recomputing the Explainer on Every Rerun — Slow Predictions

**What goes wrong:**
If `shap.LinearExplainer(clf, masker)` is constructed inside `section_prediction()` (or any function called on each rerun), it is rebuilt from scratch every time the user changes a widget — even a sidebar filter unrelated to predictions. For `LinearExplainer` this takes ~1-2 seconds on 918 rows; for `KernelExplainer` it would be 30-120 seconds.

**Why it happens:**
Streamlit reruns the full script on any widget change. Objects created at the top level or inside sections are not persisted between runs unless wrapped in `@st.cache_resource`.

**How to avoid:**
Cache the explainer alongside the model using `@st.cache_resource`:
```python
@st.cache_resource
def get_explainer():
    pipe = get_model()
    if pipe is None:
        return None, None
    clf = pipe.named_steps["clf"]
    preprocessor = pipe.named_steps["prep"]
    X_raw, _ = load_xy_for_background()    # load training data once
    X_bg = shap.utils.sample(
        preprocessor.transform(X_raw), 100, random_state=42
    )
    masker = shap.maskers.Independent(X_bg)
    return shap.LinearExplainer(clf, masker), preprocessor
```
Note: `@st.cache_resource` (not `@st.cache_data`) is correct here because the explainer is a stateful, non-serializable object — same as the model already cached in `get_model()`.

**Warning signs:**
- Dashboard feels sluggish on every prediction (>1 second delay even before SHAP computation)
- Streamlit spinner appears on simple sidebar filter changes
- Memory usage grows across reruns (new explainer allocated each time)

**Phase to address:**
Phase 2.1, Step 2 (dashboard rendering). Add `get_explainer()` function adjacent to `get_model()`.

---

### Pitfall 8: Running Beeswarm on the Full 918-Row Dataset

**What goes wrong:**
`shap.plots.beeswarm(shap_values_all)` where `shap_values_all` was computed by calling `explainer(X_all_918_rows)` will: (a) be slow to compute on every dashboard load if not cached, and (b) render a cluttered dot cloud because all 918 rows are plotted. Each beeswarm dot is one patient — at 918 points the plot is noisy and slow to render in Streamlit.

**Why it happens:**
The global beeswarm is natural to compute over the full dataset, but 918 unfiltered rows is overkill for a visual summary in an academic dashboard. The computation itself is fast for LinearExplainer (exact, O(n*p)), but the figure generation and rendering is slow.

**How to avoid:**
Precompute SHAP values for the training set once (offline, in `src/shap_explainer.py`) and persist as `output/shap/shap_values_train.npy` + `output/shap/shap_feature_names.json`. Load these in the dashboard with `@st.cache_data`. For the beeswarm, use `max_display=10` (shows top 10 features only) and optionally subsample:
```python
# In src/shap_explainer.py (offline script)
shap_values_all = explainer(X_transformed_train)
np.save("output/shap/shap_values_train.npy", shap_values_all.values)
```
This separates the expensive computation from the interactive dashboard.

**Warning signs:**
- Beeswarm tab takes >3 seconds to load on first render
- Re-rendering beeswarm on every rerun causes sidebar filter changes to stall
- `shap_values.values.shape` is `(918, 21)` computed live in the dashboard

**Phase to address:**
Phase 2.1, Step 1 (offline artefact generation in `src/shap_explainer.py`). Beeswarm artefact generated once, loaded in dashboard.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Compute SHAP values live in dashboard for both global + local | Simpler code, no offline script needed | Slow reruns, memory leaks if not cached; global beeswarm recomputed on every patient form submit | Never — split offline (global) vs live (local) from the start |
| Use `shap.Explainer(pipe, X)` (auto-select) instead of explicit `LinearExplainer` | Avoids manual step extraction | Auto-select may choose `PermutationExplainer` or `KernelExplainer` for a Pipeline, which is 100-1000x slower | Never — explicit `LinearExplainer(clf, masker)` is always correct for this logistic model |
| Display log-odds waterfall values without annotation | Less code | Academic audience reads base_value ~0.2 as 20% probability (wrong — it is log-odds) | Never in a presented dashboard; always annotate units |
| Skip `plt.close(fig)` after `st.pyplot()` | Two fewer lines | Figure accumulates in pyplot manager; memory grows per rerun | Never — one-line fix, zero tradeoff |
| Pin `shap` to a broad version range (e.g., `shap>=0.40`) | Flexible installs | Installs may land on a version with the LinearExplainer `link` bug, or on a numpy 2 incompatible version | Never — pin to `shap>=0.46.0` to ensure numpy 2 support |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| SHAP + sklearn Pipeline | Pass full Pipeline to `LinearExplainer` | Extract `pipe.named_steps["clf"]` for the explainer; use `pipe.named_steps["prep"]` separately for transforms |
| SHAP + ColumnTransformer | Use raw `X` as background data | Call `preprocessor.transform(X_background)` first; feature names via `preprocessor.get_feature_names_out()` |
| SHAP + Streamlit `st.pyplot` | Call `shap.plots.waterfall(sv, show=True)` | Use `show=False`, then `fig = plt.gcf()`, then `st.pyplot(fig, clear_figure=True)`, then `plt.close(fig)` |
| SHAP + Streamlit `force_plot` | Pass HTML object to `st.pyplot` | Use `shap.plots.waterfall` (matplotlib-native) instead, or `force_plot(..., matplotlib=True)` |
| SHAP explainer + Streamlit cache | Create explainer inside section function | Wrap in `@st.cache_resource` at module level, same as `get_model()` |
| SHAP + numpy 2 | Install `shap<0.46.0` with `numpy>=2.0` | Require `shap>=0.46.0` in `requirements.txt` which adds numpy 2 support |

---

## Dependency Pitfalls

### Pitfall 9: SHAP / NumPy 2 / Numba Version Conflicts

**What goes wrong:**
Installing `shap` without a version pin in a Python 3.11 environment with `numpy>=1.24` (as required in this project) can install SHAP versions before 0.46.0. These older versions raise `AttributeError: module 'numpy' has no attribute 'obj2sctype'` when numpy 2.0+ is present. Additionally, SHAP's optional `numba` dependency can conflict: numba 0.60.0 requires `numpy<2.3`, so a triple conflict can emerge between `shap`, `numba`, and `numpy`.

**Why it happens:**
The `requirements.txt` only specifies `numpy>=1.24` — a broad lower bound. pip's resolver may install numpy 2.x and a SHAP version that does not support it.

**How to avoid:**
Pin specifically in `requirements.txt`:
```
shap>=0.46.0
numpy>=1.24,<3.0
```
SHAP 0.46.0 was the first release to add numpy 2 support (confirmed via release notes). Do not add `numba` as a direct dependency — let SHAP pull it in at a compatible version. Verify with `pip check` after install.

**Warning signs:**
- `AttributeError: module 'numpy' has no attribute 'obj2sctype'` on import of shap
- `ImportError` from numba on startup
- `pip check` reports version conflicts after install

**Phase to address:**
Phase 2.1, Step 0 (dependency setup / `requirements.txt` update before any SHAP code is written).

---

### Pitfall 10: Reproducibility — Background Sample Seeding

**What goes wrong:**
If `shap.utils.sample(X_transformed, 100)` is called without `random_state`, the 100 background rows selected will differ between runs. For `LinearExplainer`, only the mean and covariance of the background are used (not the individual rows), so the numerical effect is small — but the explainer's `expected_value` may shift slightly, making the waterfall base_value non-reproducible. This violates the project constraint "seeds fixas" and makes `output/shap/` artefacts non-deterministic.

**Why it happens:**
`shap.utils.sample` changed its sampling mode (with/without replacement) between v0.41 and v0.42, meaning that even with the same `random_state`, results can differ if the environment's SHAP version changes.

**How to avoid:**
Always pass `random_state=RANDOM_STATE` (42, from `src/config.py`):
```python
from src.config import RANDOM_STATE
background = shap.utils.sample(X_transformed, 100, random_state=RANDOM_STATE)
```
Additionally, pin the SHAP version in `requirements.txt` to prevent sampling behavior from silently changing across installs.

**Warning signs:**
- `shap_values_train.npy` differs between two fresh runs of `src/shap_explainer.py`
- The waterfall `base_value` is slightly different across dashboard restarts
- `np.testing.assert_allclose` on saved vs regenerated SHAP values fails

**Phase to address:**
Phase 2.1, Step 1 (offline artefact generation). `RANDOM_STATE` from `src/config.py` must be threaded through all SHAP calls.

---

## "Looks Done But Isn't" Checklist

- [ ] **Explainer receives classifier, not pipeline**: Verify `isinstance(explainer.model, LogisticRegression)` — not a Pipeline or wrapper
- [ ] **Background data is transformed**: `X_background.shape[1]` equals `len(preprocessor.get_feature_names_out())` (~21), not `11` (raw features)
- [ ] **Feature names attached to Explanation**: Waterfall and beeswarm labels show `num__Age`, `cat__ST_Slope_Flat`, etc. — not `x0, x1, x2`
- [ ] **Log-odds annotated**: Waterfall plot includes visible text indicating "escala log-odds" and prediction probability is shown separately from the waterfall
- [ ] **force_plot not used**: Search `app.py` for `force_plot` — should be absent; only `shap.plots.waterfall` used
- [ ] **plt.close(fig) called after st.pyplot**: Every SHAP plot block ends with `plt.close(fig)` — same discipline as existing app sections
- [ ] **Explainer cached**: `get_explainer()` decorated with `@st.cache_resource` — not constructed inside `section_prediction()`
- [ ] **shap>=0.46.0 in requirements.txt**: `pip show shap` version is 0.46.0 or higher
- [ ] **random_state=42 on sample call**: `shap.utils.sample(..., random_state=RANDOM_STATE)` — not left as default
- [ ] **Global SHAP artefact precomputed offline**: `output/shap/shap_values_train.npy` exists and loads in dashboard without triggering re-computation

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1. Full pipeline to LinearExplainer | Phase 2.1 Step 1 (explainer construction) | `assert hasattr(explainer.model, 'coef_')` |
| 2. Raw vs transformed feature space | Phase 2.1 Step 1 (explainer construction) | `assert X_bg.shape[1] == len(preprocessor.get_feature_names_out())` |
| 3. Feature name mismatch after OHE | Phase 2.1 Steps 1+2 (construction + render) | Waterfall labels show named features, not `x0...xN` |
| 4. Log-odds vs probability confusion | Phase 2.1 Step 2 (dashboard rendering) | Waterfall has "log-odds" annotation; probability from `predict_proba` displayed separately |
| 5. force_plot JS not rendering | Phase 2.1 Step 2 (dashboard rendering) | No `force_plot` call in `app.py`; `shap.plots.waterfall` used |
| 6. Matplotlib figure not clearing | Phase 2.1 Step 2 (dashboard rendering) | `plt.close(fig)` after every `st.pyplot(fig)` in SHAP section |
| 7. Explainer recomputed every rerun | Phase 2.1 Step 2 (dashboard caching) | `get_explainer` decorated with `@st.cache_resource` |
| 8. Beeswarm on full 918-row dataset live | Phase 2.1 Step 1 (offline artefact generation) | Beeswarm loaded from `output/shap/` not computed in `app.py` |
| 9. SHAP/numpy 2/numba conflicts | Phase 2.1 Step 0 (requirements.txt) | `pip check` passes; `shap>=0.46.0` pinned |
| 10. Background sample not seeded | Phase 2.1 Step 1 (offline artefact) | `random_state=RANDOM_STATE` in all `shap.utils.sample` calls |

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Wrong explainer target (pipeline vs clf) | LOW | Swap `shap.LinearExplainer(pipe, ...)` for `shap.LinearExplainer(pipe.named_steps["clf"], ...)` — one-line fix |
| Raw vs transformed space | MEDIUM | Add `X_bg = preprocessor.transform(X_raw_bg)` before masker; rerun `src/shap_explainer.py`; regenerate all artefacts |
| Feature names missing | LOW | Add `shap_values.feature_names = feature_names` before every plot call |
| Log-odds display confusion | LOW | Add annotation string to waterfall title; no SHAP logic changes |
| force_plot blank | LOW | Replace `force_plot` with `shap.plots.waterfall`; 3-line change |
| Figure accumulation | LOW | Add `plt.close(fig)` after `st.pyplot(fig)` |
| No explainer cache | LOW | Add `@st.cache_resource` decorator to explainer function |
| numpy/shap version conflict | MEDIUM | Pin `shap>=0.46.0` in `requirements.txt`; `pip install -r requirements.txt --upgrade`; recreate venv if needed |

---

## Sources

- [SHAP LinearExplainer official docs](https://shap.readthedocs.io/en/latest/generated/shap.LinearExplainer.html)
- [Explaining a model that uses standardized features — SHAP docs](https://shap.readthedocs.io/en/latest/example_notebooks/tabular_examples/linear_models/Explaining%20a%20model%20that%20uses%20standardized%20features.html)
- [SHAP waterfall plot docs](https://shap.readthedocs.io/en/latest/example_notebooks/api_examples/plots/waterfall.html)
- [BUG: LinearExplainer ignores "link" argument — GitHub issue #3767](https://github.com/shap/shap/issues/3767)
- [NumPy and Numba dependency issues — GitHub issue #3186](https://github.com/shap/shap/issues/3186)
- [SHAP numpy 2 incompatibility — GitHub issue #3716](https://github.com/shap/shap/issues/3716)
- [BUG: random_state in shap.utils.sample not preserved between versions — GitHub issue #3215](https://github.com/shap/shap/issues/3215)
- [SHAP force_plot on Streamlit — Streamlit community thread](https://discuss.streamlit.io/t/shap-shap-force-plot-on-streamlit/10071)
- [SHAP release notes — numpy 2 support in 0.46.0](https://shap.readthedocs.io/en/latest/release_notes.html)
- [st.pyplot docs — clear_figure parameter](https://docs.streamlit.io/develop/api-reference/charts/st.pyplot)
- [Computing SHAP keeps increasing memory — Streamlit community thread](https://discuss.streamlit.io/t/computing-shap-keeps-increasing-memory-usage-after-every-user-input-change/8778)
- [Streamlit caching overview](https://docs.streamlit.io/develop/concepts/architecture/caching)
- [SHAP utils.sample docs](https://shap.readthedocs.io/en/latest/generated/shap.utils.sample.html)
- Context7 / SHAP library documentation (resolved ID: `/shap/shap`)
- Codebase inspection: `src/train_model.py`, `src/config.py`, `dashboard/app.py` (2026-06-22)

---
*Pitfalls research for: SHAP explainability on logistic sklearn Pipeline in Streamlit*
*Researched: 2026-06-22*
