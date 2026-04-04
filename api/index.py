# =============================================================
# SmartHealth AI - Vercel Serverless Entry Point
# Author:      Enock Queenson Eduafo
# Student ID:  11014444
# Institution: University of Ghana (2026)
# =============================================================

from app import create_app

# Vercel's Python runtime searches for a variable named 'app'
# This is our production-ready WSGI application
app = create_app()

# This is NOT called by Vercel's serverless runtime
if __name__ == '__main__':
    app.run(debug=True)
