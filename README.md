# Smart Health Sync — Predictive Modelling for Disease Diagnosis Using Health Data

**Author:** Enock Queenson Eduafo  
**Student ID:** 11014444  
**Supervisor:** Professor Solomon Mensah  
**Institution:** University of Ghana, Department of Computer Science  
**Programme:** Information Technology  
**Year:** 2026

---

## Project Overview

For my final year project, I built Smart Health Sync to tackle the challenges of disease diagnosis using machine learning. I wanted to see how we could use clinical biomarker data — things like glucose levels, blood pressure, and cholesterol — to help clinicians make faster and more accurate decisions. I developed a system that uses four different machine learning models to predict six different health conditions. I also built a web interface using Flask so that anyone can enter health data and see the engine's predictions in real-time.

---

## How to Run the Project

1. **Install the required libraries**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Train the models**:
   Run the training script to process the data and save the models to the `models/` folder.
   ```bash
   python src/train_models.py
   ```

3. **Start the web application**:
   ```bash
   python app/app.py
   ```

4. **Access the system**:
   Open your browser and go to `http://localhost:5000`.

---

## Project Structure

- `data/`: Contains the patient health datasets (CSV files).
- `models/`: Stores the trained machine learning models (`.pkl` files) and results.
- `src/`: Contains the Python script I wrote to train and evaluate the models.
- `app/`: The main directory for the web application.
  - `app.py`: The Flask server that handles predictions.
  - `templates/`: HTML files for the web pages.
  - `static/`: CSS and JavaScript files for the design and interactivity.
- `requirements.txt`: List of Python libraries needed to run the project.
- `ABOUT_PROJECT.md`: My personal statement and technical project report.

---

## Detectable Conditions

The system is trained to identify the following health states:
1. **Healthy**: No signs of the target diseases.
2. **Diabetes**: High blood sugar and related indicators.
3. **Anemia**: Issues with red blood cell count or hemoglobin.
4. **Heart Disease**: Cardiovascular risk markers and troponin levels.
5. **Thalassemia**: Hereditary blood disorders.
6. **Thrombocytopenia**: Dangerously low platelet levels.

---

## Model Performance

I compared four different algorithms to see which performs best on our health data:

| Model                 | Accuracy | F1 Score |
|-----------------------|----------|----------|
| **Random Forest**     | 95.1%    | 0.945    |
| **SVM**               | 94.9%    | 0.945    |
| **Decision Tree**     | 92.6%    | 0.925    |
| **Logistic Regression**| 81.9%    | 0.823    |

---

## About This Project

I chose to focus on healthcare because I believe information technology can have a massive impact on clinic efficiency in Ghana. During my studies in Computer Science at the University of Ghana, I became fascinated by how patterns in data can reveal health risks before they become critical. Building this system was a journey of learning how to handle real-world messy data, balance imbalanced classes, and design a user experience that is clear for clinical use.

Copyright 2026 Enock Queenson Eduafo. All rights reserved.
