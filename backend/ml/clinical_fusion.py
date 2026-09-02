"""
Smart Health Sync — Clinical Evidence Fusion Pipeline
Authors: Enock Queenson Eduafo & Christabel Araba Edumadze | University of Ghana 2026

Combines Stage A (Symptom/Clinical Evidence) and Stage B (Biomarker ML Model & Pattern Evidence)
into an auditable, deterministic, six-class prediction result.
"""

import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger("smarthealth.fusion")

ALLOWED_CLASSES = [
    "Diabetes",
    "Anemia",
    "Thalassemia",
    "Heart Disease",
    "Thrombocytopenia",
    "Healthy"
]


def calculate_symptom_evidence(symptoms: List[Any], preliminary_candidates: List[Dict[str, Any]] = None) -> Dict[str, float]:
    """
    Stage A: Compute symptom evidence scores (0 - 100) for each of the six allowed classes.
    """
    sym_strings = []
    if isinstance(symptoms, list):
        for item in symptoms:
            if isinstance(item, str):
                sym_strings.append(item.lower())
            elif isinstance(item, dict):
                disp = item.get("display_name") or item.get("name") or item.get("code") or ""
                sym_strings.append(str(disp).lower())

    symptom_text = " ".join(sym_strings)

    cand_map = {}
    if preliminary_candidates and isinstance(preliminary_candidates, list):
        for cand in preliminary_candidates:
            if isinstance(cand, dict) and cand.get("condition_name"):
                c_name = cand["condition_name"]
                score = float(cand.get("score", 50.0))
                cand_map[c_name] = score

    # Keyword mappings
    thromb_keywords = ["bruising", "petechiae", "bleeding", "purpura", "gums", "nosebleed", "unusual bleeding", "prolonged bleeding", "red spots", "purple spots", "skin spots"]
    anemia_keywords = ["fatigue", "weakness", "pallor", "pale", "dizziness", "shortness of breath", "breathless", "headache", "cold"]
    thal_keywords = ["fatigue", "pallor", "pale", "jaundice", "yellow", "spleen", "splenomegaly", "bone", "dark urine", "hereditary"]
    diab_keywords = ["thirst", "polydipsia", "urination", "polyuria", "frequent urination", "hunger", "polyphagia", "weight loss", "blurred vision", "slow healing"]
    hd_keywords = ["chest pain", "chest discomfort", "shortness of breath", "palpitations", "exercise intolerance", "dizziness", "fainting", "sweating"]

    def match_score(keywords):
        return sum(1 for kw in keywords if kw in symptom_text)

    thromb_matches = match_score(thromb_keywords)
    anemia_matches = match_score(anemia_keywords)
    thal_matches = match_score(thal_keywords)
    diab_matches = match_score(diab_keywords)
    hd_matches = match_score(hd_keywords)

    scores = {
        "Thrombocytopenia": min(100.0, thromb_matches * 30.0 + (cand_map.get("Thrombocytopenia", 0.0) * 0.5)),
        "Anemia": min(100.0, anemia_matches * 25.0 + (cand_map.get("Anemia", 0.0) * 0.4)),
        "Thalassemia": min(100.0, thal_matches * 25.0 + (cand_map.get("Thalassemia", 0.0) * 0.4)),
        "Diabetes": min(100.0, diab_matches * 30.0 + (cand_map.get("Diabetes", 0.0) * 0.5)),
        "Heart Disease": min(100.0, hd_matches * 30.0 + (cand_map.get("Heart Disease", 0.0) * 0.5)),
    }

    total_disease_sym = sum(scores.values())
    if total_disease_sym < 10.0:
        scores["Healthy"] = 90.0
    else:
        scores["Healthy"] = max(0.0, 100.0 - (total_disease_sym * 0.5))

    return {c: round(float(scores.get(c, 0.0)), 2) for c in ALLOWED_CLASSES}


def calculate_biomarker_evidence(raw_features: Dict[str, Any], raw_probabilities: Dict[str, float]) -> Dict[str, float]:
    """
    Stage B: Refine raw ML model probabilities with physiological biomarker pattern rules.
    """
    prob = {c: float(raw_probabilities.get(c, 0.0)) for c in ALLOWED_CLASSES}

    platelets = float(raw_features.get("Platelets", 250.0))
    glucose = float(raw_features.get("Glucose", 90.0))
    hba1c = float(raw_features.get("HbA1c", 5.2))
    hemo = float(raw_features.get("Hemoglobin", 14.0))
    mcv = float(raw_features.get("Mean Corpuscular Volume", 88.0))
    mch = float(raw_features.get("Mean Corpuscular Hemoglobin", 30.0))
    rbc = float(raw_features.get("Red Blood Cells", 4.8))
    trop = float(raw_features.get("Troponin", 0.01))
    chol = float(raw_features.get("Cholesterol", 180.0))
    ldl = float(raw_features.get("LDL Cholesterol", 95.0))

    # 1. Thrombocytopenia Pattern
    if platelets < 150.0 and platelets > 0:
        if platelets < 100.0:
            prob["Thrombocytopenia"] = max(prob["Thrombocytopenia"], 85.0)
        else:
            prob["Thrombocytopenia"] = max(prob["Thrombocytopenia"], 65.0)
    elif platelets >= 150.0:
        prob["Thrombocytopenia"] = min(prob["Thrombocytopenia"], 10.0)

    # 2. Diabetes Pattern
    if glucose > 126.0 or hba1c > 6.5:
        prob["Diabetes"] = max(prob["Diabetes"], 85.0)
    elif (100.0 <= glucose <= 125.0) or (5.7 <= hba1c <= 6.4):
        prob["Diabetes"] = max(prob["Diabetes"], 60.0)
    elif glucose < 100.0 and hba1c < 5.7:
        # Normal glucose & HbA1c -> Capped to prevent false positive Diabetes
        prob["Diabetes"] = min(prob["Diabetes"], 15.0)

    # 3. Thalassemia vs Anemia Pattern
    if hemo < 12.0 or mcv < 80.0:
        mentzer = (mcv / rbc) if rbc > 0 else 14.0
        if mentzer < 13.0 and mcv < 80.0:
            # Mentzer < 13 strongly indicates Thalassemia
            prob["Thalassemia"] = max(prob["Thalassemia"], 80.0)
            prob["Anemia"] = min(prob["Anemia"], 40.0)
        elif mentzer >= 13.0 and hemo < 12.0:
            # Mentzer >= 13 indicates Iron Deficiency Anemia
            prob["Anemia"] = max(prob["Anemia"], 75.0)
            prob["Thalassemia"] = min(prob["Thalassemia"], 35.0)

    # 4. Heart Disease Pattern
    if trop > 0.04:
        prob["Heart Disease"] = max(prob["Heart Disease"], 90.0)
    elif chol > 240.0 or ldl > 160.0:
        prob["Heart Disease"] = max(prob["Heart Disease"], 70.0)
    elif trop <= 0.04 and chol < 200.0 and ldl < 130.0:
        prob["Heart Disease"] = min(prob["Heart Disease"], 20.0)

    # 5. Healthy Pattern
    all_normal = (
        glucose < 100.0 and hba1c < 5.7 and hemo >= 12.0 and
        platelets >= 150.0 and trop <= 0.04 and chol < 200.0
    )
    if all_normal:
        prob["Healthy"] = max(prob["Healthy"], 85.0)

    return {c: round(float(prob.get(c, 0.0)), 2) for c in ALLOWED_CLASSES}


def fuse_clinical_evidence(
    symptoms: List[Any],
    raw_features: Dict[str, Any],
    raw_probabilities: Dict[str, float],
    preliminary_candidates: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Combines Stage A (Symptom Evidence) and Stage B (Biomarker Evidence) into
    auditable combined evidence, supporting symptoms/biomarkers, and final diagnosis.
    """
    stage_a_symptom = calculate_symptom_evidence(symptoms, preliminary_candidates)
    stage_b_biomarker = calculate_biomarker_evidence(raw_features, raw_probabilities)

    weight_sym = 0.35
    weight_bio = 0.65

    raw_combined = {}
    for c in ALLOWED_CLASSES:
        raw_combined[c] = round((weight_sym * stage_a_symptom[c]) + (weight_bio * stage_b_biomarker[c]), 2)

    combined_evidence = {c: min(100.0, max(0.0, raw_combined[c])) for c in ALLOWED_CLASSES}

    # Find highest evidence class
    predicted_diagnosis = max(combined_evidence, key=combined_evidence.get)
    confidence = combined_evidence[predicted_diagnosis]

    # Generate supporting & conflicting evidence lists
    supporting_symptoms = []
    supporting_biomarkers = []
    conflicting_evidence = []

    sym_strings = [
        s if isinstance(s, str) else (s.get("display_name") or s.get("name") or "")
        for s in (symptoms or [])
        if s
    ]
    if sym_strings:
        supporting_symptoms = sym_strings
    elif predicted_diagnosis == "Healthy":
        supporting_symptoms.append("No significant disease-specific symptoms.")

    platelets = float(raw_features.get("Platelets", 250.0))
    glucose = float(raw_features.get("Glucose", 90.0))
    hba1c = float(raw_features.get("HbA1c", 5.2))
    hemo = float(raw_features.get("Hemoglobin", 14.0))
    mcv = float(raw_features.get("Mean Corpuscular Volume", 88.0))
    trop = float(raw_features.get("Troponin", 0.01))

    if predicted_diagnosis == "Thrombocytopenia":
        if platelets < 150.0:
            supporting_biomarkers.append(f"Platelet count ({platelets:.1f} x10^3/uL) is in thrombocytopenia range (< 150 x10^3/uL).")

    elif predicted_diagnosis == "Diabetes":
        if glucose > 126.0 or hba1c > 6.5:
            supporting_biomarkers.append(f"Fasting glucose ({glucose:.1f} mg/dL) or HbA1c ({hba1c:.1f}%) is elevated.")
        if glucose < 100.0 and hba1c < 5.7:
            conflicting_evidence.append("Normal fasting glucose and HbA1c levels.")

    elif predicted_diagnosis == "Anemia":
        if hemo < 12.0:
            supporting_biomarkers.append(f"Hemoglobin concentration ({hemo:.1f} g/dL) is below normal (< 12 g/dL).")

    elif predicted_diagnosis == "Thalassemia":
        if mcv < 80.0:
            supporting_biomarkers.append(f"Mean Corpuscular Volume ({mcv:.1f} fL) indicates microcytosis (< 80 fL).")

    elif predicted_diagnosis == "Heart Disease":
        if trop > 0.04:
            supporting_biomarkers.append(f"Troponin level ({trop:.2f} ng/mL) is elevated (> 0.04 ng/mL).")

    elif predicted_diagnosis == "Healthy":
        supporting_biomarkers.append("All measured biomarkers fall within physiological baselines.")

    return {
        "predictedDiagnosis": predicted_diagnosis,
        "confidence": confidence,
        "symptomEvidence": stage_a_symptom,
        "biomarkerEvidence": stage_b_biomarker,
        "combinedEvidence": combined_evidence,
        "supportingSymptoms": supporting_symptoms,
        "supportingBiomarkers": supporting_biomarkers,
        "conflictingEvidence": conflicting_evidence,
    }
