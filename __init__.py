"""
Flask Application Factory Module
Constructs and configures the Flask application, registers blueprints,
applies security response headers, and initializes database tables.
"""
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from config.config import get_config, Config
from config.logging_config import setup_logger
from app.database import init_db

logger = setup_logger("app_factory")

def create_app(config_class=None) -> Flask:
    """Application factory for House Price Prediction System."""
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )
    
    if config_class is None:
        config_class = get_config()
        
    app.config.from_object(config_class)
    
    # Restrict CORS to configured origins (no wildcard fallback)
    origins = getattr(config_class, "CORS_ORIGINS", None) or ["http://localhost:5000", "http://127.0.0.1:5000"]
    CORS(app, resources={r"/api/*": {"origins": origins}})
    
    # Initialize Database Schema
    try:
        init_db()
    except Exception as e:
        logger.error(f"Database initialization failure: {e}", exc_info=True)

    # Register Blueprints
    from app.routes import web_bp
    from app.api_routes import api_bp
    
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)
    
    # Security Response Headers
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
    
    # Centralized Secure Error Handlers
    @app.errorhandler(400)
    def bad_request(e):
        if request_wants_json():
            return jsonify({"status": "error", "message": "Bad Request: Malformed payload or syntax."}), 400
        return render_template("base.html", error_message="400 - Bad Request"), 400

    @app.errorhandler(404)
    def not_found(e):
        if request_wants_json():
            return jsonify({"status": "error", "message": "Endpoint or resource not found."}), 404
        return render_template("base.html", error_message="404 - Resource Not Found"), 404

    @app.errorhandler(422)
    def unprocessable_entity(e):
        if request_wants_json():
            return jsonify({"status": "error", "message": "Unprocessable Entity: Validation rules violated."}), 422
        return render_template("base.html", error_message="422 - Unprocessable Entity"), 422

    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"Internal server error: {e}", exc_info=True)
        if request_wants_json():
            return jsonify({"status": "error", "message": "Internal Server Error. Please consult server logs."}), 500
        return render_template("base.html", error_message="500 - Internal Server Error"), 500

    return app

def request_wants_json():
    return request.path.startswith("/api/") or request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']
