import sys, os
d = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if d not in sys.path: sys.path.insert(0, d)
from app.app import app
