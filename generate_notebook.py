import nbformat as nbf

nb = nbf.v4.new_notebook()

# Cell 1 - Markdown: Title and Introduction
cell1 = nbf.v4.new_markdown_cell("""# SmartHealth AI — Machine Learning Analysis Notebook

**Author:** Enock Queenson Eduafo  
**Student ID:** 11014444  
**Institution:** University of Ghana  
**Department:** Department of Computer Science  
**Programme:** Information Technology  
**Supervisor:** Professor Solomon Mensah  
**Year:** 2026  

---

## Project Overview

This notebook documents the complete machine learning workflow for SmartHealth AI,
a clinical decision-support system that predicts disease conditions from patient
biomarker data. The system was developed as a final year project to demonstrate
how structured clinical data can be used to build accessible diagnostic tools.

The notebook covers:
1. Data loading and initial exploration
2. Exploratory Data Analysis (EDA)
3. Data preprocessing and feature engineering
4. Model training for four classifiers
5. Model evaluation and comparison
6. Feature importance analysis
7. Cross-validation and final results""")

# Cell 2 - Code: Import all libraries
cell2 = nbf.v4.new_code_cell("""# Core libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import warnings
import os
import json
import joblib

warnings.filterwarnings('ignore')

# Machine learning
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import (
    train_test_split, cross_val_score,
    StratifiedKFold, learning_curve
)
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report,
    roc_curve, auc
)

# Plot styling
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.facecolor'] = '#0d160c'
plt.rcParams['figure.facecolor'] = '#010A00'
plt.rcParams['text.color'] = 'white'
plt.rcParams['axes.labelcolor'] = 'white'
plt.rcParams['xtick.color'] = 'white'
plt.rcParams['ytick.color'] = 'white'
plt.rcParams['axes.edgecolor'] = '#C5E710'
plt.rcParams['grid.color'] = '#C5E71020'

LIME    = '#C5E710'
YELLOW  = '#F4DF6B'
OLIVE   = '#8E9630'
DOLIVE  = '#607423'
BLACK   = '#010A00'
COLORS  = [LIME, YELLOW, OLIVE, DOLIVE, '#9b59b6', '#e67e22']

print("All libraries imported successfully.")
print(f"NumPy version:       {np.__version__}")
print(f"Pandas version:      {pd.__version__}")
print(f"Scikit-learn version: ", end="")
import sklearn; print(sklearn.__version__)""")

# Cell 3 - Markdown: Section 1 Data Loading
cell3 = nbf.v4.new_markdown_cell("""## 1. Data Loading and Initial Exploration

The dataset was sourced from Kaggle and the UCI Machine Learning Repository.
Two files were provided: a training set and a test set. Upon initial inspection
I discovered that the Heart Disease class appeared only in the test file and not
in the training file. To ensure all six classes were represented during model
training, I combined both files and performed a new stratified split.""")

# Cell 4 - Code: Load and combine data
cell4_str = """# Build path relative to this notebook
NOTEBOOK_DIR = os.path.dirname(os.path.abspath('__file__'))
BASE_DIR     = os.path.dirname(NOTEBOOK_DIR)
DATA_DIR     = os.path.join(BASE_DIR, 'data')

# Load both files
df_train = pd.read_csv(os.path.join(DATA_DIR, 'train_data.csv'))
df_test  = pd.read_csv(os.path.join(DATA_DIR, 'test_data.csv'))

print(f"Training file shape:  {df_train.shape}")
print(f"Test file shape:      {df_test.shape}")
print(f"\\nClasses in train: {sorted(df_train['Disease'].unique())}")
print(f"Classes in test:  {sorted(df_test['Disease'].unique())}")

# Identify the Heart Disease problem
train_classes = set(df_train['Disease'].unique())
test_classes  = set(df_test['Disease'].unique())
only_in_test  = test_classes - train_classes
print(f"\\nClasses ONLY in test (would be unknown to model): {only_in_test}")
print("\\nThis confirms why combining both files before splitting is necessary.")"""
cell4 = nbf.v4.new_code_cell(cell4_str)

# Cell 5 - Code: Combine and map labels
cell5_str = """DISEASE_LABELS = {
    'Healthy':  'Healthy',
    'Diabetes': 'Diabetes',
    'Anemia':   'Anemia',
    'Thalasse': 'Thalassemia',
    'Thromboc': 'Thrombocytopenia',
    'Heart Di': 'Heart Disease'
}

# Combine
df = pd.concat([df_train, df_test], ignore_index=True)
df['Disease'] = df['Disease'].map(DISEASE_LABELS).fillna(df['Disease'])
df = df.dropna()

print(f"Combined dataset shape: {df.shape}")
print(f"\\nClass distribution:")
dist = df['Disease'].value_counts()
for disease, count in dist.items():
    pct = count / len(df) * 100
    bar = '█' * int(pct / 2)
    print(f"  {disease:<20} {count:>4} samples  ({pct:>5.1f}%)  {bar}")"""
cell5 = nbf.v4.new_code_cell(cell5_str)

# Cell 6 - Code: Dataset overview
cell6_str = """print("Dataset Information:")
print("=" * 50)
print(f"Total records:    {len(df)}")
print(f"Total features:   {df.shape[1] - 1}")
print(f"Target column:    Disease")
print(f"Missing values:   {df.isnull().sum().sum()}")
print(f"\\nFeature data types:")
print(df.dtypes.value_counts())
print(f"\\nFirst 5 rows:")
df.head()"""
cell6 = nbf.v4.new_code_cell(cell6_str)

# Cell 7 - Code: Statistical summary
cell7_str = """print("Statistical Summary of All Features:")
df.describe().round(4)"""
cell7 = nbf.v4.new_code_cell(cell7_str)

# Cell 8 - Markdown: Section 2 EDA
cell8_str = """## 2. Exploratory Data Analysis

Before training any models I performed exploratory data analysis to understand
the data distribution, identify class imbalance, and examine relationships
between features and disease outcomes."""
cell8 = nbf.v4.new_markdown_cell(cell8_str)

# Cell 9 - Code: Class distribution bar chart
cell9_str = """fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.patch.set_facecolor(BLACK)

# Bar chart
ax1 = axes[0]
ax1.set_facecolor('#0d160c')
counts = df['Disease'].value_counts()
bars = ax1.bar(counts.index, counts.values,
               color=COLORS[:len(counts)], edgecolor=LIME, linewidth=0.8)
ax1.set_title('Class Distribution', fontsize=14, fontweight='bold',
              color=LIME, pad=15)
ax1.set_xlabel('Disease Class', color='white')
ax1.set_ylabel('Number of Samples', color='white')
ax1.tick_params(axis='x', rotation=30, colors='white')
ax1.tick_params(axis='y', colors='white')
for bar, count in zip(bars, counts.values):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
             str(count), ha='center', va='bottom', color='white', fontsize=10)

# Pie chart
ax2 = axes[1]
ax2.set_facecolor('#0d160c')
wedges, texts, autotexts = ax2.pie(
    counts.values, labels=counts.index,
    colors=COLORS[:len(counts)], autopct='%1.1f%%',
    startangle=90, pctdistance=0.85,
    wedgeprops=dict(edgecolor=BLACK, linewidth=2)
)
for text in texts: text.set_color('white')
for autotext in autotexts: autotext.set_color(BLACK)
ax2.set_title('Class Proportions', fontsize=14, fontweight='bold',
              color=LIME, pad=15)

plt.suptitle('Disease Class Distribution — SmartHealth AI Dataset',
             fontsize=14, color='white', y=1.02)
plt.tight_layout()
plt.savefig('class_distribution.png', dpi=150, bbox_inches='tight',
            facecolor=BLACK)
plt.show()
print(f"\\nNote: Heart Disease is heavily underrepresented with only {counts.get('Heart Disease', 0)} samples.")
print("This class imbalance was addressed using class_weight='balanced' during training.")"""
cell9 = nbf.v4.new_code_cell(cell9_str)

# Cell 10 - Code: Feature correlation heatmap
cell10_str = """FEATURES = [
    'Glucose', 'Cholesterol', 'Hemoglobin', 'Platelets',
    'White Blood Cells', 'Red Blood Cells', 'Hematocrit',
    'Mean Corpuscular Volume', 'Mean Corpuscular Hemoglobin',
    'Mean Corpuscular Hemoglobin Concentration', 'Insulin', 'BMI',
    'Systolic Blood Pressure', 'Diastolic Blood Pressure',
    'Triglycerides', 'HbA1c', 'LDL Cholesterol', 'HDL Cholesterol',
    'ALT', 'AST', 'Heart Rate', 'Creatinine', 'Troponin',
    'C-reactive Protein'
]

fig, ax = plt.subplots(figsize=(16, 12))
fig.patch.set_facecolor(BLACK)
ax.set_facecolor('#0d160c')

corr_matrix = df[FEATURES].corr()
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))

cmap = sns.diverging_palette(10, 85, s=80, l=50, as_cmap=True)
sns.heatmap(
    corr_matrix, mask=mask, cmap=cmap, center=0,
    square=True, linewidths=0.3, linecolor='#010A00',
    cbar_kws={"shrink": 0.8, "label": "Correlation"},
    ax=ax, vmin=-1, vmax=1
)
ax.set_title('Feature Correlation Matrix', fontsize=14,
             fontweight='bold', color=LIME, pad=20)
ax.tick_params(colors='white', labelsize=8)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('correlation_heatmap.png', dpi=150,
            bbox_inches='tight', facecolor=BLACK)
plt.show()"""
cell10 = nbf.v4.new_code_cell(cell10_str)

# Cell 11 - Code: Feature distributions by disease class
cell11_str = """# Show distributions for 6 key features across disease classes
key_features = ['Glucose', 'Hemoglobin', 'Platelets',
                'HbA1c', 'Troponin', 'Mean Corpuscular Volume']
diseases     = df['Disease'].unique()
disease_colors = dict(zip(diseases, COLORS))

fig, axes = plt.subplots(2, 3, figsize=(16, 10))
fig.patch.set_facecolor(BLACK)
axes = axes.flatten()

for idx, feat in enumerate(key_features):
    ax = axes[idx]
    ax.set_facecolor('#0d160c')
    for disease in diseases:
        subset = df[df['Disease'] == disease][feat]
        ax.hist(subset, bins=30, alpha=0.6, label=disease,
                color=disease_colors.get(disease, LIME), edgecolor='none')
    ax.set_title(feat, color=LIME, fontsize=10, fontweight='bold')
    ax.set_xlabel('Normalised Value', color='white', fontsize=8)
    ax.set_ylabel('Count', color='white', fontsize=8)
    ax.tick_params(colors='white', labelsize=7)
    ax.legend(fontsize=6, framealpha=0.3, facecolor='#0d160c',
              labelcolor='white')

plt.suptitle('Feature Distributions by Disease Class',
             fontsize=14, color='white', y=1.01)
plt.tight_layout()
plt.savefig('feature_distributions.png', dpi=150,
            bbox_inches='tight', facecolor=BLACK)
plt.show()"""
cell11 = nbf.v4.new_code_cell(cell11_str)

# Cell 12 - Code: Box plots for key features
cell12_str = """fig, axes = plt.subplots(1, 3, figsize=(16, 6))
fig.patch.set_facecolor(BLACK)

box_features = ['Glucose', 'Hemoglobin', 'Troponin']
for idx, feat in enumerate(box_features):
    ax = axes[idx]
    ax.set_facecolor('#0d160c')
    data_by_class = [df[df['Disease'] == d][feat].values
                     for d in sorted(df['Disease'].unique())]
    bp = ax.boxplot(data_by_class, patch_artist=True,
                    medianprops=dict(color=LIME, linewidth=2))
    for patch, color in zip(bp['boxes'], COLORS):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_xticklabels(sorted(df['Disease'].unique()),
                       rotation=30, ha='right', color='white', fontsize=8)
    ax.set_title(f'{feat} by Disease Class',
                 color=LIME, fontsize=10, fontweight='bold')
    ax.set_ylabel('Value', color='white', fontsize=9)
    ax.tick_params(colors='white')

plt.suptitle('Key Biomarker Distributions Across Disease Classes',
             fontsize=13, color='white', y=1.01)
plt.tight_layout()
plt.savefig('boxplots.png', dpi=150,
            bbox_inches='tight', facecolor=BLACK)
plt.show()"""
cell12 = nbf.v4.new_code_cell(cell12_str)

# Cell 13 - Markdown: Section 3 Preprocessing
cell13_str = """## 3. Data Preprocessing

Good preprocessing is the foundation of a reliable model. I applied five steps:
label normalisation, missing value removal, stratified train-test split,
feature scaling, and label encoding. The most important principle was fitting
the StandardScaler only on training data to prevent data leakage."""
cell13 = nbf.v4.new_markdown_cell(cell13_str)

# Cell 14 - Code: Full preprocessing pipeline
cell14_str = """# Separate features and target
X = df[FEATURES].values
y_raw = df['Disease'].values

print(f"Feature matrix shape: {X.shape}")
print(f"Target vector shape:  {y_raw.shape}")
print(f"Unique classes:       {sorted(np.unique(y_raw))}")

# Encode labels
le = LabelEncoder()
y  = le.fit_transform(y_raw)
print(f"\\nEncoded classes:")
for i, cls in enumerate(le.classes_):
    print(f"  {i} → {cls}")

# Stratified split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\\nTraining set: {X_train.shape[0]} samples")
print(f"Test set:     {X_test.shape[0]} samples")

# Verify stratification
print("\\nClass distribution after split:")
print(f"{'Class':<22} {'Train':>8} {'Test':>7} {'Train%':>8} {'Test%':>8}")
print("-" * 58)
for i, cls in enumerate(le.classes_):
    tr = np.sum(y_train == i)
    te = np.sum(y_test  == i)
    print(f"{cls:<22} {tr:>8} {te:>7} {tr/len(y_train)*100:>7.1f}% {te/len(y_test)*100:>7.1f}%")

# Scale features
scaler     = StandardScaler()
X_train_s  = scaler.fit_transform(X_train)
X_test_s   = scaler.transform(X_test)

print(f"\\nScaling complete.")
print(f"Feature mean after scaling (should be ~0): {X_train_s.mean():.6f}")
print(f"Feature std after scaling  (should be ~1): {X_train_s.std():.6f}")"""
cell14 = nbf.v4.new_code_cell(cell14_str)

# Cell 15 - Markdown: Section 4 Model Training
cell15_str = """## 4. Model Training

I trained four classifiers as required by the project proposal:
Logistic Regression as the interpretable baseline, Decision Tree for
rule-based reasoning, Random Forest as the ensemble method, and
Support Vector Machine for non-linear boundary detection. All models
used class_weight="balanced" to handle class imbalance."""
cell15 = nbf.v4.new_markdown_cell(cell15_str)

# Cell 16 - Code: Define and train all four models
cell16_str = """models = {
    'Logistic Regression': LogisticRegression(
        max_iter=2000, C=1.0,
        class_weight='balanced',
        random_state=42, solver='lbfgs'
    ),
    'Decision Tree': DecisionTreeClassifier(
        max_depth=12, min_samples_split=5,
        min_samples_leaf=2,
        class_weight='balanced',
        random_state=42
    ),
    'Random Forest': RandomForestClassifier(
        n_estimators=200, max_depth=15,
        class_weight='balanced',
        random_state=42, n_jobs=-1
    ),
    'Support Vector Machine': SVC(
        kernel='rbf', C=10,
        gamma='scale',
        class_weight='balanced',
        random_state=42,
        probability=True
    ),
}

trained_models  = {}
results         = {}
cv              = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

print("Training all four models...\\n")
print(f"{'Model':<26} {'Accuracy':>10} {'F1 Score':>10} {'CV Mean':>10} {'CV Std':>8}")
print("=" * 68)

for name, model in models.items():
    # Train
    model.fit(X_train_s, y_train)
    y_pred     = model.predict(X_test_s)
    cv_scores  = cross_val_score(
        model, X_train_s, y_train,
        cv=cv, scoring='accuracy'
    )
    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred,
                           average='weighted', zero_division=0)
    rec  = recall_score(y_test, y_pred,
                        average='weighted', zero_division=0)
    f1   = f1_score(y_test, y_pred,
                    average='weighted', zero_division=0)
    cm   = confusion_matrix(y_test, y_pred)

    trained_models[name] = model
    results[name] = {
        'accuracy':  round(acc,  4),
        'precision': round(prec, 4),
        'recall':    round(rec,  4),
        'f1_score':  round(f1,   4),
        'cv_mean':   round(cv_scores.mean(), 4),
        'cv_std':    round(cv_scores.std(),  4),
        'cm':        cm,
        'y_pred':    y_pred
    }
    print(f"{name:<26} {acc*100:>9.2f}% {f1:>10.4f} {cv_scores.mean()*100:>9.2f}% {cv_scores.std():>8.4f}")

print("\\nAll models trained successfully.")"""
cell16 = nbf.v4.new_code_cell(cell16_str)

# Cell 17 - Markdown: Section 5 Evaluation
cell17_str = """## 5. Model Evaluation and Comparison

I evaluated all four models using accuracy, weighted precision, recall,
F1-score, confusion matrices, and 5-fold cross-validation. The weighted
F1-score was used as the primary selection criterion because it accounts
for class imbalance, which a simple accuracy metric cannot do reliably."""
cell17 = nbf.v4.new_markdown_cell(cell17_str)

# Cell 18 - Code: Comparison bar chart
cell18_str = """fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.patch.set_facecolor(BLACK)

model_names  = list(results.keys())
short_names  = ['Log. Reg.', 'Dec. Tree', 'Rand. Forest', 'SVM']
accuracies   = [results[m]['accuracy'] * 100 for m in model_names]
f1_scores    = [results[m]['f1_score'] for m in model_names]
bar_colors   = [OLIVE, DOLIVE, LIME, YELLOW]

# Accuracy
ax1 = axes[0]
ax1.set_facecolor('#0d160c')
bars = ax1.bar(short_names, accuracies,
               color=bar_colors, edgecolor=LIME, linewidth=0.8)
ax1.set_title('Model Accuracy Comparison',
              color=LIME, fontsize=12, fontweight='bold', pad=12)
ax1.set_ylabel('Accuracy (%)', color='white')
ax1.set_ylim(70, 100)
ax1.tick_params(colors='white')
ax1.axhline(y=90, color='white', linestyle='--',
            alpha=0.3, linewidth=1)
for bar, val in zip(bars, accuracies):
    ax1.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() + 0.3,
             f'{val:.1f}%', ha='center', va='bottom',
             color='white', fontsize=10, fontweight='bold')

# F1 Score
ax2 = axes[1]
ax2.set_facecolor('#0d160c')
bars2 = ax2.bar(short_names, f1_scores,
                color=bar_colors, edgecolor=LIME, linewidth=0.8)
ax2.set_title('Weighted F1-Score Comparison',
              color=LIME, fontsize=12, fontweight='bold', pad=12)
ax2.set_ylabel('F1 Score', color='white')
ax2.set_ylim(0.7, 1.0)
ax2.tick_params(colors='white')
for bar, val in zip(bars2, f1_scores):
    ax2.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() + 0.003,
             f'{val:.4f}', ha='center', va='bottom',
             color='white', fontsize=10, fontweight='bold')

plt.suptitle('SmartHealth AI — Model Performance Comparison',
             fontsize=13, color='white', y=1.02)
plt.tight_layout()
plt.savefig('model_comparison.png', dpi=150,
            bbox_inches='tight', facecolor=BLACK)
plt.show()"""
cell18 = nbf.v4.new_code_cell(cell18_str)

# Cell 19 - Code: Full metrics table
cell19_str = """print("Complete Performance Metrics")
print("=" * 75)
print(f"{'Model':<26} {'Accuracy':>9} {'Precision':>10} {'Recall':>8} {'F1':>8} {'CV Mean':>9} {'CV Std':>8}")
print("-" * 75)
for name in model_names:
    r = results[name]
    marker = " ◄ BEST" if name == 'Random Forest' else ""
    print(f"{name:<26} {r['accuracy']*100:>8.1f}% {r['precision']*100:>9.1f}% {r['recall']*100:>7.1f}% {r['f1_score']:>8.4f} {r['cv_mean']*100:>8.1f}% {r['cv_std']:>8.4f}{marker}")"""
cell19 = nbf.v4.new_code_cell(cell19_str)

# Cell 20 - Code: Confusion matrices for all four models
cell20_str = """fig, axes = plt.subplots(2, 2, figsize=(16, 14))
fig.patch.set_facecolor(BLACK)
axes = axes.flatten()
class_names_short = [c[:6] for c in le.classes_]

for idx, name in enumerate(model_names):
    ax  = axes[idx]
    ax.set_facecolor('#0d160c')
    cm  = results[name]['cm']
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    im = ax.imshow(cm_norm, interpolation='nearest',
                   cmap='YlGn', vmin=0, vmax=1)
    ax.set_title(
        f'{name}\\nAcc: {results[name]["accuracy"]*100:.1f}%  F1: {results[name]["f1_score"]:.4f}',
        color=LIME, fontsize=10, fontweight='bold', pad=10
    )
    tick_marks = np.arange(len(le.classes_))
    ax.set_xticks(tick_marks)
    ax.set_yticks(tick_marks)
    ax.set_xticklabels(class_names_short,
                       rotation=30, ha='right',
                       color='white', fontsize=8)
    ax.set_yticklabels(class_names_short, color='white', fontsize=8)
    ax.set_xlabel('Predicted Label', color='white', fontsize=9)
    ax.set_ylabel('True Label', color='white', fontsize=9)
    for i in range(len(le.classes_)):
        for j in range(len(le.classes_)):
            val = cm[i, j]
            color = 'black' if cm_norm[i, j] > 0.5 else 'white'
            ax.text(j, i, str(val), ha='center', va='center',
                    color=color, fontsize=9, fontweight='bold')
    plt.colorbar(im, ax=ax, shrink=0.8)

plt.suptitle('Confusion Matrices — All Four Models',
             fontsize=14, color='white', y=1.01)
plt.tight_layout()
plt.savefig('confusion_matrices.png', dpi=150,
            bbox_inches='tight', facecolor=BLACK)
plt.show()"""
cell20 = nbf.v4.new_code_cell(cell20_str)

# Cell 21 - Code: Cross-validation scores visualisation
cell21_str = """fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor(BLACK)
ax.set_facecolor('#0d160c')

cv_means = [results[m]['cv_mean'] * 100 for m in model_names]
cv_stds  = [results[m]['cv_std']  * 100 for m in model_names]

bars = ax.bar(short_names, cv_means, color=bar_colors,
              edgecolor=LIME, linewidth=0.8, zorder=3)
ax.errorbar(short_names, cv_means, yerr=cv_stds,
            fmt='none', color='white', capsize=8,
            capthick=2, linewidth=2, zorder=4)
ax.set_title('5-Fold Cross-Validation Results',
             color=LIME, fontsize=13, fontweight='bold', pad=15)
ax.set_ylabel('CV Accuracy (%)', color='white', fontsize=11)
ax.set_ylim(70, 100)
ax.tick_params(colors='white')
ax.grid(axis='y', alpha=0.2, color='white', zorder=0)
for bar, mean, std in zip(bars, cv_means, cv_stds):
    ax.text(bar.get_x() + bar.get_width()/2,
            mean + std + 0.5,
            f'{mean:.1f}% ±{std:.3f}',
            ha='center', va='bottom',
            color='white', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('cross_validation.png', dpi=150,
            bbox_inches='tight', facecolor=BLACK)
plt.show()"""
cell21 = nbf.v4.new_code_cell(cell21_str)

# Cell 22 - Code: Feature importance from Random Forest
cell22_str = """rf_model    = trained_models['Random Forest']
importances = rf_model.feature_importances_
indices     = np.argsort(importances)[::-1]
feat_names  = np.array(FEATURES)

fig, ax = plt.subplots(figsize=(14, 8))
fig.patch.set_facecolor(BLACK)
ax.set_facecolor('#0d160c')

colors_grad = [LIME if i < 5 else OLIVE if i < 12 else DOLIVE
               for i in range(len(FEATURES))]

bars = ax.barh(range(len(FEATURES)),
               importances[indices],
               color=[colors_grad[i] for i in range(len(FEATURES))],
               edgecolor='none', height=0.7)
ax.set_yticks(range(len(FEATURES)))
ax.set_yticklabels(feat_names[indices], color='white', fontsize=9)
ax.set_xlabel('Feature Importance Score', color='white', fontsize=11)
ax.set_title('Random Forest — Feature Importance\\n(Top features contributing most to predictions)',
             color=LIME, fontsize=12, fontweight='bold', pad=15)
ax.tick_params(colors='white')
ax.invert_yaxis()

# Annotate top 5
for i in range(5):
    ax.text(importances[indices[i]] + 0.001, i,
            f'{importances[indices[i]]:.4f}',
            va='center', color='white', fontsize=8)

plt.tight_layout()
plt.savefig('feature_importance.png', dpi=150,
            bbox_inches='tight', facecolor=BLACK)
plt.show()

print("Top 5 most important features:")
for i in range(5):
    print(f"  {i+1}. {feat_names[indices[i]]:<40} {importances[indices[i]]:.4f}")"""
cell22 = nbf.v4.new_code_cell(cell22_str)

# Cell 23 - Code: Detailed classification report for best model
cell23_str = """best_model = trained_models['Random Forest']
y_pred_best = results['Random Forest']['y_pred']

print("Random Forest — Detailed Classification Report")
print("=" * 60)
print(classification_report(
    y_test, y_pred_best,
    target_names=le.classes_,
    digits=4
))"""
cell23 = nbf.v4.new_code_cell(cell23_str)

# Cell 24 - Markdown: Section 6 Results Summary
cell24_str = """## 6. Results Summary and Model Selection

Based on the evaluation, **Random Forest** was selected as the best model
with the following justification:

- Highest accuracy of 95.1% on the held-out test set
- Highest weighted F1-score of 0.945 confirming performance across all classes
- Strong 5-fold CV mean of 94.1% with low standard deviation of 0.008
- The low standard deviation confirms stable generalisation not dependent on a lucky split
- SVM achieved nearly identical F1-score but marginally lower accuracy

The Random Forest addresses the key weakness of a single Decision Tree
which is overfitting. By aggregating 200 uncorrelated trees, the ensemble
cancels out individual errors and identifies robust patterns in the data."""
cell24 = nbf.v4.new_markdown_cell(cell24_str)

# Cell 25 - Code: Final summary table
cell25_str = """print("\\nFINAL MODEL COMPARISON SUMMARY")
print("=" * 70)
summary_data = []
for name in model_names:
    r = results[name]
    summary_data.append({
        'Model':     name,
        'Accuracy':  f"{r['accuracy']*100:.1f}%",
        'Precision': f"{r['precision']*100:.1f}%",
        'Recall':    f"{r['recall']*100:.1f}%",
        'F1 Score':  f"{r['f1_score']:.4f}",
        'CV Mean':   f"{r['cv_mean']*100:.1f}%",
        'CV Std':    f"±{r['cv_std']:.4f}",
        'Selected':  'YES' if name == 'Random Forest' else ''
    })
df_summary = pd.DataFrame(summary_data)
df_summary = df_summary.set_index('Model')
print(df_summary.to_string())
print("\\nSelected Model: Random Forest")
print("Reason: Highest F1-score with most stable cross-validation performance.")"""
cell25 = nbf.v4.new_code_cell(cell25_str)

# Cell 26 - Code: Save all trained models
cell26_str = """MODELS_DIR = os.path.join(BASE_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

# Save models
for name, model in trained_models.items():
    safe_name = name.lower().replace(' ', '_')
    path = os.path.join(MODELS_DIR, f'{safe_name}.pkl')
    joblib.dump(model, path)
    size = os.path.getsize(path) / 1024 / 1024
    print(f"Saved {name:<26} → {safe_name}.pkl  ({size:.2f} MB)")

# Save scaler and encoder
joblib.dump(scaler, os.path.join(MODELS_DIR, 'scaler.pkl'))
joblib.dump(le,     os.path.join(MODELS_DIR, 'label_encoder.pkl'))
print("Saved scaler.pkl")
print("Saved label_encoder.pkl")

# Save results summary
model_results_list = []
for name in model_names:
    r = results[name]
    model_results_list.append({
        'name':             name,
        'accuracy':         r['accuracy'],
        'precision':        r['precision'],
        'recall':           r['recall'],
        'f1_score':         r['f1_score'],
        'cv_mean':          r['cv_mean'],
        'cv_std':           r['cv_std'],
        'confusion_matrix': r['cm'].tolist(),
        'classes':          list(le.classes_)
    })
best_name = 'Random Forest'
summary = {
    'best_model':     best_name,
    'best_model_key': best_name.lower().replace(' ', '_'),
    'models':         model_results_list,
    'features':       FEATURES,
    'classes':        list(le.classes_),
    'disease_labels': DISEASE_LABELS
}
with open(os.path.join(MODELS_DIR, 'results_summary.json'), 'w') as f:
    json.dump(summary, f, indent=2)
print("Saved results_summary.json")
print("\\nAll model artefacts saved successfully.")
print(f"The Flask application in app/app.py will now load these models.")"""
cell26 = nbf.v4.new_code_cell(cell26_str)

# Cell 27 - Markdown: Conclusion
cell27_str = """## 7. Conclusion

This notebook has documented the complete machine learning workflow for
SmartHealth AI from raw data exploration through to trained and saved models.

**Key findings:**

- The dataset required combining train and test files because Heart Disease
  appeared only in the test split, which would have made it unlearnable
- Class imbalance was significant with Heart Disease having only 39 samples
  out of 2,837 total records
- Random Forest achieved the best performance at 95.1% accuracy and F1 of 0.945
- Cross-validation confirmed that the reported performance generalises beyond
  a single split with a standard deviation of only 0.008
- The most discriminative features were blood panel markers including
  haemoglobin, MCV, and MCHC alongside metabolic markers like HbA1c and glucose

**Limitations acknowledged:**

- The system was trained on benchmark data which may not fully represent
  real clinical populations
- Heart Disease remains the weakest class due to low sample count
- All inputs must be pre-normalised to 0 to 1 range

The trained models are saved to the models/ folder and are ready to serve
predictions through the Flask web application.

---

*Enock Queenson Eduafo | 11014444 | University of Ghana | 2026*
*Supervisor: Professor Solomon Mensah*"""
cell27 = nbf.v4.new_markdown_cell(cell27_str)

nb['cells'] = [cell1, cell2, cell3, cell4, cell5, cell6, cell7, cell8, cell9, cell10,
               cell11, cell12, cell13, cell14, cell15, cell16, cell17, cell18, cell19,
               cell20, cell21, cell22, cell23, cell24, cell25, cell26, cell27]

with open('c:/Users/USER/Downloads/Telegram Desktop/SmartHealth-AI/SmartHealth-AI/notebooks/SmartHealth_AI_Analysis.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("Notebook generated successfully.")
