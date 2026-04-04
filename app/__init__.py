# =============================================================
# SmartHealth AI - App Factory Pattern
# Author:      Enock Queenson Eduafo
# Student ID:  11014444
# Institution: University of Ghana (2026)
# =============================================================

from flask import Flask
from .routes import api_bp

def create_app():
    """Flask app factory for serverless Vercel deployment."""
    app = Flask(__name__)
    
    # Optional configurations for deployment environment
    # app.config['DEBUG'] = False
    
    # Register blueprints for modular routing
    app.register_blueprint(api_bp)
    
    return app
