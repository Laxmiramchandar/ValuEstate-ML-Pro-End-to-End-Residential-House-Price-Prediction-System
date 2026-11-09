"""
Application Entrypoint
Run locally via: python run.py
Run production via: gunicorn --bind 0.0.0.0:5000 run:app
"""
import os
from app import create_app
from config.config import get_config

config = get_config()
app = create_app(config)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1")
    print(f"\n=======================================================")
    print(f" HOUSE PRICE PREDICTION SYSTEM - ENTERPRISE SERVER")
    print(f" Environment : {os.getenv('FLASK_ENV', 'development')}")
    print(f" URL         : http://127.0.0.1:{port}")
    print(f" API Docs    : http://127.0.0.1:{port}/api/health")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=debug)

