"""
REST API Blueprint for House Price Prediction System
Implements enterprise-grade JSON endpoints with validation, dynamic explainability,
and conformal prediction intervals.
"""
from datetime import datetime
from typing import Any, Dict, List
from flask import Blueprint, jsonify, request, current_app
from src.model_inference import get_predictor
from src.model_registry import ModelRegistry
from app.validators import validate_prediction_payload
from app.database import (
    insert_prediction, get_recent_predictions, get_prediction_by_id, get_prediction_count
)
from config.logging_config import setup_logger

logger = setup_logger("api_routes")
api_bp = Blueprint("api", __name__, url_prefix="/api")

def sanitize_for_json(obj: Any) -> Any:
    """Recursively converts numpy numbers/arrays to standard Python types for JSON serialization."""
    if hasattr(obj, "item"):
        return obj.item()
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(v) for v in obj]
    return obj

@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint indicating API operational status and model availability."""
    predictor = get_predictor()
    model_loaded = predictor.pipeline is not None
    return jsonify({
        "status": "healthy" if model_loaded else "degraded",
        "service": "House Price Prediction API",
        "timestamp": datetime.now().isoformat(),
        "model_available": model_loaded,
        "active_version": predictor.metadata.get("version", "unknown") if predictor.metadata else None,
        "version": "1.0.0"
    }), 200 if model_loaded else 503

@api_bp.route("/model-info", methods=["GET"])
def model_info():
    """Returns metadata, schema constraints, and hyperparameters of active production model."""
    predictor = get_predictor()
    if not predictor.metadata:
        return jsonify({"status": "error", "message": "No active model metadata available."}), 404
        
    return jsonify({
        "status": "success",
        "metadata": predictor.metadata
    }), 200

@api_bp.route("/predict", methods=["POST"])
def predict():
    """
    Predicts residential property price based on validated input attributes.
    Returns point estimate, statistically calibrated conformal prediction intervals (90%),
    and persists prediction record into SQLite audit log.
    """
    if not request.is_json:
        return jsonify({"status": "error", "message": "Payload must be JSON with Content-Type: application/json"}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"status": "error", "message": "Malformed or empty JSON in request body."}), 400

    is_valid, error_msg, sanitized = validate_prediction_payload(data)
    if not is_valid:
        return jsonify({"status": "error", "message": error_msg}), 422

    predictor = get_predictor()
    try:
        result = predictor.predict(sanitized)
        interval = result.get("prediction_interval", {})
        
        # Log to SQLite
        pred_id = insert_prediction(
            area=sanitized["Area"],
            bedrooms=sanitized["Bedrooms"],
            bathrooms=sanitized["Bathrooms"],
            age=sanitized["Age"],
            location=sanitized["Location"],
            property_type=sanitized["Property_Type"],
            predicted_price=result["predicted_price"],
            formatted_price=result["formatted_price"],
            model_version=result["model_version"],
            input_payload=sanitized,
            conformal_lower=interval.get("lower_bound", 0.0),
            conformal_upper=interval.get("upper_bound", 0.0)
        )
        result["prediction_id"] = pred_id
        
        return jsonify({
            "status": "success",
            "data": sanitize_for_json(result)
        }), 200
    except Exception as e:
        logger.error(f"Prediction inference error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Inference execution failed. Please verify input data."}), 500

@api_bp.route("/metrics", methods=["GET"])
def metrics():
    """Returns unbiased 3-stage evaluation metrics of the active production model."""
    predictor = get_predictor()
    if not predictor.metadata:
        return jsonify({"status": "error", "message": "No model metadata found."}), 404
        
    return jsonify({
        "status": "success",
        "model_name": predictor.metadata.get("model_name"),
        "version": predictor.metadata.get("version"),
        "metrics": predictor.metadata.get("metrics", {}),
        "conformal_calibration": predictor.metadata.get("conformal_calibration", {})
    }), 200

@api_bp.route("/feature-importance", methods=["GET"])
def feature_importance():
    """
    Returns dynamically computed permutation feature importance from untouched holdout test set
    and native tree-based feature importance. Zero hardcoding.
    """
    predictor = get_predictor()
    metadata = predictor.metadata or {}
    feat_imp = metadata.get("feature_importance", {})
    
    perm_rankings = feat_imp.get("permutation_importance", [])
    tree_rankings = feat_imp.get("tree_importance", [])
    location_premiums = feat_imp.get("location_premiums", {})
    
    return jsonify({
        "status": "success",
        "active_version": metadata.get("version", "v1"),
        "model_name": metadata.get("model_name", "Gradient Boosting"),
        "rankings": perm_rankings,
        "permutation_importance": perm_rankings,
        "tree_importance": tree_rankings,
        "empirical_location_premiums": location_premiums
    }), 200

@api_bp.route("/predictions", methods=["GET"])
def list_predictions():
    """Returns paginated historical predictions with deterministic sorting."""
    try:
        limit = min(int(request.args.get("limit", 20)), 100)
        offset = max(int(request.args.get("offset", 0)), 0)
    except ValueError:
        return jsonify({"status": "error", "message": "Limit and offset must be non-negative integers."}), 400

    items = get_recent_predictions(limit=limit, offset=offset)
    total = get_prediction_count()

    return jsonify({
        "status": "success",
        "total_records": total,
        "limit": limit,
        "offset": offset,
        "predictions": items
    }), 200

@api_bp.route("/predictions/<int:prediction_id>", methods=["GET"])
def get_prediction(prediction_id: int):
    """Returns a single historical prediction record by ID."""
    record = get_prediction_by_id(prediction_id)
    if not record:
        return jsonify({"status": "error", "message": f"Prediction ID {prediction_id} not found."}), 404
        
    return jsonify({
        "status": "success",
        "prediction": record
    }), 200
