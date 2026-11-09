# Troubleshooting & Operational Guide

## 1. Common Issues and Resolutions

### Issue 1: `FileNotFoundError: No active model found in registry.`
- **Cause:** Model training script has not been executed yet.
- **Resolution:** Run the automated training pipeline:
  ```bash
  python scripts/train_model.py
  ```

### Issue 2: `422 Unprocessable Entity` on API prediction
- **Cause:** Input values violate domain boundaries (e.g. area < 200, negative age, invalid location).
- **Resolution:** Verify payload matches schema in `docs/DATA_DICTIONARY.md`:
  - Area: 200 to 15,000 sq ft
  - Bedrooms: 1 to 10
  - Bathrooms: 1 to 10
  - Age: 0 to 120
  - Location: `City Center`, `Suburb`, `Rural`
  - Property_Type: `Apartment`, `House`, `Villa`

### Issue 3: SQLite Database Locked Error
- **Cause:** Concurrent write contention or unclosed cursor.
- **Resolution:** The database module uses context managers (`with get_connection() as conn:`) ensuring immediate commit and close. For high concurrency, SQLite WAL mode can be enabled:
  ```bash
  python -c "import sqlite3; conn=sqlite3.connect('instance/house_prices.sqlite'); conn.execute('PRAGMA journal_mode=WAL;'); conn.close()"
  ```

