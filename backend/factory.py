"""
Smart Health Sync — Flask Application Factory
Author: Enock Queenson Eduafo | University of Ghana 2026
"""

import logging
import os
from flask import Flask
from flask_cors import CORS

from backend.config import get_config


def configure_logging(level: str = "INFO"):
    """Set up structured logging for the application."""
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_app() -> Flask:
    """Application factory — returns a fully configured Flask instance."""
    cfg = get_config()
    configure_logging(cfg.LOG_LEVEL)
    log = logging.getLogger("smarthealth.factory")

    # ── Create Flask app pointing to legacy templates/static ──
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "app", "templates"),
        static_folder=os.path.join(base_dir, "static"),
        static_url_path="/static",
    )
    app.config["SECRET_KEY"] = cfg.SECRET_KEY
    app.config["DEBUG"]      = cfg.DEBUG

    # ── CORS ──────────────────────────────────────────────────
    CORS(app, resources={r"/api/*": {"origins": cfg.CORS_ORIGINS}})

    # ── Register blueprints ───────────────────────────────────
    from backend.api.routes import api_bp
    from backend.api.views  import views_bp
    app.register_blueprint(api_bp,   url_prefix="/api")
    app.register_blueprint(views_bp, url_prefix="")

    log.info(f"[SmartHealth] App created — ENV={cfg.FLASK_ENV}, DEBUG={cfg.DEBUG}")
    return app
