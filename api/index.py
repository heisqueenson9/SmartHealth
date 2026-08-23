import os
import sys

# Add project root directory to sys.path so backend imports resolve cleanly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from main import app

# Export Flask WSGI application instance for Vercel Serverless Function
app = app
