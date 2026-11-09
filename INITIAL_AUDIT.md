# Initial Repository Audit & Architectural Gap Analysis
**Project:** ValuEstate ML Pro — Residential Real Estate Valuation Intelligence  
**Audit Date:** November 2026  
**Status:** Completed Prior to Architectural Refinement  

---

## 1. Executive Summary & Existing Architecture
ValuEstate ML Pro is a fully integrated end-to-end Machine Learning web application and REST API predicting residential property prices in Indian Rupees (INR ₹). The core stack utilizes Python 3.10+, Scikit-learn 1.4, Flask 3.0, SQLite 3, Bootstrap 5, Pytest, and Docker.

While the existing system contains a functional pipeline, professional visual branding, and 22 passing tests, a rigorous technical audit identified several statistical, methodological, and security vulnerabilities that must be resolved to meet enterprise and academic standards.

---

## 2. Identified Vulnerabilities & Methodological Deficiencies

### Defect 1: Test-Set Contamination During Model Selection (Methodological Error)
- **Location:** [`src/model_training.py`](file:///d:/The%20Developers%20Arena%20Intership%20Task%20-%204/src/model_training.py#L196)
- **Current Behavior:** `comparison_df.sort_values(by="Test_RMSE", ascending=True)` selects the best production model by sorting its holdout test performance.
- **Problem:** The test holdout set ceases to be an independent, unbiased estimator of generalization error when it is used as the criterion for model selection.
- **Required Correction:** Enforce a strict 3-stage ML lifecycle:
  1. *Stage 1 (Training):* Pipeline fitting, preprocessing, and hyperparameter tuning using training data only.
  2. *Stage 2 (Model Selection):* Compare candidate models strictly using training 5-fold cross-validation RMSE ($CV\_RMSE\_Mean$).
  3. *Stage 3 (Final Evaluation):* Refit the selected best model on the complete training set and evaluate **once** on the untouched holdout test set.

### Defect 2: Hardcoded Feature Importance Scores (Explainability Flaw)
- **Location:** [`app/api_routes.py`](file:///d:/The%20Developers%20Arena%20Intership%20Task%20-%204/app/api_routes.py#L106-L115) and [`templates/explainability.html`](file:///d:/The%20Developers%20Arena%20Intership%20Task%20-%204/templates/explainability.html#L48-L100)
- **Current Behavior:** Hardcoded static percentages (`Area ~72.5%`, `Location ~18.5%`, `Age ~5.2%`, etc.) are returned by `/api/feature-importance` and displayed on the web dashboard.
- **Problem:** Artificial, non-reproducible explainability that fails to reflect actual model parameters or dataset shifts.
- **Required Correction:** Compute dynamic permutation importance on the holdout test set and native tree-based feature importance from the production Gradient Boosting model. Save raw metrics and normalized percentages to metadata and load dynamically in templates and APIs.

### Defect 3: Ad-Hoc Tolerance Band Disguised as Uncertainty (Statistical Flaw)
- **Location:** [`app/routes.py`](file:///d:/The%20Developers%20Arena%20Intership%20Task%20-%204/app/routes.py#L79-L84) and [`templates/result.html`](file:///d:/The%20Developers%20Arena%20Intership%20Task%20-%204/templates/result.html#L25-L29)
- **Current Behavior:** Calculates bounds as $\text{Price} \times (1 \pm \text{Test\_MAPE})$.
- **Problem:** Misleadingly presents test-set MAPE as an individual prediction tolerance interval. MAPE does not provide formal statistical coverage guarantees.
- **Required Correction:** Implement inductive split-conformal prediction (or cross-conformal prediction) using calibration residuals to construct a statistically valid prediction interval at a nominal 90% coverage level.

### Defect 4: Controlled Feature Engineering Validation Gap
- **Location:** [`src/feature_engineering.py`](file:///d:/The%20Developers%20Arena%20Intership%20Task%20-%204/src/feature_engineering.py)
- **Current Behavior:** Feature engineering functions exist but have not been evaluated in a controlled ablation experiment against the raw feature baseline.
- **Required Correction:** Conduct controlled 5-fold CV experiments comparing Experiment A (raw 6 features) against Experiment B (engineered features). Only retain features that statistically improve cross-validation RMSE without introducing collinear instability.

### Defect 5: Unvalidated Location Premium Claims
- **Location:** [`templates/explainability.html`](file:///d:/The%20Developers%20Arena%20Intership%20Task%20-%204/templates/explainability.html#L70)
- **Current Behavior:** Claims City Center properties have a "+101% premium over Rural" without providing empirical context.
- **Required Correction:** Calculate descriptive statistics (mean price, median price, price per sq ft mean/median, record counts) from the ground-truth dataset and explicitly distinguish descriptive unadjusted sample differences from adjusted model coefficients.

### Defect 6: Security & API Hardening Deficiencies
- **Location:** [`config/config.py`](file:///d:/The%20Developers%20Arena%20Intership%20Task%20-%204/config/config.py), [`app/validators.py`](file:///d:/The%20Developers%20Arena%20Intership%20Task%20-%204/app/validators.py), [`run.py`](file:///d:/The%20Developers%20Arena%20Intership%20Task%20-%204/run.py)
- **Current Behavior:** Default debug mode on in dev script, missing `NaN` / `Infinity` validation checks, lack of security response headers, and potential duplicate database inserts on rapid double submissions.
- **Required Correction:** Implement `math.isnan()` and `math.isinf()` rejections, set production security headers, disable debug mode by default, implement database duplicate submission prevention, and restrict CORS to configured domains.

---

## 3. Files Requiring Modification & Preservation Plan

| Component | Target File | Actions & Modifications Required |
|---|---|---|
| **Backup** | `backup/pre_correction_snapshot/` | Preserved snapshot created prior to edits. |
| **ML Training** | `src/model_training.py` | Refactor to 3-stage lifecycle: train, CV-based selection, holdout evaluation. |
| **Model Registry** | `src/model_registry.py` | Store conformal calibration quantiles, dynamic feature importances, and provenance hashes. |
| **Inference Engine** | `src/model_inference.py` | Support conformal intervals, dynamic local attribution reconciliation, and validation. |
| **Explainability** | `src/model_explainability.py` | Generate dynamic permutation importance and model-specific tree importances without hardcoded values. |
| **Database** | `app/database.py` | Enforce deterministic sorting `ORDER BY created_at DESC, id DESC` and duplicate insert prevention. |
| **Validation** | `app/validators.py` | Add NaN and Infinity checks, strict schema boundaries, and error formatting. |
| **API Blueprint** | `app/api_routes.py` | Return dynamic feature importances, conformal bounds, and sanitized error messages. |
| **Web Routes** | `app/routes.py` | Connect dynamic conformal intervals and feature contributions to templates. |
| **Templates** | `templates/*.html` | Update result, performance, and explainability templates to render dynamic metrics. |
| **Testing** | `tests/` | Retain all 22 existing tests; add test suites for CV selection, conformal prediction, and security. |
| **Documentation** | `README.md`, `reports/`, `docs/` | Update reports to reflect actual retrained metrics and methodologies. |

---

## 4. Preserved Core Architecture
The following assets and identities are strictly maintained:
1. Brand: **ValuEstate ML Pro — Residential Real Estate Valuation Intelligence**
2. Blueprints: `web_bp` and `api_bp`
3. Database: SQLite with `predictions` and `model_versions` tables
4. Endpoints: `/api/health`, `/api/model-info`, `/api/predict`, `/api/metrics`, `/api/feature-importance`, `/api/predictions`
5. Template layouts: Clean Bootstrap 5 SaaS theme with navigation and responsive footers
6. Containerization: `Dockerfile` and `docker-compose.yml`

