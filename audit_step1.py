import sys, os
import json

# Ensure app is in path
sys.path.insert(0, os.path.join(os.getcwd(), 'app'))

try:
    from app import app
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

client = app.test_client()
routes = ['/', '/predict', '/results', '/about']

print("Checking routes:")
for r in routes:
    try:
        resp = client.get(r)
        print(f"{r} => {resp.status_code}")
    except Exception as e:
        print(f"{r} => ERROR: {e}")

features = {f: 0.5 for f in [
    'Glucose','Cholesterol','Hemoglobin','Platelets',
    'White Blood Cells','Red Blood Cells','Hematocrit',
    'Mean Corpuscular Volume','Mean Corpuscular Hemoglobin',
    'Mean Corpuscular Hemoglobin Concentration','Insulin',
    'BMI','Systolic Blood Pressure','Diastolic Blood Pressure',
    'Triglycerides','HbA1c','LDL Cholesterol','HDL Cholesterol',
    'ALT','AST','Heart Rate','Creatinine','Troponin',
    'C-reactive Protein'
]}

print("\nChecking /api/predict:")
try:
    r = client.post('/api/predict',
        data=json.dumps({'model':'random_forest','features':features}),
        content_type='application/json')
    print(f"/api/predict => {r.status_code}")
    print(json.loads(r.data))
except Exception as e:
    print(f"/api/predict => ERROR: {e}")
