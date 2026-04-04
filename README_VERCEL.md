# SmartHealth AI - Vercel Serverless Integration
### Author: Enock Queenson Eduafo (11014444)
---
### Deployment Steps (Vercel CLI)
1. Install Vercel CLI: `npm install -g vercel`
2. Link project: `vercel link`
3. Deploy to production: `vercel --prod`

### API Usage (POST /predict)
```bash
curl -X POST https://your-vercel-domain.vercel.app/predict \
     -H "Content-Type: application/json" \
     -d '{
           "features": {
             "Glucose": 0.52,
             "Cholesterol": 0.48,
             "Hemoglobin": 0.5,
             "Platelets": 0.45,
             "White Blood Cells": 0.42,
             "Red Blood Cells": 0.48,
             "Hematocrit": 0.55,
             "Mean Corpuscular Volume": 0.52,
             "Mean Corpuscular Hemoglobin": 0.48,
             "Mean Corpuscular Hemoglobin Concentration": 0.5,
             "Insulin": 0.45,
             "BMI": 0.42,
             "Systolic Blood Pressure": 0.48,
             "Diastolic Blood Pressure": 0.55,
             "Triglycerides": 0.52,
             "HbA1c": 0.48,
             "LDL Cholesterol": 0.5,
             "HDL Cholesterol": 0.45,
             "ALT": 0.42,
             "AST": 0.48,
             "Heart Rate": 0.55,
             "Creatinine": 0.52,
             "Troponin": 0.48,
             "C-reactive Protein": 0.5
           }
         }'
```

### Common Errors:
- **ModuleNotFoundError: joblib**: Ensure `joblib` is in requirements.txt.
- **Payload Too Large**: Vercel has a 4.5MB limit on request size (not applicable for this small feature JSON).
- **Function Timeout**: Cold starts with model loading might take a second. Vercel's default is 10s (plenty for this 6MB model).
- **Paths**: Ensure `models/` directory is in the root of your Vercel deployment.
