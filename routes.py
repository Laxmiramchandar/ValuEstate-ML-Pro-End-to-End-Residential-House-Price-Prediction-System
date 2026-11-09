"""
Web Application Routes
Renders responsive user-facing templates for dashboard, prediction form,
results, model metrics, explainability, history, and educational insights.
Integrates Conformal Prediction intervals and dynamic local feature explanations.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import pandas as pd
from src.model_inference import get_predictor, format_inr_currency
from src.model_explainability import explain_single_prediction
from app.validators import validate_prediction_payload
from app.database import (
    insert_prediction, get_recent_predictions, get_prediction_count, get_prediction_by_id
)
from config.config import Config
from config.logging_config import setup_logger

logger = setup_logger("web_routes")
web_bp = Blueprint("web", __name__)

@web_bp.route("/")
def index():
    """Home Dashboard Page."""
    predictor = get_predictor()
    total_preds = get_prediction_count()
    recent_activity = get_recent_predictions(limit=5)
    
    meta = predictor.metadata or {}
    metrics = meta.get("metrics", {})
    
    return render_template(
        "index.html",
        total_predictions=total_preds,
        recent_activity=recent_activity,
        model_name=meta.get("model_name", "Gradient Boosting"),
        model_version=meta.get("version", "v1"),
        metrics=metrics,
        last_updated=meta.get("created_at", "Recently")
    )

@web_bp.route("/predict", methods=["GET", "POST"])
def predict():
    """Interactive House Price Prediction Form."""
    predictor = get_predictor()
    bounds = Config.FEATURE_CONSTRAINTS
    
    if request.method == "POST":
        form_data = {
            "Area": request.form.get("area"),
            "Bedrooms": request.form.get("bedrooms"),
            "Bathrooms": request.form.get("bathrooms"),
            "Age": request.form.get("age"),
            "Location": request.form.get("location"),
            "Property_Type": request.form.get("property_type")
        }
        
        is_valid, error_msg, sanitized = validate_prediction_payload(form_data)
        if not is_valid:
            flash(error_msg, "danger")
            return render_template("predict.html", bounds=bounds, prev=form_data)
            
        try:
            result = predictor.predict(sanitized)
            interval = result.get("prediction_interval", {})
            
            # Save in SQLite with conformal prediction bounds
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
            return redirect(url_for("web.result", prediction_id=pred_id))
        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            flash(f"Error calculating price: {str(e)}", "danger")
            return render_template("predict.html", bounds=bounds, prev=form_data)
            
    return render_template("predict.html", bounds=bounds, prev={})

@web_bp.route("/result/<int:prediction_id>")
def result(prediction_id: int):
    """Detailed Prediction Result Page with Conformal Prediction Interval."""
    record = get_prediction_by_id(prediction_id)
    if not record:
        flash(f"Prediction record #{prediction_id} not found.", "warning")
        return redirect(url_for("web.predict"))
        
    predictor = get_predictor()
    meta = predictor.metadata or {}
    metrics = meta.get("metrics", {})
    conformal_meta = meta.get("conformal_calibration", {})
    
    price = record["predicted_price"]
    
    # Conformal prediction interval
    conf_lower = record.get("conformal_lower_bound") or (price - conformal_meta.get("quantile_q_inr", 2159600.0))
    conf_upper = record.get("conformal_upper_bound") or (price + conformal_meta.get("quantile_q_inr", 2159600.0))
    conf_lower = max(0.0, conf_lower)
    
    formatted_lower, _ = format_inr_currency(conf_lower)
    formatted_upper, _ = format_inr_currency(conf_upper)
    half_width_inr = conformal_meta.get("quantile_q_inr", 2159600.08)
    nominal_cov = conformal_meta.get("nominal_coverage_pct", 90.0)
    
    # Dynamic local feature attribution
    sample_df = pd.DataFrame([{
        "Area": record["property_area"],
        "Bedrooms": record["bedrooms"],
        "Bathrooms": record["bathrooms"],
        "Age": record["age"],
        "Location": record["location"],
        "Property_Type": record["property_type"]
    }])
    
    local_explanation = None
    if predictor.pipeline:
        try:
            local_explanation = explain_single_prediction(predictor.pipeline, sample_df, predictor.background_df)
        except Exception as e:
            logger.warning(f"Local explanation calculation error: {e}")
    
    return render_template(
        "result.html",
        record=record,
        meta=meta,
        metrics=metrics,
        conformal_lower=formatted_lower,
        conformal_upper=formatted_upper,
        half_width_inr=half_width_inr,
        nominal_coverage_pct=nominal_cov,
        local_explanation=local_explanation
    )

@web_bp.route("/performance")
def performance():
    """Model Performance and Diagnostic Charts Page."""
    predictor = get_predictor()
    meta = predictor.metadata or {}
    metrics = meta.get("metrics", {})
    
    return render_template(
        "performance.html",
        model_name=meta.get("model_name", "Gradient Boosting"),
        model_version=meta.get("version", "v1"),
        metrics=metrics
    )

@web_bp.route("/explainability")
def explainability():
    """Model Interpretability & Feature Drivers Page with Dynamic Data."""
    predictor = get_predictor()
    meta = predictor.metadata or {}
    feat_meta = meta.get("feature_importance", {})
    
    perm_importances = feat_meta.get("permutation_importance", [])
    tree_importances = feat_meta.get("tree_importance", [])
    location_premiums = feat_meta.get("location_premiums", {})
    
    return render_template(
        "explainability.html",
        model_name=meta.get("model_name", "Gradient Boosting"),
        permutation_importances=perm_importances,
        tree_importances=tree_importances,
        location_premiums=location_premiums
    )

@web_bp.route("/history")
def history():
    """Prediction History Audit Trail Page with Deterministic Sorting."""
    page = max(int(request.args.get("page", 1)), 1)
    per_page = 10
    offset = (page - 1) * per_page
    
    total = get_prediction_count()
    records = get_recent_predictions(limit=per_page, offset=offset)
    total_pages = max(1, (total + per_page - 1) // per_page)
    
    return render_template(
        "history.html",
        records=records,
        page=page,
        total_pages=total_pages,
        total_records=total
    )

@web_bp.route("/about")
def about():
    """About Project & Architectural Details Page."""
    return render_template("about.html")

@web_bp.route("/educational")
def educational():
    """Educational Machine Learning Foundations Page."""
    return render_template("educational.html")
