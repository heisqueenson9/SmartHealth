# =============================================================
# SmartHealth AI - Model Training Script
# Author:      Enock Queenson Eduafo
# Student ID:  11014444
# Institution: University of Ghana
# Department:  Computer Science - Information Technology
# Supervisor:  Professor Solomon Mensah
# Year:        2026
#
# Description: Trains and evaluates four machine learning
# classifiers on patient health data to predict disease
# conditions. Run this script once before starting the app.
# =============================================================

import os, sys, json, shutil, warnings
import numpy as np, pandas as pd, joblib
warnings.filterwarnings('ignore')

from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data')
MDLS = os.path.join(BASE, 'models')
os.makedirs(MDLS, exist_ok=True)

# List of biomarkers used as inputs for the models
FEATURES = [
    'Glucose','Cholesterol','Hemoglobin','Platelets','White Blood Cells',
    'Red Blood Cells','Hematocrit','Mean Corpuscular Volume',
    'Mean Corpuscular Hemoglobin','Mean Corpuscular Hemoglobin Concentration',
    'Insulin','BMI','Systolic Blood Pressure','Diastolic Blood Pressure',
    'Triglycerides','HbA1c','LDL Cholesterol','HDL Cholesterol',
    'ALT','AST','Heart Rate','Creatinine','Troponin','C-reactive Protein'
]

# Map abbreviated labels to full disease names
DISEASE_LABELS = {
    'Healthy':'Healthy','Diabetes':'Diabetes','Anemia':'Anemia',
    'Thalasse':'Thalassemia','Thromboc':'Thrombocytopenia','Heart Di':'Heart Disease'
}

def main():
    # Load and combine data
    df = pd.concat([pd.read_csv(os.path.join(DATA,'train_data.csv')),
                    pd.read_csv(os.path.join(DATA,'test_data.csv'))], ignore_index=True)
    
    # Fix labels and remove any missing values
    df['Disease'] = df['Disease'].map(DISEASE_LABELS).fillna(df['Disease'])
    df = df.dropna()
    
    X, y_raw = df[FEATURES].values, df['Disease'].values
    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    
    # Split data into training and testing sets, keeping class proportions equal
    X_tr,X_te,y_tr,y_te = train_test_split(X,y,test_size=0.2,random_state=42,stratify=y)
    
    # Scale the features so no single one dominates the model
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_te_s = scaler.transform(X_te)
    
    # Save the preprocessing tools
    joblib.dump(scaler, os.path.join(MDLS,'scaler.pkl'))
    joblib.dump(le, os.path.join(MDLS,'label_encoder.pkl'))

    print(f'Dataset: {len(df)} | Train: {X_tr_s.shape} | Test: {X_te_s.shape}')
    print(f'Classes: {list(le.classes_)}')

    # Setting up the different models to compare
    clfs = [
        ('Logistic Regression', LogisticRegression(max_iter=2000,C=1.0,class_weight='balanced',random_state=42,solver='lbfgs')),
        ('Decision Tree', DecisionTreeClassifier(max_depth=12,min_samples_split=5,min_samples_leaf=2,class_weight='balanced',random_state=42)),
        ('Random Forest', RandomForestClassifier(n_estimators=200,max_depth=15,class_weight='balanced',random_state=42,n_jobs=-1)),
        ('Support Vector Machine', SVC(kernel='rbf',C=10,gamma='scale',class_weight='balanced',random_state=42,probability=True)),
    ]
    
    results = []
    
    # Loop through each model to train and test it
    for name, clf in clfs:
        clf.fit(X_tr_s, y_tr)
        y_pred = clf.predict(X_te_s)
        
        # Cross validation to ensure the model generalizes well
        cv = StratifiedKFold(n_splits=5,shuffle=True,random_state=42)
        cv_s = cross_val_score(clf,X_tr_s,y_tr,cv=cv,scoring='accuracy')
        
        # Calculate performance scores
        acc=accuracy_score(y_te,y_pred); prec=precision_score(y_te,y_pred,average='weighted',zero_division=0)
        rec=recall_score(y_te,y_pred,average='weighted',zero_division=0); f1=f1_score(y_te,y_pred,average='weighted',zero_division=0)
        cm=confusion_matrix(y_te,y_pred)
        
        # Save the trained model to a file so the web app can load it
        safe = name.lower().replace(' ', '_')
        model_path = os.path.join(MDLS, f'{safe}_model.pkl')
        joblib.dump(clf, model_path)
        
        r = {'name': name, 'accuracy': round(float(acc), 4), 'precision': round(float(prec), 4),
             'recall': round(float(rec), 4), 'f1_score': round(float(f1), 4),
             'cv_mean': round(float(cv_s.mean()), 4), 'cv_std': round(float(cv_s.std()), 4),
             'confusion_matrix': cm.tolist(), 'classes': list(le.classes_), 'key': safe}
        
        print(f'  {name}: acc={acc:.4f} f1={f1:.4f} cv={cv_s.mean():.4f}')
        results.append(r)

    # Pick the best model based on F1-score
    best = max(results, key=lambda x: x['f1_score'])
    shutil.copy(os.path.join(MDLS, f'{best["key"]}_model.pkl'), os.path.join(MDLS, 'best_model.pkl'))
    
    # Save the summary of results for the frontend to show
    summary = {'best_model': best['name'], 'best_model_key': best['key'],
               'models': results, 'features': FEATURES, 'classes': list(le.classes_), 'disease_labels': DISEASE_LABELS}
    
    with open(os.path.join(MDLS,'results_summary.json'),'w') as f:
        json.dump(summary,f,indent=2)
        
    print(f'\nBest: {best["name"]} (F1={best["f1_score"]}). All models saved.')

if __name__ == '__main__':
    main()
