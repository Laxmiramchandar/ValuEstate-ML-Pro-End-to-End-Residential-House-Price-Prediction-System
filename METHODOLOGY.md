# Machine Learning Methodology & Engineering Lifecycle

## 1. Lifecycle Overview
The **House Price Prediction System** adheres strictly to production-grade CRISP-DM and MLOps principles, encompassing:
1. **Business Problem Alignment:** Identifying stakeholders, objectives, and tolerance thresholds.
2. **Dataset Audit & Sanitation:** Ground-truth audit of raw features and verification of non-negative bounds.
3. **Leak-Free Partitioning:** Splitting 80% train / 20% test holdout BEFORE fitting any preprocessing transformers.
4. **Scikit-Learn Pipeline Preprocessing:** Encapsulating median imputation, scaling, and categorical one-hot encoding.
5. **Algorithm Exploration & Hyperparameter Tuning:** Systematic search across linear, tree, bagging, boosting, and ensemble estimators using 5-fold cross-validation.
6. **Model Registry & Persistence:** Storing complete pipelines, SHA-256 dataset hashes, and manifest metadata via Joblib.
7. **REST API & Web Interface:** Low-latency JSON inference and interactive UI.
8. **Explainability & Transparency:** Test-set permutation importance, tree impurity importance, and local counterfactual breakdowns.

---

## 2. Preventing Data Leakage
Data leakage occurs when information outside the training dataset is inadvertently used to create the model. In this project:
- Train-test splitting is executed as step 1 in `src/data_preprocessing.py`.
- Transformers (`SimpleImputer`, `StandardScaler`, `OneHotEncoder`) are fit strictly on the training partition (`X_train`).
- The test holdout set (`X_test`) is exclusively used for final evaluation and remains untouched during hyperparameter optimization.
- No target-derived features (such as price per square foot) are supplied as inputs to any predictive model.

---

## 3. Mathematical Formulations

### Ordinary Least Squares (OLS) Linear Regression
Given feature matrix $X \in \mathbb{R}^{m \times (n+1)}$ and target vector $y \in \mathbb{R}^m$, the closed-form solution minimizing sum of squared residuals is:
$$\theta = (X^T X)^{-1} X^T y$$

### Gradient Boosting Regression
Sequential additive expansion minimizing squared error loss:
$$F_0(x) = \arg\min_\gamma \sum_{i=1}^m L(y_i, \gamma)$$
For each stage $m = 1, \dots, M$:
1. Compute pseudo-residuals:
$$r_{im} = -\left[ \frac{\partial L(y_i, F(x_i))}{\partial F(x_i)} \right]_{F(x) = F_{m-1}(x)} = y_i - F_{m-1}(x_i)$$
2. Fit a regression tree $h_m(x)$ to residuals $r_{im}$.
3. Update model with shrinkage learning rate $\eta$:
$$F_m(x) = F_{m-1}(x) + \eta h_m(x)$$

