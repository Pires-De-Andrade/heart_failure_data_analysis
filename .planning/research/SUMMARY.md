# Project Research Summary

**Project:** Heart Failure Prediction Dashboard - Milestone v2.1 Explicabilidade (SHAP)
**Domain:** SHAP explainability layer on top of a scikit-learn logistic Pipeline surfaced via Streamlit
**Researched:** 2026-06-22
**Confidence:** HIGH

## Executive Summary

This milestone adds SHAP-based model explainability to an already-working Heart Failure prediction dashboard. The existing codebase has a fully trained two-step sklearn Pipeline (ColumnTransformer + LogisticRegression), a prediction form, and a descriptive analysis section. The gap is that the model produces predictions with no per-patient explanation: odds-ratios exist but are global and cannot answer which patient features drove a specific risk score. SHAP closes that gap with three outputs: a global bar chart (mean |SHAP| per feature), a global beeswarm (direction and magnitude), and a local waterfall (per-patient contribution breakdown surfaced after form submission).

The recommended approach is narrow and precise: add one dependency (shap>=0.46,<0.50), extend train_model.py to precompute global SHAP artifacts at train time, and extend dashboard/app.py with a new Explicabilidade section and an augmented prediction form. The explainer must be shap.LinearExplainer targeting the extracted LogisticRegression step, not the full Pipeline, with ColumnTransformer-transformed data as background. All rendering goes through st.pyplot(plt.gcf(), clear_figure=True) with plt.close() -- the same pattern already established throughout app.py. LinearExplainer takes 0.21 ms per row and 19 ms for all 734 training rows; the only discipline required is Streamlit caching via @st.cache_resource for the explainer object.

The critical risk is the wrong-input-space class of errors: passing the full Pipeline instead of the isolated classifier, passing raw DataFrame columns instead of ColumnTransformer-transformed arrays, and failing to inject human-readable feature names before plotting. All three produce silently wrong or unreadable output. A second risk is log-odds/probability confusion: LinearExplainer outputs in log-odds space and the link argument is confirmed broken (GitHub shap#3767); the waterfall must be annotated to clarify this, with the actual probability shown separately from model.predict_proba(). Both risk classes have specific assertions and verification steps defined in the pitfalls research.

## Key Findings

### Recommended Stack

The project stack is already complete. Only one addition is needed: shap>=0.46,<0.50. The lower bound ensures NumPy 2 support (added in 0.46.0); the upper bound avoids SPEC 0 minimum dependency bumps that 0.50+ introduced. SHAP 0.48.0 is already installed in the project .venv, so the requirement is effectively satisfied -- it only needs to be made explicit in requirements.txt. No other packages are needed: streamlit-shap is unmaintained (last release March 2022) and conflicts with matplotlib>=3.7; LIME, captum, and all tree/neural XAI packages are inapplicable to logistic regression.

**Core technologies:**
- shap>=0.46,<0.50: Single new dependency -- exact Shapley values for logistic Pipeline with NumPy 2 compatibility guaranteed
- shap.LinearExplainer: Correct explainer for this model -- closed-form coef[i]*(x[i]-E[x[i]]), deterministic, 0.21 ms/row; KernelExplainer is 100x slower and an unnecessary approximation for a linear model
- shap.maskers.Independent(X_train_t, max_samples=100): Correct masker for tabular data without feature interaction assumptions
- st.pyplot(plt.gcf(), clear_figure=True): Established rendering pattern already in app.py; captures SHAP internally created figures correctly
- numpy.savez_compressed: Persists background matrix + SHAP values in 29 KB vs. 718 KB for a joblib-serialized Explanation object

**Critical dependency note:** numba is a mandatory transitive dependency of SHAP 0.46-0.47 (not optional). It pulls in llvmlite and requires 100-200 MB on install. Must account for install time on restricted academic networks.

### Expected Features

The target is visual parity with the existing descriptive analysis section.

**Must have (table stakes for v2.1):**
- Global SHAP bar chart (mean |SHAP| per feature) -- canonical feature importance; first thing any ML instructor expects
- Global SHAP beeswarm -- adds direction and magnitude that bar chart alone cannot show; standard companion
- Local SHAP waterfall after form submission -- closes the why-this-patient gap; highest-impact single addition
- Feature name mapping from internal prefixed names (num__Age, cat__ST_Slope_Flat) to Portuguese display names -- required for the academic/clinical audience
- Explicabilidade sidebar section -- structural requirement for visual parity
- @st.cache_resource for explainer -- correctness requirement; without it the explainer rebuilds on every widget interaction

**Should have (differentiators for v2.1.x):**
- Side-by-side SHAP bar vs. Odds-Ratio bar -- directly answers what SHAP adds over OR for academic audience; easy once both charts exist
- Probability annotation on waterfall -- st.caption clarifying log-odds contributions with predicted probability; high instructional value, near-zero effort
- Human-readable waterfall labels with actual input values (e.g. ST_Slope = Flat contributed +0.41) -- two-line dict lookup from src/config.py

**Defer to v3+:**
- Precomputed SHAP artifacts saved to .npy/.json by train_model.py -- @st.cache_resource already makes on-the-fly computation cheap enough for 918 rows
- Interactive force plot (JavaScript) -- anti-feature; requires unmaintained streamlit-shap; waterfall is the modern matplotlib replacement
- SHAP dependence plots -- anti-feature for logistic regression; produces straight lines, adds nothing beyond coefficient plot
- Kernel SHAP -- anti-feature for logistic regression; unnecessary approximation, 100x slower than LinearExplainer

### Architecture Approach

Two parallel flows separated by time: a build-time flow in src/train_model.py that precomputes global SHAP artifacts (output/figures/06_shap_beeswarm.png and output/tables/shap_global.npz), and a runtime flow in dashboard/app.py that loads artifacts for global display and computes local waterfall values on demand per form submission. The explainer is rebuilt from the persisted background matrix (29 KB .npz) via @st.cache_resource -- not persisted as a joblib object (718 KB) -- because 0.36 ms reconstruction is cheaper than deserialization and avoids SHAP version coupling.

**Major components:**
1. src/config.py (modified) -- Add SHAP_NPZ_PATH and SHAP_BEESWARM_PATH constants; all downstream code imports paths from here
2. src/train_model.py (modified) -- Add compute_shap_artifacts(pipe, X_train) and build_display_names() helper; called after joblib.dump in main(); generates both new artifacts
3. output/tables/shap_global.npz (new) -- Compressed numpy archive: shap_values [734,20], X_transformed [734,20] (background for live explainer), expected_value [1]
4. output/figures/06_shap_beeswarm.png (new) -- Precomputed beeswarm over training set; loaded at zero compute cost via st.image()
5. dashboard/app.py (modified) -- get_shap_explainer() (@st.cache_resource), get_shap_global_fig() (@st.cache_data), new section_explainability(), modified section_prediction() with waterfall block inside the if submitted: branch

**Suggested build order:** src/config.py paths -> src/train_model.py extension + artifact generation -> requirements.txt update -> dashboard global section -> dashboard local waterfall. Each step is independently testable before the next.

### Critical Pitfalls

1. **Passing the full Pipeline to LinearExplainer instead of the extracted classifier** -- Extract pipe.named_steps["clf"] and use pipe.named_steps["prep"].transform(X_background) as input. Verify: assert hasattr(explainer.model, "coef_").

2. **Explaining in raw-feature space instead of ColumnTransformer-transformed space** -- Always call preprocessor.transform(X) before passing data to the explainer (both background setup and per-patient local explanations). Verify: assert X_bg.shape[1] == len(preprocessor.get_feature_names_out()) (should be 20, not 11).

3. **Feature name mismatch after OneHotEncoding -- unreadable plot labels** -- LinearExplainer given a numpy array defaults to ["Feature 0", ..., "Feature 19"]. Always inject: sv.feature_names = display_names immediately after creating any Explanation object. display_names is built once from get_feature_names_out() + VAR_LABELS + CAT_LABELS.

4. **Log-odds vs. probability confusion in waterfall display** -- LinearExplainer returns values in log-odds space; the link argument is confirmed broken (GitHub shap#3767) and silently ignored. Keep waterfall in log-odds (mathematically correct and additive); annotate with "escala log-odds; probabilidade prevista = X%"; display actual probability from model.predict_proba() as the primary metric.

5. **Matplotlib figure accumulation across Streamlit reruns** -- Use show=False, capture with plt.gcf(), render with st.pyplot(fig, clear_figure=True), then plt.close(). Mirrors the exact pattern already established in app.py for all other plots.

## Implications for Roadmap

Based on research, the work decomposes into three phases with a strict dependency order.

### Phase 1: Dependency and Artifact Setup

**Rationale:** Everything downstream depends on the SHAP package being explicit in requirements.txt and on the precomputed artifacts existing on disk. Config path constants must be defined before train_model.py or app.py can reference them. This is a zero-UI phase -- verifiable by running pip check and python -m src.train_model and confirming the two new files appear in output/.

**Delivers:** shap>=0.46,<0.50 in requirements.txt; SHAP_NPZ_PATH and SHAP_BEESWARM_PATH in src/config.py; compute_shap_artifacts() and build_display_names() in src/train_model.py; output/figures/06_shap_beeswarm.png and output/tables/shap_global.npz on disk.

**Addresses:** Table-stakes requirements for explainer caching (background data lives in .npz) and precomputed global beeswarm PNG.

**Avoids:** Pitfall 9 (numpy/shap version conflict -- fixed by explicit version pin); Pitfall 10 (reproducibility -- random_state=RANDOM_STATE from src/config.py in all shap.utils.sample calls); Pitfalls 1 and 2 (wrong inputs -- asserted in compute_shap_artifacts() with shape checks).

### Phase 2: Global Explainability Section

**Rationale:** Once artifacts exist and the explainer can be constructed from the .npz, the global beeswarm and bar chart can be added as a new static sidebar section with no dependency on the prediction form. This section is independently testable: navigate to Explicabilidade and verify both plots render with Portuguese display names and correct feature ordering.

**Delivers:** New section_explainability() in dashboard/app.py; get_shap_explainer() (@st.cache_resource); get_shap_global_fig() (@st.cache_data); Explicabilidade entry in sidebar st.sidebar.radio; global bar chart and beeswarm with readable labels.

**Uses:** shap.Explanation rebuilt from .npz; build_display_names() from Phase 1; st.image(SHAP_BEESWARM_PATH) or st.pyplot(get_shap_global_fig()).

**Avoids:** Pitfall 3 (feature names injected before rendering); Pitfall 5 (no force_plot used); Pitfall 6 (explicit plt.close after each st.pyplot); Pitfall 7 (@st.cache_resource prevents explainer rebuild on every rerun); Pitfall 8 (beeswarm loaded from precomputed PNG, not recomputed live on every dashboard load).

### Phase 3: Local Waterfall in Prediction Form

**Rationale:** The local waterfall depends on the prediction form working AND on the explainer from Phase 2 being cached. It inserts inside the if submitted: block after the existing proba/pred display -- no changes to form layout itself. This is the highest-impact user-facing deliverable: it directly answers "why this patient?"

**Delivers:** Waterfall plot rendered below prediction result after form submission; probability annotation clarifying log-odds space; human-readable labels with actual input values (differentiator, near-zero effort once waterfall exists).

**Uses:** get_shap_explainer(model) from Phase 2; prep = model.named_steps["prep"].transform(row) -- the single structural addition required inside section_prediction(); shap.plots.waterfall(sv_local[0], show=False).

**Avoids:** Pitfall 4 (log-odds annotation + proba from predict_proba() shown as primary metric); Pitfall 6 (explicit figure close after waterfall st.pyplot).

### Phase Ordering Rationale

- Phase 1 before 2: The .npz file must exist before the dashboard can load it; config path constants must be defined before any code imports them.
- Phase 2 before 3: The get_shap_explainer() cached loader is written in Phase 2 and reused in Phase 3; feature name mapping is established in Phase 2 and applied to local waterfall in Phase 3.
- Differentiators (SHAP vs. OR side-by-side, waterfall probability annotation, readable value labels) slot into Phase 3 as low-effort additions once the waterfall exists.

### Research Flags

Phases with standard patterns (skip --research-phase during planning):
- **Phase 1:** All integration points verified; exact code patterns provided in STACK.md and ARCHITECTURE.md; performance benchmarks measured; shap>=0.46 already installed in .venv.
- **Phase 2:** Global plot rendering fully documented with verified patterns; caching strategy confirmed; complete feature name table with all 20 post-OHE names provided in ARCHITECTURE.md.
- **Phase 3:** Insertion point for waterfall in section_prediction() is exact and specific; log-odds annotation strategy documented; no unknowns remain.

No phase requires a --research-phase deep-dive. All patterns are documented to implementation-ready specificity.

Open cosmetic decision (Phase 2 planning): Whether to show the global beeswarm as a precomputed PNG via st.image() (simpler, zero compute) or recompute it live from .npz via st.pyplot() (allows dynamic feature count). Recommendation: prefer st.image() unless interactive colorbar scaling is explicitly needed.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | SHAP 0.48.0 verified in .venv; version compatibility checked against PyPI metadata; streamlit-shap exclusion confirmed via release dates and matplotlib pin conflict |
| Features | HIGH | Feature table derived from SHAP library docs verified via Context7; rendering patterns confirmed against Streamlit community; anti-features validated with specific GitHub issues |
| Architecture | HIGH | All integration points verified against live codebase; performance benchmarks measured; expected_value verified to float64 precision; all 20 post-OHE feature names confirmed |
| Pitfalls | HIGH | Every pitfall backed by SHAP GitHub issues (numbered), Streamlit community threads, or official docs; link bug confirmed open (GitHub shap#3767); recovery costs assessed |

**Overall confidence:** HIGH

### Gaps to Address

- Cosmetic rendering choice (Phase 2): st.image(PNG) vs. st.pyplot(fig_from_npz). Both are correct; decide during Phase 2 task planning based on whether colorbar interactivity is desired.
- max_samples value for masker: Research recommends 100. For LinearExplainer, only background mean/covariance matter, so precision is unaffected above ~50 rows. Document this rationale in a comment inside compute_shap_artifacts().
- Waterfall annotation phrasing in Portuguese: Exact Portuguese wording not standardized -- should be agreed on during Phase 3 task planning to match the dashboard language register.

## Sources

### Primary (HIGH confidence)
- SHAP library documentation via Context7 (/shap/shap) -- LinearExplainer, shap.plots.beeswarm, shap.plots.waterfall, shap.plots.bar, show=False rendering pattern, Explanation object API
- PyPI shap 0.46.0 + 0.47.0 JSON metadata -- requires_python >=3.9, numba>=0.54 confirmed core dep, numpy/matplotlib no upper bound
- SHAP release notes (shap.readthedocs.io/en/latest/release_notes.html) -- numpy 2 support in 0.46.0; Python 3.9/3.10 dropped in 0.50
- Streamlit docs (docs.streamlit.io) -- st.pyplot fig=None deprecated; clear_figure=True recommended
- Live codebase verification (2026-06-22): shap.__version__ = 0.48.0; get_feature_names_out() returns 20 features; expected_value = 0.247; SHAP sum matches clf.decision_function() to float64 precision; shap_global.npz = 28.7 KB; beeswarm PNG = 158 KB

### Secondary (MEDIUM confidence)
- Streamlit community: SHAP force_plot rendering issues -- confirms JS force plot blank in st.pyplot
- Streamlit community: Computing SHAP memory increase -- figure accumulation without plt.close()
- SHAP Values for Logistic Regression (Medium/Biased-Algorithms)
- Case study: explaining credit modeling predictions with SHAP (Fiddler Labs)

### Tertiary (confirmed-open GitHub issues)
- GitHub shap#3767 -- link argument silently ignored in LinearExplainer; do not use link=shap.links.logit
- GitHub shap#3716 -- numpy 2 incompatibility in shap < 0.46.0
- GitHub shap#3215 -- random_state in shap.utils.sample not preserved between SHAP versions; always pass explicitly
- GitHub shap#3186 -- numpy/numba dependency conflicts
- PyPI streamlit-shap 1.0.2 -- last release March 2022; unmaintained; matplotlib<=3.4.3 conflict confirmed

---
*Research completed: 2026-06-22*
*Ready for roadmap: yes*
