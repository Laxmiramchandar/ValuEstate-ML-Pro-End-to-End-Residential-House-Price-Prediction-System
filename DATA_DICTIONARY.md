# Comprehensive Data Dictionary

## Overview
This document specifies the exact schema, statistical properties, domain constraints, and semantics of every variable within the **House Price Prediction System** dataset (`house_prices.csv`).

---

## Detailed Variable Specifications

### 1. `Property_ID`
- **Description:** Unique synthetic string identifier assigned to each real estate asset.
- **Data Type:** `object` (string)
- **Role:** Non-predictive unique record identifier.
- **Example Values:** `PROP0001`, `PROP0002`, ..., `PROP0300`
- **Cardinality:** 300 unique entries (100% unique).
- **Missing Values:** 0 (0.0%).
- **Preprocessing Action:** Dropped from feature matrix before model training to eliminate identifier-based overfitting.

---

### 2. `Area`
- **Description:** Total built-up / livable floor area of the property.
- **Unit of Measurement:** Square Feet (sq ft).
- **Data Type:** `int64` (Continuous numeric)
- **Role:** Primary predictive feature.
- **Statistical Summary:**
  - Minimum: 520.00 sq ft
  - 25th Percentile: 1,675.75 sq ft
  - Median (50th): 2,738.00 sq ft
  - Mean: 2,759.70 sq ft
  - 75th Percentile: 3,801.25 sq ft
  - Maximum: 4,999.00 sq ft
  - Standard Deviation: 1,297.68 sq ft
- **Correlation with Price:** **+0.7963** (Dominant positive linear driver).
- **Domain Constraints:** Must be strictly positive ($200 \le \text{Area} \le 15000$).
- **Preprocessing Action:** Imputation safeguard (median) followed by standard scaling (`StandardScaler`) where appropriate for linear and distance-based estimators.

---

### 3. `Bedrooms`
- **Description:** Number of dedicated bedrooms in the property.
- **Unit of Measurement:** Room count.
- **Data Type:** `int64` (Discrete numeric)
- **Role:** Secondary predictive feature.
- **Statistical Summary:**
  - Minimum: 1
  - 25th Percentile: 2
  - Median (50th): 3
  - Mean: 3.03
  - 75th Percentile: 4
  - Maximum: 5
  - Standard Deviation: 1.47
- **Correlation with Price:** **+0.2025** (Moderate positive driver).
- **Domain Constraints:** Positive integer ($1 \le \text{Bedrooms} \le 10$).
- **Preprocessing Action:** Median imputation fallback and scaling.

---

### 4. `Bathrooms`
- **Description:** Number of full bathrooms within the residential structure.
- **Unit of Measurement:** Room count.
- **Data Type:** `int64` (Discrete numeric)
- **Role:** Predictive feature.
- **Statistical Summary:**
  - Minimum: 1
  - 25th Percentile: 1
  - Median (50th): 2
  - Mean: 2.03
  - 75th Percentile: 3
  - Maximum: 3
  - Standard Deviation: 0.79
- **Correlation with Price:** **-0.0303** (Near zero direct linear correlation; non-linear interactions).
- **Domain Constraints:** Positive integer ($1 \le \text{Bathrooms} \le 10$).
- **Preprocessing Action:** Median imputation fallback and scaling.

---

### 5. `Age`
- **Description:** Chronological age of the building since construction completion.
- **Unit of Measurement:** Years.
- **Data Type:** `int64` (Continuous/Discrete numeric)
- **Role:** Predictive feature (Depreciation indicator).
- **Statistical Summary:**
  - Minimum: 0 years (brand new construction)
  - 25th Percentile: 12.00 years
  - Median (50th): 25.50 years
  - Mean: 25.00 years
  - 75th Percentile: 36.25 years
  - Maximum: 49.00 years
  - Standard Deviation: 14.33 years
- **Correlation with Price:** **-0.1308** (Negative linear association indicating structural depreciation over time).
- **Domain Constraints:** Non-negative integer ($0 \le \text{Age} \le 120$).
- **Preprocessing Action:** Median imputation fallback and scaling.

---

### 6. `Location`
- **Description:** Macro-geographic classification of the property site.
- **Data Type:** `object` (Nominal categorical)
- **Role:** Key predictive categorical feature.
- **Allowed Categories & Frequencies:**
  - `Suburb`: 105 properties (35.0%) — Average Price: ₹25,108,071
  - `Rural`: 98 properties (32.7%) — Average Price: ₹16,461,429
  - `City Center`: 97 properties (32.3%) — Average Price: ₹33,149,794
- **Economic Insight:** Prime urban location (`City Center`) commands a ~101% average price premium over `Rural` locations.
- **Preprocessing Action:** Most frequent imputation fallback and One-Hot Encoding (`OneHotEncoder(handle_unknown='ignore')`).

---

### 7. `Property_Type`
- **Description:** Structural zoning and building typology classification.
- **Data Type:** `object` (Nominal categorical)
- **Role:** Key predictive categorical feature.
- **Allowed Categories & Frequencies:**
  - `House`: 107 properties (35.7%) — Average Price: ₹22,876,916
  - `Villa`: 102 properties (34.0%) — Average Price: ₹24,989,853
  - `Apartment`: 91 properties (30.3%) — Average Price: ₹27,124,176
- **Preprocessing Action:** Most frequent imputation fallback and One-Hot Encoding (`OneHotEncoder(handle_unknown='ignore')`).

---

### 8. `Price` (Target Variable)
- **Description:** Final transaction / market valuation price of the property.
- **Currency:** Indian Rupee (INR ₹).
- **Data Type:** `int64` (Continuous numeric)
- **Role:** Regression Target ($y$).
- **Statistical Summary:**
  - Minimum: ₹3,695,000 (36.95 Lakhs)
  - 25th Percentile: ₹15,277,500 (1.53 Crores)
  - Median (50th): ₹22,365,000 (2.24 Crores)
  - Mean: ₹24,883,658 (2.49 Crores)
  - 75th Percentile: ₹34,608,125 (3.46 Crores)
  - Maximum: ₹58,700,000 (5.87 Crores)
  - Standard Deviation: ₹12,665,255
  - Skewness: ~0.43 (Mild positive skewness, well-behaved for regression).
- **Transformation Note:** The target is preserved in its natural currency unit to ensure transparent error metrics (MAE in ₹), avoiding synthetic log distortion while ensuring ease of interpretability for business stakeholders.

