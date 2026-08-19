# Symptom & Biomarker Dataset Audit Report

**Date:** 2026-08-19
**Symptom Dataset File:** `data/Final_Augmented_dataset_Diseases_and_Symptoms.csv`

## 1. Symptom Dataset Audit Results

- **Total Rows:** 246,945
- **Total Columns:** 378 (1 disease label column: `diseases` + 377 binary symptom features)
- **Exact Duplicate Rows:** 57,298 (23.20%)
- **Unique Disease Labels:** 773

## 2. Target Class Frequencies in Symptom Dataset

| Disease Label | Exact Row Count | Status (<50 rows = Sparse) |
|---|---|---|
| `anemia` | 331 | ✅ Usable (>=50 rows) |
| `diabetes` | 1 | ⚠️ Too Sparse (<50 rows) |
| `thalassemia` | 1 | ⚠️ Too Sparse (<50 rows) |
| `thrombocytopenia` | 126 | ✅ Usable (>=50 rows) |
| `malaria` | 15 | ⚠️ Too Sparse (<50 rows) |
| `typhoid fever` | 1 | ⚠️ Too Sparse (<50 rows) |

## 3. Biomarker Dataset Audit Results (`train_data.csv` & `test_data.csv`)

### `train_data.csv`
- **Total Rows:** 2,351
- **Exact Duplicate Rows:** 2,286 (97.24%)
- **Unique Clean Rows:** 65
- **Class Breakdown:**
  - `Anemia`: 623 rows
  - `Healthy`: 556 rows
  - `Diabetes`: 540 rows
  - `Thalasse`: 509 rows
  - `Thromboc`: 123 rows

### `test_data.csv`
- **Total Rows:** 486
- **Exact Duplicate Rows:** 0 (0.00%)
- **Class Breakdown:**
  - `Diabetes`: 294 rows
  - `Anemia`: 84 rows
  - `Thalasse`: 48 rows
  - `Heart Di`: 39 rows
  - `Thromboc`: 16 rows
  - `Healthy`: 5 rows

## 4. Key Findings & Recommendations

1. **Symptom Dataset Usage Boundary:**
   - `anemia` (331 rows) and `thrombocytopenia` (126 rows) are usable.
   - `diabetes` (1 row), `thalassemia` (1 row), `typhoid fever` (1 row), and `malaria` (15 rows) are sparse (<50 rows).
   - **Conclusion:** Do NOT train a high-confidence multi-class classifier on these sparse classes. Use `Final_Augmented_dataset_Diseases_and_Symptoms.csv` exclusively for symptom vocabulary, chip extraction, and rule-scoring pre-assessment.
2. **Biomarker Dataset Defects:**
   - **Training Duplicates:** 2,286 out of 2,351 rows (97.24%) in `train_data.csv` are exact duplicates. Only 65 unique rows exist across 5 classes.
   - **Label Mismatch / Missing Class:** `test_data.csv` contains `Heart Di` (39 rows), whereas `train_data.csv` has ZERO rows labeled `Heart Di`. A model trained on `train_data.csv` cannot predict `Heart Di` / `Heart Disease` without training examples.
   - **Taxonomy Normalization Required:** `Thalasse` → `Thalassemia`, `Thromboc` → `Thrombocytopenia`, `Heart Di` → `Heart Disease`.
