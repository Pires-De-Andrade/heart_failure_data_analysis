# Architecture Research

**Domain:** SHAP explainability integration — sklearn Pipeline + Streamlit app
**Researched:** 2026-06-22
**Confidence:** HIGH (all integration points verified against live code and running environment; SHAP 0.48.0 already installed)

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│  BUILD TIME  (python -m src.train_model)                                │
│                                                                         │
│  dataset/raw/heart.csv                                                  │
│       │                                                                 │
│       ▼                                                                 │
│  load_xy()  →  X_train, X_test, y_train, y_test                        │
│       │                                                                 │
│       ▼                                                                 │
│  pipe.fit(X_train, y_train)                                             │
│    prep  =  ColumnTransformer                                           │
│               num: [SimpleImputer(median) → StandardScaler]            │
│               cat: [OneHotEncoder]                                      │
│    clf   =  LogisticRegression                                          │
│       │                                                                 │
│       ├──► models/logistic_model.joblib          (existing)            │
│       │                                                                 │
│       │   NEW: compute_shap_artifacts()                                 │
│       │        X_train_t = prep.transform(X_train)  [734×20]           │
│       │        masker    = Independent(X_train_t, max_samples=100)      │
│       │        explainer = LinearExplainer(clf, masker)                 │
│       │        sv_train  = explainer(X_train_t)                         │
│       │        sv_train.feature_names = display_names                   │
│       │                                                                 │
│       ├──► output/figures/06_shap_beeswarm.png   (NEW, precomputed)    │
│       └──► output/tables/shap_global.npz         (NEW, precomputed)    │
│                 shap_values  [734×20]                                   │
│                 X_transformed[734×20]  ← background for live explainer  │
│                 expected_value [1]                                      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  RUNTIME  (streamlit run dashboard/app.py)                              │
│                                                                         │
│  @st.cache_resource                                                     │
│  get_model()  →  pipe (logistic_model.joblib)                          │
│                                                                         │
│  @st.cache_resource                                                     │
│  get_shap_explainer(pipe)  →  (explainer, display_names)   NEW         │
│    loads shap_global.npz → X_bg                                         │
│    builds LinearExplainer(clf, Independent(X_bg, max_samples=100))     │
│    builds display_names from prep.get_feature_names_out()              │
│                                                                         │
│  @st.cache_data                                                         │
│  get_shap_global_fig()  →  matplotlib Figure  (beeswarm)   NEW         │
│    loads shap_global.npz → sv_values, X_bg                             │
│    rebuilds Explanation(sv_values, X_bg, display_names)                │
│    renders shap.plots.beeswarm(sv, show=False) → plt.gcf()             │
│                                                                         │
│  section_explainability()                 NEW SECTION                  │
│    st.image(output/figures/06_shap_beeswarm.png)  OR                  │
│    st.pyplot(get_shap_global_fig())                                    │
│                                                                         │
│  section_prediction()                     MODIFIED                     │
│    ... (existing form unchanged) ...                                    │
│    if submitted:                                                        │
│      row_t = prep.transform(row)              (existing)               │
│      proba = model.predict_proba(row_t)       (existing)               │
│      explainer, names = get_shap_explainer(pipe)  NEW                  │
│      sv_local = explainer(row_t)              NEW                      │
│      sv_local.feature_names = names           NEW                      │
│      shap.plots.waterfall(sv_local[0], show=False)  NEW               │
│      st.pyplot(plt.gcf()) ; plt.close('all')  NEW                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Status |
|-----------|----------------|--------|
| `src/train_model.py` | Pipeline fit, evaluation, odds-ratios, model persist | Existing — extend with `compute_shap_artifacts()` |
| `src/config.py` | Paths, labels, constants | Existing — add `SHAP_NPZ_PATH`, `SHAP_BEESWARM_PATH` |
| `models/logistic_model.joblib` | Persisted sklearn Pipeline (prep + clf) | Existing — unchanged |
| `output/figures/06_shap_beeswarm.png` | Precomputed global SHAP beeswarm plot | NEW artifact |
| `output/tables/shap_global.npz` | Background matrix + SHAP values + expected_value | NEW artifact |
| `dashboard/app.py` — `get_shap_explainer()` | Cached explainer construction from background data | NEW cached loader |
| `dashboard/app.py` — `get_shap_global_fig()` | Cached beeswarm Figure rendering | NEW cached renderer |
| `dashboard/app.py` — `section_explainability()` | New dashboard section: global SHAP display | NEW section |
| `dashboard/app.py` — `section_prediction()` | Prediction form + local waterfall after submit | MODIFIED — append waterfall |

---

## Recommended Project Structure

```
heart_failure_data_analysis/
├── src/
│   ├── config.py           # add: SHAP_NPZ_PATH, SHAP_BEESWARM_PATH
│   └── train_model.py      # add: compute_shap_artifacts(), call in main()
├── dashboard/
│   └── app.py              # add: get_shap_explainer(), get_shap_global_fig(),
│                           #      section_explainability(), extend section_prediction()
│                           #      add "Explicabilidade" to sidebar radio
├── models/
│   └── logistic_model.joblib   (unchanged)
├── output/
│   ├── figures/
│   │   └── 06_shap_beeswarm.png   (NEW — precomputed at train time)
│   └── tables/
│       └── shap_global.npz        (NEW — background + global SHAP values)
└── requirements.txt        # add: shap>=0.46
```

### Structure Rationale

- **`src/train_model.py` extended (not split):** SHAP artifacts are deterministic outputs of training, just like odds-ratios. Adding `compute_shap_artifacts()` mirrors the existing `odds_ratios_table()` pattern exactly.
- **`output/tables/shap_global.npz`:** Follows the existing convention of saving all training artifacts to `output/`. The `.npz` compressed format is 28 KB vs. 718 KB for joblib of the Explanation object — negligible I/O at startup.
- **Explainer NOT persisted via joblib:** The `LinearExplainer` object itself is cheap to reconstruct (0.36 ms) from the background matrix. Persisting the background data (`X_transformed` in the npz) is sufficient and smaller.

---

## Architectural Patterns

### Pattern 1: Extract-and-Pass (not wrap) for SHAP on Pipelines

**What:** Extract the `clf` step from the Pipeline and pass ColumnTransformer-transformed data separately to `LinearExplainer`. Do NOT wrap the full Pipeline in `shap.Explainer`.

**When to use:** Always, when the Pipeline contains transformers before a linear model. `shap.Explainer` on a Pipeline calls `predict_proba` as a black box and uses KernelExplainer internally, which is slower and approximate.

**Trade-offs:** Slightly more code; SHAP values are in the transformed (standardized, one-hot) space and must be labeled manually via `feature_names` injection. The payoff is exact linear SHAP (closed-form, not sampling-based) and 0.21 ms per call.

**Concrete extraction (verified against the real pipeline):**
```python
prep = pipe.named_steps["prep"]   # ColumnTransformer
clf  = pipe.named_steps["clf"]    # LogisticRegression

X_train_t = prep.transform(X_train)                         # shape (734, 20)
masker    = shap.maskers.Independent(X_train_t, max_samples=100)
explainer = shap.LinearExplainer(clf, masker=masker)
```

### Pattern 2: Feature Name Recovery via `get_feature_names_out()` + prefix strip

**What:** The ColumnTransformer's `get_feature_names_out()` returns names with transformer prefixes (`num__Age`, `cat__Sex_M`). Strip the prefix, then split on the first `_` anchored to a known categorical variable to recover `("Sex", "M")` → `VAR_LABELS["Sex"] + " = " + CAT_LABELS["Sex"]["M"]`.

**Verified name list (20 features after transform):**

| Raw name | Display name |
|----------|--------------|
| `num__Age` | `Idade (anos)` |
| `num__RestingBP` | `Pressão Arterial em Repouso (mmHg)` |
| `num__Cholesterol` | `Colesterol Sérico (mg/dL)` |
| `num__FastingBS` | `Glicemia de Jejum > 120 mg/dL` |
| `num__MaxHR` | `Frequência Cardíaca Máxima (bpm)` |
| `num__Oldpeak` | `Depressão ST (Oldpeak)` |
| `cat__Sex_F` | `Sexo = Feminino` |
| `cat__Sex_M` | `Sexo = Masculino` |
| `cat__ChestPainType_ASY` | `Tipo de Dor Torácica = Assintomático` |
| `cat__ChestPainType_ATA` | `Tipo de Dor Torácica = Angina Atípica` |
| `cat__ChestPainType_NAP` | `Tipo de Dor Torácica = Dor Não-Anginosa` |
| `cat__ChestPainType_TA` | `Tipo de Dor Torácica = Angina Típica` |
| `cat__RestingECG_LVH` | `ECG em Repouso = Hipertrofia Ventricular Esq.` |
| `cat__RestingECG_Normal` | `ECG em Repouso = Normal` |
| `cat__RestingECG_ST` | `ECG em Repouso = Anormalidade ST-T` |
| `cat__ExerciseAngina_N` | `Angina Induzida por Exercício = Não` |
| `cat__ExerciseAngina_Y` | `Angina Induzida por Exercício = Sim` |
| `cat__ST_Slope_Down` | `Inclinação do Segmento ST = Descendente` |
| `cat__ST_Slope_Flat` | `Inclinação do Segmento ST = Plano` |
| `cat__ST_Slope_Up` | `Inclinação do Segmento ST = Ascendente` |

**Mapping function (uses existing `VAR_LABELS` + `CAT_LABELS` from `src/config.py`):**
```python
def build_display_names(raw_names, var_labels, cat_labels):
    display = []
    for n in raw_names:
        _, rest = n.split("__", 1) if "__" in n else ("", n)
        found = False
        for var in cat_labels:
            if rest.startswith(var + "_"):
                cat_val = rest[len(var) + 1:]
                display.append(
                    f"{var_labels.get(var, var)} = {cat_labels[var].get(cat_val, cat_val)}"
                )
                found = True
                break
        if not found:
            display.append(var_labels.get(rest, rest))
    return display
```

**Feature names must be injected into the `Explanation` object** because `LinearExplainer` sets them to `["Feature 0", "Feature 1", ...]` by default when given a numpy array as input (verified):
```python
sv = explainer(X_transformed)
sv.feature_names = display_names   # mutate in place; affects all plots
```

### Pattern 3: Precompute Global / Compute Live Local

**Decision: global artifacts precomputed in `train_model.py`; local waterfall computed live in dashboard.**

**Rationale (performance measurements):**

| Operation | Time |
|-----------|------|
| `LinearExplainer` construction | 0.36 ms |
| Single-row SHAP (`explainer(row_t)`) | 0.21 ms |
| Full training-set SHAP (734 rows) | 19.2 ms |
| Beeswarm render (`shap.plots.beeswarm`) | 114 ms |
| Waterfall render (`shap.plots.waterfall`) | 68 ms |

Beeswarm over 734 rows: 19 ms compute + 114 ms render = ~133 ms total. This is fast enough to cache once and never recompute. Precomputing at train time (a) makes the dashboard stateless w.r.t. training data, (b) aligns with the existing pattern (`output/figures/*.png` and `output/tables/*.csv` are all train-time artifacts), (c) the beeswarm PNG can simply be loaded with `st.image()`.

Local waterfall: 0.36 ms (explainer rebuild from cached background) + 0.21 ms (SHAP) + 68 ms (render) = ~68 ms net per form submit. Acceptable for interactive use and cannot be precomputed because it depends on user input.

**What to precompute (saved by `compute_shap_artifacts()`):**

```
output/figures/06_shap_beeswarm.png   — beeswarm plot over X_train (max_display=15)
output/tables/shap_global.npz         — compressed numpy archive:
    shap_values   [734, 20]  float64  — sv_train.values
    X_transformed [734, 20]  float64  — sv_train.data (serves as background for live explainer)
    expected_value[1]        float64  — explainer.expected_value
```

**What to compute live (in `section_prediction()` after form submit):**

```
row_t     = prep.transform(row)         — 1×20 numpy array
sv_local  = explainer(row_t)            — Explanation(values=[1,20])
sv_local.feature_names = display_names
shap.plots.waterfall(sv_local[0], show=False)
fig = plt.gcf()
st.pyplot(fig)
plt.close("all")
```

### Pattern 4: `@st.cache_resource` for Explainer, `@st.cache_data` for Global Figure

**What:** Cache the explainer object as a resource (stateful, not serializable), the beeswarm figure as data (pure output, hashable). Both survive re-runs without recomputing.

```python
@st.cache_resource
def get_shap_explainer(_pipe):
    """Loads background from shap_global.npz and builds LinearExplainer.
    
    The leading underscore tells Streamlit not to hash _pipe (it's not
    hashable), so the cache key is effectively per-session.
    """
    data = np.load(SHAP_NPZ_PATH)
    X_bg = data["X_transformed"]
    prep = _pipe.named_steps["prep"]
    clf  = _pipe.named_steps["clf"]
    display_names = build_display_names(
        list(prep.get_feature_names_out()), VAR_LABELS, CAT_LABELS
    )
    masker    = shap.maskers.Independent(X_bg, max_samples=100)
    explainer = shap.LinearExplainer(clf, masker=masker)
    return explainer, display_names


@st.cache_data
def get_shap_global_fig():
    """Renders beeswarm from precomputed npz. Cached indefinitely per session."""
    data = np.load(SHAP_NPZ_PATH)
    sv   = shap.Explanation(
        values=data["shap_values"],
        base_values=float(data["expected_value"][0]),
        data=data["X_transformed"],
        feature_names=display_names,   # computed once at import / via helper
    )
    shap.plots.beeswarm(sv, show=False, max_display=15)
    fig = plt.gcf()
    plt.close("all")
    return fig
```

Note: `st.image(SHAP_BEESWARM_PATH)` is a simpler alternative for the global beeswarm if the section only needs to display the PNG saved at train time.

---

## Data Flow

### Global SHAP Flow (Build Time)

```
dataset/raw/heart.csv
    │
    ▼ load_xy()
X_train (DataFrame, 734×11, raw with NaN for 0-as-missing)
    │
    ▼ prep.transform(X_train)
X_train_t (ndarray, 734×20, scaled + one-hot)
    │
    ├──► masker = shap.maskers.Independent(X_train_t, max_samples=100)
    │
    ▼ shap.LinearExplainer(clf, masker)
explainer
    │
    ▼ explainer(X_train_t)
sv_train  Explanation(values[734,20], data[734,20], base_values=scalar)
    │
    ├──► sv_train.feature_names = display_names
    ├──► shap.plots.beeswarm(sv_train, show=False, max_display=15)
    │         plt.gcf().savefig("output/figures/06_shap_beeswarm.png")
    └──► np.savez_compressed("output/tables/shap_global.npz",
              shap_values=sv_train.values,
              X_transformed=sv_train.data,
              expected_value=[explainer.expected_value])
```

### Local SHAP Flow (Runtime, on form submit)

```
User form inputs (section_prediction)
    │
    ▼ pd.DataFrame([{...}])[MODEL_FEATURES]
row  (DataFrame, 1×11, with np.nan for zeros flagged as missing)
    │
    ▼ prep.transform(row)        ← existing transform, unchanged
row_t  (ndarray, 1×20)
    │
    ├──► existing: model.predict_proba(row_t) → proba, pred class
    │
    │   NEW:
    ▼ get_shap_explainer(pipe)   ← @st.cache_resource, runs once
(explainer, display_names)
    │
    ▼ explainer(row_t)
sv_local  Explanation(values[1,20], base_values=scalar)
    │
    ▼ sv_local.feature_names = display_names
    │
    ▼ shap.plots.waterfall(sv_local[0], show=False)
    │
    ▼ plt.gcf()  →  st.pyplot(fig)  →  plt.close("all")
waterfall rendered in dashboard below prediction result
```

### Key Data Flows

1. **`X_transformed` as shared background:** The same `X_train_t` numpy array is both the SHAP background for the masker and the `data` attribute of `sv_train`. Persisting it in the npz means the live dashboard never needs access to `heart.csv` for SHAP — only for the existing descriptive sections.

2. **`expected_value` semantics:** `LinearExplainer(clf, masker).expected_value` returns the mean log-odds over the background (0.247 for X_train background, verified). SHAP values sum to `decision_function(x) - expected_value` in log-odds space. Verified: `sv.values.sum() + expected_value == clf.decision_function(row_t)[0]` to float64 precision.

3. **`plt.gcf()` pattern for both plots:** `shap.plots.beeswarm()` and `shap.plots.waterfall()` both accept `show=False` and create a matplotlib figure internally. `plt.gcf()` retrieves it. `st.pyplot(fig)` renders it. `plt.close("all")` prevents figure accumulation. This is the same pattern already used throughout `app.py`.

---

## Scaling Considerations

This is a local academic tool — scaling is not a concern. Notes are provided only to explain why certain architectural choices are appropriate:

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1 user (academic) | Current approach is ideal — precomputed PNG + live waterfall, all in-process |
| N concurrent users | Not applicable: `streamlit run` is single-session local; no changes needed |
| Large dataset | Not applicable: 918 rows; LinearExplainer is O(n*p) at 20ms for 734 rows |

---

## Anti-Patterns

### Anti-Pattern 1: Wrapping the Full Pipeline in `shap.Explainer`

**What people do:** `explainer = shap.Explainer(pipe, X_train)` — wrap the full sklearn Pipeline.

**Why it's wrong:** SHAP cannot introspect a Pipeline; it falls back to KernelExplainer (perturbation-based, approximate, slow: seconds per instance vs. 0.21 ms). It also loses access to the exact linear formula.

**Do this instead:** Extract `prep` and `clf` separately. Pass `clf` to `LinearExplainer` with `prep.transform(X_train)` as the background.

### Anti-Pattern 2: Persisting the `LinearExplainer` Object via `joblib`

**What people do:** `joblib.dump(explainer, "models/shap_explainer.joblib")` to avoid rebuilding.

**Why it's wrong:** The explainer is 718 KB serialized vs. 29 KB for the npz. Rebuilding from the background takes 0.36 ms — cheaper than deserialization. Persisting a SHAP object also introduces version coupling between SHAP versions.

**Do this instead:** Persist only `X_transformed` (the background matrix) and `expected_value` in the npz. Rebuild the explainer on dashboard startup via `@st.cache_resource`.

### Anti-Pattern 3: Calling `plt.show()` inside Streamlit

**What people do:** Add `plt.show()` after `shap.plots.waterfall(sv, show=False)`.

**Why it's wrong:** In Streamlit's execution model, `plt.show()` opens a GUI window (or does nothing in headless environments), not a dashboard element. The figure is captured by `plt.gcf()` and passed to `st.pyplot(fig)`.

**Do this instead:** `shap.plots.beeswarm(sv, show=False)` or `shap.plots.waterfall(sv[0], show=False)` → `fig = plt.gcf()` → `st.pyplot(fig)` → `plt.close("all")`. This mirrors the existing `st.pyplot` calls already in `app.py`.

### Anti-Pattern 4: Using Feature Indices Instead of Display Names in Plots

**What people do:** Call `shap.plots.waterfall(sv_local[0], show=False)` without injecting `feature_names` into the `Explanation`.

**Why it's wrong:** `LinearExplainer` given a numpy array (not a DataFrame) defaults to `["Feature 0", ..., "Feature 19"]`. Verified: `sv.feature_names[:3]` returns `["Feature 0", "Feature 1", "Feature 2"]` without injection.

**Do this instead:** `sv.feature_names = display_names` immediately after creating any `Explanation` object. `display_names` is built once from `prep.get_feature_names_out()` + `VAR_LABELS` + `CAT_LABELS`.

### Anti-Pattern 5: Recomputing Global SHAP at Every Dashboard Load

**What people do:** Run `explainer(X_train_t)` inside a dashboard function without `@st.cache_data`.

**Why it's wrong:** Adds 133 ms to every page interaction. More importantly, the global beeswarm depends only on the trained model and training data — both static. Recomputing it is pure waste.

**Do this instead:** Precompute `06_shap_beeswarm.png` in `train_model.py`. In the dashboard, either `st.image(SHAP_BEESWARM_PATH)` (zero overhead, reads the PNG) or `@st.cache_data` on the render function (computes once, serves from memory).

---

## Integration Points

### New vs. Modified Components

| Component | Change Type | Concrete Integration |
|-----------|-------------|----------------------|
| `src/config.py` | Modified | Add two path constants: `SHAP_NPZ_PATH = OUTPUT_TABLES / "shap_global.npz"` and `SHAP_BEESWARM_PATH = OUTPUT_FIGURES / "06_shap_beeswarm.png"` |
| `src/train_model.py` | Modified | Add `compute_shap_artifacts(pipe, X_train)` function; call after `joblib.dump` in `main()` |
| `dashboard/app.py` | Modified | Add imports (`shap`, `SHAP_NPZ_PATH`, `SHAP_BEESWARM_PATH`); add `build_display_names()`, `get_shap_explainer()`, `get_shap_global_fig()`, `section_explainability()`; extend `section_prediction()` with waterfall block; add `"Explicabilidade"` to sidebar radio |
| `output/figures/06_shap_beeswarm.png` | New artifact | Generated by `compute_shap_artifacts()` at train time |
| `output/tables/shap_global.npz` | New artifact | Generated by `compute_shap_artifacts()` at train time |
| `requirements.txt` | Modified | Add `shap>=0.46` (0.48.0 already installed in `.venv`) |

### Insertion Point: `section_prediction()` Waterfall

The waterfall inserts **after** the existing `st.error` / `st.success` block, inside the `if submitted:` branch. No changes to the form widget layout or the `proba`/`pred` computation above it. Exact insertion:

```
[existing]  st.form("pred_form")  →  proba, pred  →  metrics display  →  error/success
[NEW]       if submitted:
                explainer, names = get_shap_explainer(model)
                row_t = prep.transform(row)           # row already built above
                sv_local = explainer(row_t)
                sv_local.feature_names = names
                st.markdown("---")
                st.subheader("Explicação da Predição (SHAP)")
                shap.plots.waterfall(sv_local[0], show=False)
                st.pyplot(plt.gcf())
                plt.close("all")
```

`prep` must be extracted from `model` in `section_prediction()`:
```python
prep = model.named_steps["prep"]
```

This is the only structural dependency — `model` is already in scope as `get_model()` return value.

### Insertion Point: Sidebar Radio

```python
# existing:
section = st.sidebar.radio(
    "Seção",
    ["Visão Geral", "Qualitativas", "Idade", "Contínuas", "Predição"],
)
# modified:
section = st.sidebar.radio(
    "Seção",
    ["Visão Geral", "Qualitativas", "Idade", "Contínuas", "Predição", "Explicabilidade"],
)
```

Add to the dispatch block:
```python
elif section == "Explicabilidade":
    section_explainability()
```

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `train_model.py` → `output/` | File I/O — npz + PNG | Follows existing pattern for all other artifacts |
| `dashboard/app.py` → `output/tables/shap_global.npz` | `np.load()` inside `@st.cache_resource` | Called once per session; 29 KB file |
| `dashboard/app.py` → `models/logistic_model.joblib` | `joblib.load()` via `get_model()` | Already `@st.cache_resource`, unchanged |
| `section_prediction()` → `get_shap_explainer()` | Function call — passes `model` (the pipe) | Triggered only when form is submitted |
| `section_explainability()` → `get_shap_global_fig()` | Function call — no arguments | Returns cached matplotlib Figure |

---

## Suggested Build Order

Dependencies flow strictly in one direction: config paths → training artifact generation → dashboard consumption.

**Step 1 — `src/config.py`:** Add `SHAP_NPZ_PATH` and `SHAP_BEESWARM_PATH`. No other code depends on this being done last, and everything downstream imports from config.

**Step 2 — `src/train_model.py`:** Add `compute_shap_artifacts(pipe, X_train)` and `build_display_names()` helper. Add call in `main()` after `joblib.dump`. Add `shap` to imports. Run `python -m src.train_model` to regenerate all artifacts including the two new SHAP files.

**Step 3 — `requirements.txt`:** Add `shap>=0.46`. Already installed; this makes it explicit.

**Step 4 — `dashboard/app.py` (global section):** Add `section_explainability()` with `get_shap_global_fig()` and `@st.cache_data` wrapper. Add sidebar entry. Test with `streamlit run dashboard/app.py` — verifies npz loads, beeswarm renders.

**Step 5 — `dashboard/app.py` (local waterfall):** Extend `section_prediction()` with the waterfall block inside `if submitted:`. Add `get_shap_explainer()` with `@st.cache_resource`. Test by submitting the prediction form.

This order ensures each step is independently testable: after Step 2 you can verify artifacts exist; after Step 4 you can verify the global section without touching the prediction form; Step 5 is isolated to the form submit path.

---

## Sources

- SHAP 0.48.0 installed in `.venv` — verified via `shap.__version__`
- SHAP Context7 documentation: `/shap/shap` — LinearExplainer API, beeswarm, waterfall plots
- Live verification against `models/logistic_model.joblib` and `dataset/raw/heart.csv`:
  - `get_feature_names_out()` returns 20 features with `num__`/`cat__` prefixes
  - `LinearExplainer.expected_value` = 0.247 (X_train background), scalar float64
  - SHAP sum + expected_value matches `clf.decision_function()` to float64 precision
  - `plt.gcf()` + `st.pyplot(fig)` pattern works for both beeswarm and waterfall
  - `sv.feature_names` defaults to `["Feature 0", ...]` without injection (requires explicit set)
  - `shap_global.npz` = 28.7 KB compressed; beeswarm PNG = 158 KB

---

*Architecture research for: SHAP integration into sklearn Pipeline + Streamlit (Heart Failure v2.1)*
*Researched: 2026-06-22*
