# REST API Documentation

## Base URL
`http://localhost:5000/api`

---

## 1. Health Check
- **Endpoint:** `GET /health`
- **Description:** Verifies application and active model availability.
- **Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "House Price Prediction API",
  "timestamp": "2026-11-07T11:08:00.000",
  "model_available": true,
  "active_version": "v1",
  "version": "1.0.0"
}
```

---

## 2. Model Metadata
- **Endpoint:** `GET /model-info`
- **Description:** Returns production model hyperparameters, schema constraints, and metrics.
- **Response (200 OK):**
```json
{
  "status": "success",
  "metadata": {
    "version": "v1",
    "model_name": "Gradient Boosting",
    "dataset_fingerprint": "...",
    "metrics": {
      "Test_R2": 0.9918,
      "Test_RMSE": 1078547.58
    }
  }
}
```

---

## 3. Predict Property Price
- **Endpoint:** `POST /predict`
- **Headers:** `Content-Type: application/json`
- **Request Body Example:**
```json
{
  "Area": 3200,
  "Bedrooms": 4,
  "Bathrooms": 3,
  "Age": 8,
  "Location": "City Center",
  "Property_Type": "Villa"
}
```
- **Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "prediction_id": 1,
    "predicted_price": 42500000.0,
    "formatted_price": "₹4,25,00,000",
    "formatted_inr_words": "₹4.25 Crores",
    "model_version": "v1",
    "model_name": "Gradient Boosting",
    "input_features": {
      "Area": 3200.0,
      "Bedrooms": 4,
      "Bathrooms": 3,
      "Age": 8.0,
      "Location": "City Center",
      "Property_Type": "Villa"
    }
  }
}
```
- **Error Response (422 Unprocessable Entity):**
```json
{
  "status": "error",
  "message": "Area (50) must be between 200 and 15000 sq ft."
}
```

---

## 4. Model Evaluation Metrics
- **Endpoint:** `GET /metrics`
- **Response (200 OK):**
```json
{
  "status": "success",
  "model_name": "Gradient Boosting",
  "version": "v1",
  "metrics": {
    "Test_R2": 0.9918,
    "Test_RMSE": 1078547.58,
    "Test_MAE": 777199.15,
    "Test_MAPE": 3.75,
    "CV_R2_Mean": 0.9915
  }
}
```

---

## 5. Feature Importance Rankings
- **Endpoint:** `GET /feature-importance`
- **Response (200 OK):**
```json
{
  "status": "success",
  "active_version": "v1",
  "rankings": [
    {"feature": "Area", "importance_score": 0.725, "impact": "Primary value driver"},
    {"feature": "Location", "importance_score": 0.185, "impact": "Urban tier premium"},
    {"feature": "Age", "importance_score": 0.052, "impact": "Structural depreciation"}
  ]
}
```

---

## 6. Prediction History
- **Endpoint:** `GET /predictions?limit=10&offset=0`
- **Response (200 OK):**
```json
{
  "status": "success",
  "limit": 10,
  "offset": 0,
  "total_records": 45,
  "predictions": [...]
}
```

