# System Architecture & Technical Specifications
## ValuEstate ML Pro — Enterprise Real Estate Valuation Intelligence

### 1. Architectural Diagram

```
+-----------------------------------------------------------------------------------+
|                                 USER / CLIENT                                     |
|           +---------------------------+   +---------------------------+           |
|           |   Web Browser (HTML5/CSS) |   |   API Consumer (REST/JSON)|           |
+-----------+-------------+-------------+---+-------------+-------------+-----------+
                          |                               |
                          v                               v
+-----------------------------------------------------------------------------------+
|                   FLASK APPLICATION & SECURITY LAYER (run.py)                     |
|  - Security Headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection    |
|  - Payload Size Limiter (1MB) & CORS Configuration                                |
|                                                                                   |
|   +------------------------------------+   +----------------------------------+   |
|   |         Web UI (routes.py)         |   |      REST API (api_routes.py)    |   |
|   |  - Dashboard      - Result         |   |  - /api/health   - /api/predict  |   |
|   |  - Predict Form   - History        |   |  - /api/metrics  - /api/history  |   |
|   |  - Performance    - Explainability |   |  - /api/model-info               |   |
|   +-----------------+------------------+   +-----------------+----------------+   |
|                     |                                        |                    |
|                     +--------------------+-------------------+                    |
|                                          |                                        |
|                                          v                                        |
|                       +--------------------------------------+                    |
|                       |  Input Validation & Schema Enforcer  |                    |
|                       |  - NaN / Infinity / Boolean Rejection|                    |
|                       |  - Bounded Range Checking            |                    |
|                       |         (app/validators.py)          |                    |
|                       +------------------+-------------------+                    |
+------------------------------------------|----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                              MACHINE LEARNING ENGINE                              |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |           Model Inference Engine (src/model_inference.py)                   |  |
|  |  +-----------------------------------------------------------------------+  |  |
|  |  | Scikit-learn Pipeline (ColumnTransformer + GradientBoostingRegressor)|  |  |
|  |  |  - Imputation (Median / Mode)                                        |  |  |
|  |  |  - Categorical Encoding (OneHotEncoder)                               |  |  |
|  |  |  - Standard Scaling                                                   |  |  |
|  |  +-----------------------------------------------------------------------+  |  |
|  |                                                                             |  |
|  |  +-----------------------------------------------------------------------+  |  |
|  |  | Conformal Prediction Uncertainty Engine (src/conformal_prediction.py)|  |  |
|  |  |  - Calibrated Nonconformity Residual Quantiles (nominal 90% coverage) |  |  |
|  |  |  - Non-negative Lower Bound & Monotonic Ordering                      |  |  |
|  |  +-----------------------------------------------------------------------+  |  |
|  |                                                                             |  |
|  |  +-----------------------------------------------------------------------+  |  |
|  |  | Local Explainability Engine (src/model_explainability.py)             |  |  |
|  |  |  - Counterfactual Feature Perturbation                                |  |  |
|  |  |  - Reconciled Waterfall Contributions vs Training Baseline            |  |  |
|  |  +-----------------------------------------------------------------------+  |  |
|  +-----------------------------------------------------------------------------+  |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                               PERSISTENCE STORAGE                                 |
|                                                                                   |
|  +------------------------------------+   +------------------------------------+  |
|  |       SQLite Audit Database        |   |           Model Registry           |  |
|  |     (data/app_database.db)         |   |      (models/metadata_v1.json)     |  |
|  |   - Predictions table              |   |   - Active Pipeline (v1.joblib)    |  |
|  |   - Deterministic Ordering Index   |   |   - SHA-256 Dataset Provenance     |  |
|  |   - 3-5s Window Payload Deduplicat.|   |   - 5-Fold Cross-Validation Stats  |  |
|  |   - Conformal Prediction Bounds    |   |   - Holdout Permutation Importance |  |
|  +------------------------------------+   +------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

### 2. Methodological 3-Stage Machine Learning Lifecycle
1. **Stage 1 (Training & Preprocessing Pipelines):**
   - 80% split (240 records).
   - Numerical (`Area`, `Bedrooms`, `Bathrooms`, `Age`) and Categorical (`Location`, `Property_Type`).
   - Hyperparameter grids optimized exclusively across internal cross-validation folds.
2. **Stage 2 (Model Selection via 5-Fold CV):**
   - 7 competing architectures benchmarked using strictly training-only 5-fold CV RMSE.
   - Gradient Boosting selected based on lowest CV RMSE (₹11.56 Lakhs) and highest CV $R^2$ (0.9915).
3. **Stage 3 (Untouched Holdout Final Evaluation):**
   - Evaluated once on the 60-record holdout set.
   - Final Test $R^2$: 0.9918, Test RMSE: ₹10.79 Lakhs, Test MAPE: 3.75%.
   - Test set is never touched during hyperparameter tuning or feature selection.

### 3. Conformal Prediction Engine
- Replaced heuristic $\pm \text{MAPE}$ tolerance percentages with Split Conformal Prediction.
- Fits calibration scores $R_i = |y_i - \hat{y}_i|$ across 240 training instances.
- Computes empirical $(1-\alpha)$-th quantile:
  $$\hat{q} = \text{Quantile}\left(R, \frac{\lceil (n+1)(1-\alpha) \rceil}{n}\right) = \pm ₹21,59,600.08$$
- Guarantees marginal coverage probability:
  $$\mathbb{P}(Y_{n+1} \in [\hat{y}_{n+1} - \hat{q}, \hat{y}_{n+1} + \hat{q}]) \ge 90\%$$

### 4. Database Determinism & Deduplication
- **Deterministic Ordering:** All historical queries enforce `ORDER BY created_at DESC, id DESC`.
- **Deduplication:** Computes canonical SHA-256 hash of normalized property attributes. Identical submissions within 5 seconds return the existing prediction ID, preventing double-entry race conditions.
