
import urllib.request
import json
import time

base = 'http://localhost:5000'

# Give the server a moment to start if run concurrently
# time.sleep(5) 

# Test all pages
for path in ['/', '/predict', '/results', '/about']:
    try:
        r = urllib.request.urlopen(base + path)
        print(f'PASS {path} — {r.status}')
    except Exception as e:
        print(f'FAIL {path} — {e}')

# Test the prediction API
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
payload = json.dumps({'model': 'random_forest', 'features': features}).encode()
req = urllib.request.Request(
    base + '/api/predict',
    data=payload,
    headers={'Content-Type': 'application/json'},
    method='POST'
)
try:
    r = urllib.request.urlopen(req)
    data = json.loads(r.read())
    print(f'PASS /api/predict — prediction: {data.get("prediction")} confidence: {data.get("confidence")}')
except Exception as e:
    print(f'FAIL /api/predict — {e}')
