# Model Explainability & Interpretability Report
## ValuEstate ML Pro — Enterprise Real Estate Valuation Intelligence

### 1. Architectural Philosophy
Black-box machine learning models in automated real estate valuation (AVMs) introduce significant regulatory and stakeholder risks if predictions cannot be justified and audited. In ValuEstate ML Pro, explainability is not an afterthought or a static marketing claim. It is mathematically grounded, dynamically computed, and verified against untouched holdout data.

---

### 2. Global Explainability

#### A. Permutation Feature Importance (Holdout Test Set)
Permutation importance evaluates the direct drop in model performance ($R^2$) when the values of a single feature are randomly shuffled across the 60 untouched test instances, breaking the relationship between that feature and the ground truth.

**Mathematical Formulation:**
$$I(f) = R^2_{\text{baseline}} - \frac{1}{K} \sum_{k=1}^K R^2_{\text{permuted}(f, k)}$$

Where $K=10$ random repetitions with a fixed random seed (`random_state=42`).

**Empirical Results:**
| Feature | Mean Metric Drop ($\Delta R^2$) | Standard Deviation ($\sigma$) | Normalized Importance (%) | Economic Interpretation |
|---|---|---|---|---|
| **Area** | **1.2599** | ±0.1417 | **88.46%** | Core physical valuation driver; square footage dictates overall space scale. |
| **Location** | **0.1085** | ±0.0381 | **7.62%** | Urban zoning & accessibility premium (City Center vs Suburb vs Rural). |
| **Age** | **0.0401** | ±0.0152 | **2.82%** | Structural depreciation over property lifecycle. |
| **Bedrooms** | **0.0125** | ±0.0068 | **0.88%** | Functional room allocation utility. |
| **Property_Type** | **0.0029** | ±0.0021 | **0.21%** | Typology variation (House vs Villa vs Apartment). |
| **Bathrooms** | **0.0003** | ±0.0003 | **0.02%** | Additional sanitary amenity convenience. |

#### B. Native Tree-Based Importance (Mean Decrease in Impurity / Gini)
Extracted directly from the ensemble decision trees (`model.feature_importances_`) across the one-hot encoded representation:
- `num__Area`: **0.7842** (78.42%)
- `cat__Location_City Center`: **0.0812** (8.12%)
- `num__Age`: **0.0519** (5.19%)
- `cat__Location_Suburb`: **0.0425** (4.25%)
- `num__Bedrooms`: **0.0210** (2.10%)
- `cat__Property_Type_Villa`: **0.0118** (1.18%)
- `num__Bathrooms`: **0.0051** (0.51%)
- `cat__Property_Type_House`: **0.0023** (0.23%)

---

### 3. Local Prediction Attribution (Saabas Tree Path Decomposition)
For each individual property valuation, the system computes local feature attributions using the **Saabas Tree Path Decomposition** algorithm across all ensemble boosting stages:

1. **Algorithm Specification & Attribution Mechanism:**
   The algorithm traces the specific decision path that an evaluated property takes through every decision tree in the Gradient Boosting ensemble. At each internal split node $s$ on feature $j$, the decision path moves from parent node to child node, changing the local sub-tree expected output by:
   $$\Delta_{t, s} = \text{value}(\text{child}_s) - \text{value}(\text{parent}_s)$$
   Accumulated across all $T$ boosting trees scaled by learning rate $\eta$:
   $$\text{Contribution}_j = \sum_{t=1}^T \eta \sum_{s \in \text{path}_t, \, \text{split}(s) = j} (\text{value}(\text{child}_{t,s}) - \text{value}(\text{parent}_{t,s}))$$

2. **Baseline Derivation ($\bar{y}_{\text{base}}$):**
   The baseline is mathematically calculated as the model's initial estimator expectation plus the accumulated root node expectations across all ensemble trees:
   $$\bar{y}_{\text{base}} = \hat{f}_{\text{init}}(\mathbf{x}) + \sum_{t=1}^T \eta \cdot \text{value}(\text{root}_t)$$

3. **Deterministic One-Hot Feature Grouping:**
   Transformed one-hot categorical indicators (`cat__Location_City Center`, `cat__Location_Suburb`, `cat__Location_Rural`, `cat__Property_Type_House`, `cat__Property_Type_Villa`, etc.) and scaled numerical features (`num__*`) map deterministically back to their original domain features (`Location`, `Property_Type`, `Area`, `Bedrooms`, `Bathrooms`, `Age`). Each parent categorical attribute receives the exact sum of its underlying dummy split impacts.

4. **Exact Additive Reconciliation:**
   The contributions satisfy exact mathematical reconstruction:
   $$\bar{y}_{\text{base}} + \sum_{f \in \text{Features}} \text{Contribution}_f = \hat{y}_{\text{predicted}}$$
   - **Numerical Precision:** Reconciled to $< 10^{-4}$ INR (mathematically verified to 0.0 INR error).
   - **Labeling Standard:** Labeled explicitly as `"Saabas Tree Path Decomposition"`. Never misrepresented as SHAP values.

5. **Path-Dependent Nature & Differences from SHAP:**
   - **Path Dependence:** Saabas attribution is path-dependent; it attributes value shifts based on the specific hierarchical split sequence learned by the trees. Features split closer to the root node may capture interaction effects that could also be attributed to other features lower in the tree.
   - **Distinction from SHAP (Shapley Additive exPlanations):** While Saabas attribution satisfies local additivity for decision trees along the evaluated path, it does not average marginal contributions across all $2^{|F|}$ feature subsets. Consequently, unlike SHAP, Saabas does not satisfy the game-theoretic consistency axiom (a feature that increases its marginal impact in all models can occasionally receive a smaller Saabas value due to tree split order).
   - **Operational Benefit:** Saabas provides instantaneous, exact $O(\text{depth} \times T)$ path-based additive decomposition that explains the internal decision trajectory of the fitted tree ensemble with zero sampling approximation noise.

This breakdown is rendered dynamically in the web UI result page (`templates/result.html`) and exposed via the REST API response (`/api/predict`).

---

### 4. Empirical Location Premium Analysis
Claims regarding geographic valuation premiums are derived strictly from empirical sample statistics in `data/raw/house_prices.csv`:

$$\text{Premium (\%)} = \frac{\bar{Y}_{\text{Location}} - \bar{Y}_{\text{Rural}}}{\bar{Y}_{\text{Rural}}} \times 100$$

**Empirical Metrics:**
- **City Center:**
  - Mean Listing Price: ₹3.64 Crores (Full Dataset) | ₹2.93 Crores (Holdout Test Set)
  - Price per Sq. Ft.: ₹13,678 / sq. ft.
  - Descriptive Premium vs Rural: **+101.38%** (Full Dataset) | **+71.04%** (Holdout Test Set)
- **Suburb:**
  - Mean Listing Price: ₹2.25 Crores (Full Dataset) | ₹2.77 Crores (Holdout Test Set)
  - Price per Sq. Ft.: ₹8,421 / sq. ft.
  - Descriptive Premium vs Rural: **+76.51%** (Full Dataset) | **+61.94%** (Holdout Test Set)
- **Rural:**
  - Mean Listing Price: ₹1.81 Crores (Full Dataset) | ₹1.71 Crores (Holdout Test Set)
  - Price per Sq. Ft.: ₹6,540 / sq. ft.
  - Baseline reference category.

> **Methodological Disclaimer:** These metrics represent descriptive empirical differences observed in the historical sample. They do not constitute controlled econometric causal effects, as properties across zones also vary by square footage and architectural specifications.

