import sys, os
sys.path.insert(0, 'app')
from app import app
client = app.test_client()
routes = ['/', '/predict', '/results', '/about']
for r in routes:
    resp = client.get(r)
    print(f'{r} => {resp.status_code}')

import json
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
r = client.post('/api/predict',
    data=json.dumps({'model':'random_forest','features':features}),
    content_type='application/json')
print(f'/api/predict => {r.status_code}')
print(json.loads(r.data))
