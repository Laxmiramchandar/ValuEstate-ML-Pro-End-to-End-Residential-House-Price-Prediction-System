# Dataset Storage & Integrity Guidelines

## 1. Directory Structure
```
data/
├── raw/
│   └── house_prices.csv        # Immutable original dataset
├── processed/
│   └── house_prices_cleaned.csv# Cleaned dataset (Property_ID decoupled, validated)
└── README.md                   # This file
```

## 2. Integrity Rules
- The raw dataset in `data/raw/` must NEVER be edited in place. It serves as the immutable ground truth.
- All cleaning, outlier filtering, and feature encoding pipelines are defined programmatically via `src/data_preprocessing.py`.
- Data splitting occurs before any fit operations on transformers to guarantee zero data leakage between training and evaluation splits.

