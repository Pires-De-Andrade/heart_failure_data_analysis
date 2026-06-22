# Feature Research

**Domain:** SHAP model explainability surfaced in a Streamlit dashboard (academic heart-disease prediction project)
**Researched:** 2026-06-22
**Confidence:** HIGH — SHAP library docs verified via Context7, rendering patterns confirmed via community sources

---

## SHAP vs Odds-Ratios: What Each Gives You

The existing `pred_odds_ratios.csv` already ranks all 20 post-encoding features by `|coefficient|` and provides the odds-ratio (e.g., ST_Slope_Up OR=0.27, ChestPainType_ASY OR=3.23). That is **global, model-level, linear** interpretation. SHAP adds three things odds-ratios structurally cannot:

| Dimension | Odds-Ratios (existing) | SHAP (new) |
|-----------|------------------------|------------|
| Scope | Global only — one number per feature for the whole model | Both global (mean |SHAP| over dataset) and local (per patient) |
| Patient-level | Not possible — OR is a population-level weight | Waterfall: exactly why THIS patient scored p=0.87 |
| Direction by patient | Coefficient direction is fixed; does not flip for a patient | SHAP value can be +/- per patient depending on their actual feature value |
| Pipeline awareness | Requires manually mapping coef back through one-hot names | `LinearExplainer` operates on transformed space; feature names map directly |
| Visual encoding | Table only | Beeswarm (color = feature value magnitude) + Waterfall (cumulative contribution) |

**Core rule: odds-ratios explain the model; SHAP explains a prediction.** For an academic audience already seeing odds-ratios, SHAP earns its place only if the two sections are scoped clearly: odds-ratios in a "Model Interpretation" tab, SHAP global in "Feature Importance" subsection, SHAP local inside the prediction result block. If they overlap without that scoping, the section feels redundant.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features a reviewer or instructor expects when a dashboard claims "SHAP explainability." Missing any of these = the explainability section feels incomplete or token.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| SHAP global bar chart (mean \|SHAP\| per feature) | The canonical "feature importance" SHAP chart — first thing anyone expects | LOW | `shap.plots.bar(shap_values)` or `shap.plots.bar(shap_values.abs.mean(0))`; rendered via `matplotlib`, `show=False`, then `st.pyplot(fig)`. Uses the full training set passed through `pipe["prep"].transform(X_train)`. Explainer: `shap.LinearExplainer(pipe["clf"], X_train_transformed)`. |
| SHAP beeswarm plot (global, full dataset) | Shows direction AND magnitude — what bar chart alone cannot; standard companion to bar | MEDIUM | `shap.plots.beeswarm(shap_values, show=False)` → `st.pyplot(plt.gcf())`. Requires mapping feature names from `pipe["prep"].get_feature_names_out()` to the `Explanation` object. Color encodes raw feature value (high=red, low=blue). 918 samples = acceptable render time. |
| SHAP local waterfall (per prediction, shown after form submit) | The single most-requested local explanation — "why did this patient get p=0.87?" | MEDIUM | Computed on the single row returned by the prediction form, AFTER pipeline preprocessing. `shap.plots.waterfall(shap_values_single[0], show=False)` → `st.pyplot(plt.gcf())`. Base value = E[f(x)] (training set mean). Requires reconstructing a 1-row DataFrame, preprocessing it the same way as training. |
| Feature name mapping (original names, not `cat__ST_Slope_Up`) | Internal sklearn pipeline names are unreadable; audience is clinical/academic | LOW | `pipe["prep"].get_feature_names_out()` returns `["num__Age", "cat__ST_Slope_Up", ...]`. Must map these to display names consistent with `VAR_LABELS` and `CAT_LABELS` from `src/config.py`. A dict built from `config.py` at import time is sufficient. |
| Explainer cached in Streamlit (`@st.cache_resource`) | Without caching, the explainer is rebuilt on every UI interaction — unacceptable latency | LOW | `LinearExplainer` on 918 rows is fast, but rebuilding on every re-render breaks UX. Pattern: `@st.cache_resource def get_shap_explainer(): ...` returning the fitted explainer + precomputed training SHAP values. |
| Dedicated "Explicabilidade" section in sidebar navigation | The PROJECT.md goal is "paridade visual com o descritivo" — requires its own nav entry | LOW | Add `"Explicabilidade"` to the `st.sidebar.radio` options in `main()`. Section function `section_explainability()` wraps both global plots. Local waterfall stays inside `section_prediction()`, shown after form submit. |

### Differentiators (Competitive Advantage)

Features that make the explainability section stand out beyond the minimum — valuable but not assumed.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Side-by-side comparison: SHAP bar vs Odds-Ratio bar | Explicitly shows where the two agree and diverge — directly answers the "what does SHAP add?" question for an academic audience | MEDIUM | Two `st.columns` side by side: left = existing odds-ratio ranking, right = SHAP mean-abs bar. Audience can see ST_Slope, ChestPainType, Sex appear top in both — reinforcing validity — while SHAP reveals magnitude differences at instance level that OR cannot. Requires only reading `pred_odds_ratios.csv` (already exists) and rendering it as a bar chart. |
| Human-readable waterfall feature labels with actual input values | Shows "ST_Slope = Flat contributed +0.41" rather than "cat__ST_Slope_Flat = 0.41" | LOW | Build label map from `src/config.py` VAR_LABELS + CAT_LABELS. Apply to `Explanation.feature_names` before calling `shap.plots.waterfall`. High instructional value for clinical/academic audience. |
| Probability annotation on waterfall (base value → final p) | Connects the waterfall output back to the P(HeartDisease) metric the user already sees | LOW | `LinearExplainer` output for logistic regression is in log-odds space. Annotate the figure with `f"Base rate: {sigmoid(base_value):.1%} → Prediction: {proba:.1%}"` above the waterfall. Clarifies that the waterfall sums explain the log-odds shift, not the raw probability shift. |
| SHAP-precomputed artefact (`shap_values_train.npy` + `shap_feature_names.json`) | Dashboard loads precomputed global SHAP values instead of recomputing on startup — faster cold start, reproducible | MEDIUM | `src/train_model.py` extended to compute and persist SHAP values over the training set. Dashboard loads these via `np.load` / `json.load` instead of recomputing. Seeds already fixed. Reproducibility is a stated constraint. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Interactive SHAP force plot (JavaScript) | Looks impressive; is the "classic" SHAP viz from early demos | `shap.force_plot()` outputs JavaScript/HTML; Streamlit community forums confirm it does not render via `st.pyplot` and requires `streamlit_shap` third-party component or `st.components.v1.html` with the full JS bundle — adds a non-trivial dependency and fragile rendering path. The waterfall plot is the modern replacement and renders cleanly via matplotlib. | Use `shap.plots.waterfall` (matplotlib, `show=False` → `st.pyplot`). Same information, zero rendering issues. |
| SHAP dependence plots per feature | Useful for non-linear models to show interaction effects | For logistic regression, SHAP dependence is exactly linear by construction — it will produce a straight line, adding no information beyond what the coefficient already states. Teaching moment against, not for, this feature. | Mention in academic context: "dependence plots are valuable for tree models where SHAP can capture non-linearities; for logistic regression they are redundant with coefficient plots." |
| Kernel SHAP (`shap.KernelExplainer`) as the explainer | Model-agnostic, appears more "general" | For logistic regression, `LinearExplainer` computes exact SHAP values analytically. `KernelExplainer` uses Monte Carlo sampling and is 10-100x slower with approximation error. Using it on a linear model is technically incorrect (unnecessary approximation) and slow. | Use `shap.LinearExplainer` always for this logistic pipeline. |
| Per-feature SHAP distribution over the filtered dataset | Filter widgets already narrow cohort; recomputing SHAP over filtered subsets on every slider drag | Filtering 918 rows to e.g. 50 and recomputing SHAP on the fly on each UI event creates latency and risks near-empty cohorts (< 10 samples) producing unstable SHAP distributions. Also conceptually muddled: the explainer was fitted on training data, not on the filtered subset. | Keep global SHAP fixed to training set (precomputed). Filtering is for the descriptive analysis sections, not for model explanations. Note this boundary clearly in the UI with a caption. |
| Cross-validation SHAP stability analysis | Technically rigorous — shows whether SHAP rankings are stable across folds | Out of scope per PROJECT.md: "Sem expandir avaliação (cross-val/calibração/threshold ficam fora)". Cross-val SHAP also multiplies compute by n_folds. | Accept that single-split SHAP over training set is sufficient for academic purposes at this scale. |
| Probability-space SHAP (link="logit" passed to older API) | "More intuitive" probability contributions per feature | The link function transforms the output space but makes SHAP values non-additive in log-odds space, breaking the core Shapley additivity property. `LinearExplainer` correctly operates in log-odds; the waterfall base value is in log-odds. Annotate the chart to explain this, rather than distorting the math. | Annotate the base value with sigmoid conversion (see Differentiators above). |

---

## Feature Dependencies

```
[Explainer init + training SHAP precompute]
    └──requires──> [Trained pipeline: models/logistic_model.joblib]
    └──requires──> [Training X_train (split must be reproducible — RANDOM_STATE fixed)]

[Global bar chart]
    └──requires──> [Explainer init + training SHAP precompute]

[Global beeswarm plot]
    └──requires──> [Explainer init + training SHAP precompute]
    └──requires──> [Feature name mapping from get_feature_names_out()]

[Local waterfall (per patient)]
    └──requires──> [Explainer init]
    └──requires──> [Prediction form submission (existing section_prediction)]
    └──requires──> [Pipeline preprocessor: pipe["prep"].transform(single_row)]

[Side-by-side SHAP vs OR comparison] (Differentiator)
    └──requires──> [Global bar chart]
    └──requires──> [output/tables/pred_odds_ratios.csv (already exists)]

[Precomputed artefacts: shap_values_train.npy + shap_feature_names.json] (Differentiator)
    └──requires──> [src/train_model.py extended]
    └──enhances──> [Dashboard cold-start performance]
    └──enhances──> [Reproducibility constraint]

[Human-readable waterfall labels] (Differentiator)
    └──requires──> [VAR_LABELS + CAT_LABELS from src/config.py]
    └──enhances──> [Local waterfall (per patient)]
```

### Dependency Notes

- **Local waterfall requires pipeline preprocessing of the single row:** `pipe["prep"].transform(row)` must be called before passing to the explainer. The existing `section_prediction` already builds the row DataFrame — waterfall computation slots in right after `model.predict_proba(row)`.
- **Explainer requires the classifier step, not the full pipeline:** `shap.LinearExplainer(pipe["clf"], X_train_transformed)` where `X_train_transformed = pipe["prep"].transform(X_train)`. The explainer does not accept the full pipeline object — it needs the isolated `LogisticRegression` and already-transformed data.
- **RANDOM_STATE already fixed in config.py:** Reproducing the same `X_train` split for SHAP background data is guaranteed without any new code.
- **Precomputed artefact enhances reproducibility:** If global SHAP is precomputed in `train_model.py` and saved, the dashboard loads it deterministically. If computed on-the-fly in the dashboard, it is still deterministic (same `X_train`, same explainer), but slightly slower.

---

## MVP Definition

### Launch With (v2.1)

Minimum viable SHAP section that achieves the stated milestone goal: "give the predictive model the same depth/prominence the descriptive analysis already has."

- [ ] Global SHAP bar chart (mean |SHAP|) — canonical feature importance, renders via matplotlib, no new dependencies beyond `shap`
- [ ] Global SHAP beeswarm — direction + magnitude, companion to bar, one function call after bar
- [ ] Local SHAP waterfall after form submit — per-patient explanation, completes the "why this patient" story
- [ ] Feature name mapping (readable labels, not `cat__ST_Slope_Flat`) — required for academic audience
- [ ] Dedicated "Explicabilidade" sidebar section — required for visual parity with descriptive analysis
- [ ] `@st.cache_resource` for explainer — required for acceptable UX

### Add After Validation (v2.1.x)

- [ ] Side-by-side SHAP bar vs Odds-Ratio bar — powerful for academic insight; easy to add once both charts exist
- [ ] Probability annotation on waterfall — one `st.caption` line; high instructional value, near-zero effort
- [ ] Human-readable labels with actual input values in waterfall — two-line dict lookup from config.py

### Future Consideration (v3+)

- [ ] Precomputed SHAP artefacts saved by `train_model.py` — adds reproducibility and cold-start speed; deferred because dashboard `@st.cache_resource` already makes re-computation cheap enough for 918 rows
- [ ] SHAP decision plot (cumulative path to prediction) — informative but redundant given waterfall at this scale

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Global bar chart (mean \|SHAP\|) | HIGH — canonical, expected by any ML instructor | LOW | P1 |
| Global beeswarm | HIGH — adds direction information bar lacks | LOW-MEDIUM | P1 |
| Local waterfall after predict | HIGH — closes the "why this patient" gap | MEDIUM | P1 |
| Feature name mapping | HIGH — without it, plots are unreadable to target audience | LOW | P1 |
| Sidebar nav section | HIGH — structural, required for paridade visual | LOW | P1 |
| Explainer caching | HIGH — UX correctness, not optional | LOW | P1 |
| SHAP bar vs OR comparison | MEDIUM-HIGH — academic insight, differentiator | LOW | P2 |
| Probability waterfall annotation | MEDIUM — clarifies log-odds space for non-ML audience | LOW | P2 |
| Readable labels with values | MEDIUM — polishes local explanation | LOW | P2 |
| Precomputed artefacts | LOW-MEDIUM — reproducibility, marginal speed gain | MEDIUM | P3 |
| Force plot (interactive JS) | LOW (anti-feature) | HIGH + fragile | NEVER |
| Kernel SHAP | LOW (anti-feature — wrong explainer) | MEDIUM | NEVER |
| Dependence plots | LOW (anti-feature — linear model) | LOW | NEVER |

---

## Sources

- SHAP library documentation (Context7 / shap/shap): `LinearExplainer`, `shap.plots.beeswarm`, `shap.plots.waterfall`, `shap.plots.bar`, matplotlib rendering with `show=False`
- Streamlit community: [Force plot rendering issues in Streamlit](https://discuss.streamlit.io/t/shap-shap-force-plot-on-streamlit/10071) — confirms JavaScript force plot is problematic, waterfall is the correct alternative
- [SHAP Values for Logistic Regression — Medium/Biased-Algorithms](https://medium.com/biased-algorithms/shap-values-for-logistic-regression-51ffa5bdcedc)
- [Case study: explaining credit modeling predictions with SHAP — Fiddler Labs](https://medium.com/fiddlerlabs/case-study-explaining-credit-modeling-predictions-with-shap-2a7b3f86ec12)
- Existing project artefacts: `output/tables/pred_odds_ratios.csv`, `dashboard/app.py`, `src/train_model.py`, `src/config.py`

---

*Feature research for: SHAP explainability milestone (v2.1) — Heart Failure Prediction Dashboard*
*Researched: 2026-06-22*
