"""
Smart Health Sync — Clinical Catalog Seed Data
Populates default symptom catalog, investigation catalog, and investigation rules.
"""

import json
import logging
from pathlib import Path
from backend.database.models import db, SymptomCatalog, InvestigationCatalog, InvestigationRule

logger = logging.getLogger("smarthealth.seed")

VOCAB_PATH = Path(__file__).resolve().parent / "symptom_vocabulary.json"


def _load_extended_vocabulary():
    if not VOCAB_PATH.exists():
        return []
    try:
        with open(VOCAB_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        logger.warning(f"[Seed] Could not read symptom_vocabulary.json: {exc}")
        return []

DEFAULT_SYMPTOMS = [
    {
        "code": "SYM_FATIGUE",
        "display_name": "Severe Fatigue & Weakness",
        "category": "General",
        "synonyms": ["tiredness", "exhaustion", "lethargy", "weakness", "lack of energy"],
        "description": "Persistent lack of energy or muscle weakness affecting daily activities."
    },
    {
        "code": "SYM_FEVER",
        "display_name": "Prolonged High Fever",
        "category": "General",
        "synonyms": ["fever", "pyrexia", "high body temperature", "febrile illness", "chills"],
        "description": "Elevated core body temperature above 38.0°C."
    },
    {
        "code": "SYM_ABDOMINAL_PAIN",
        "display_name": "Abdominal Pain / Cramps",
        "category": "Gastrointestinal",
        "synonyms": ["stomach pain", "stomach cramps", "belly ache", "abdominal distress"],
        "description": "Pain or discomfort localized in the stomach or pelvic area."
    },
    {
        "code": "SYM_HEADACHE",
        "display_name": "Severe Headache",
        "category": "Neurological",
        "synonyms": ["head pain", "migraine", "cephalea"],
        "description": "Continuous or throbbing pain in the head or upper neck."
    },
    {
        "code": "SYM_DIARRHEA_CONSTIPATION",
        "display_name": "Diarrhea or Altered Bowel Habits",
        "category": "Gastrointestinal",
        "synonyms": ["loose stools", "diarrhea", "constipation", "irregular bowel"],
        "description": "Frequent watery bowel movements or persistent intestinal motility changes."
    },
    {
        "code": "SYM_SHORTNESS_OF_BREATH",
        "display_name": "Shortness of Breath (Dyspnea)",
        "category": "Respiratory",
        "synonyms": ["breathlessness", "dyspnea", "difficulty breathing", "air hunger"],
        "description": "Sensation of difficult or uncomfortable breathing."
    },
    {
        "code": "SYM_CHEST_PAIN",
        "display_name": "Chest Pain or Pressure",
        "category": "Cardiovascular",
        "synonyms": ["angina", "chest pressure", "chest tightness", "cardiac pain"],
        "description": "Discomfort, tightness, or sharp pain in the thoracic region."
    },
    {
        "code": "SYM_PALPITATIONS",
        "display_name": "Heart Palpitations / Rapid Pulse",
        "category": "Cardiovascular",
        "synonyms": ["racing heart", "fluttering pulse", "tachycardia"],
        "description": "Awareness of abnormally fast or irregular heartbeats."
    },
    {
        "code": "SYM_POLYDIPSIA_POLYURIA",
        "display_name": "Excessive Thirst & Frequent Urination",
        "category": "Metabolic",
        "synonyms": ["frequent urination", "excessive thirst", "polyuria", "polydipsia"],
        "description": "Unusually high fluid intake requirement accompanied by frequent urinary output."
    },
    {
        "code": "SYM_WEIGHT_LOSS",
        "display_name": "Unexplained Weight Loss",
        "category": "Metabolic",
        "synonyms": ["rapid weight loss", "unintentional weight loss"],
        "description": "Significant decrease in body mass without deliberate diet or exercise."
    },
    {
        "code": "SYM_BRUISING_BLEEDING",
        "display_name": "Easy Bruising or Petechiae",
        "category": "Hematological",
        "synonyms": ["purpura", "bleeding gums", "nosebleeds", "petechiae", "skin spots"],
        "description": "Spontaneous pinpoint skin hemorrhages, mucosal bleeding, or frequent hematomas."
    },
    {
        "code": "SYM_PALLOR",
        "display_name": "Skin Pallor / Pale Mucosa",
        "category": "Hematological",
        "synonyms": ["pale skin", "pale gums", "pallor"],
        "description": "Unusual lightness of skin color or conjunctival mucous membranes."
    },
    {
        "code": "SYM_JAUNDICE",
        "display_name": "Jaundice (Yellowish Skin/Eyes)",
        "category": "Hepatic",
        "synonyms": ["yellow eyes", "yellow skin", "icterus"],
        "description": "Yellowish pigmentation of the skin and sclera from elevated bilirubin."
    },
    {
        "code": "SYM_DIZZINESS",
        "display_name": "Dizziness & Lightheadedness",
        "category": "Neurological",
        "synonyms": ["vertigo", "lightheadedness", "fainting feelings"],
        "description": "Sensation of unsteadiness, feeling faint, or lightheadedness."
    }
]

DEFAULT_INVESTIGATIONS = [
    {
        "code": "INV_FBC",
        "name": "Full Blood Count (FBC / CBC)",
        "category": "Laboratory",
        "biomarker_keys": [
            "Hemoglobin", "Platelets", "White Blood Cells", "Red Blood Cells",
            "Hematocrit", "Mean Corpuscular Volume", "Mean Corpuscular Hemoglobin",
            "Mean Corpuscular Hemoglobin Concentration"
        ],
        "description": "Evaluates overall hematological status including RBC, WBC, Hemoglobin, and Platelet levels."
    },
    {
        "code": "INV_GLUCOSE_HBA1C",
        "name": "Fasting Plasma Glucose & HbA1c Panel",
        "category": "Laboratory",
        "biomarker_keys": ["Glucose", "HbA1c", "Insulin"],
        "description": "Assesses blood glucose concentration and 3-month glycemic control for diabetes screening."
    },
    {
        "code": "INV_LIPID_PROFILE",
        "name": "Complete Lipid Profile Panel",
        "category": "Laboratory",
        "biomarker_keys": ["Cholesterol", "Triglycerides", "LDL Cholesterol", "HDL Cholesterol"],
        "description": "Measures total cholesterol, LDL, HDL, and triglycerides for cardiovascular risk stratifying."
    },
    {
        "code": "INV_CARDIAC_MARKERS",
        "name": "Cardiac Troponin & Inflammatory Panel",
        "category": "Laboratory",
        "biomarker_keys": ["Troponin", "C-reactive Protein", "Heart Rate", "Systolic Blood Pressure", "Diastolic Blood Pressure"],
        "description": "Evaluates cardiac muscle strain and systemic vascular inflammatory status."
    },
    {
        "code": "INV_LFT_KFT",
        "name": "Metabolic, Liver & Renal Panel (LFT/KFT)",
        "category": "Laboratory",
        "biomarker_keys": ["ALT", "AST", "Creatinine", "BMI"],
        "description": "Assesses hepatic transaminases, kidney filtration, and body composition index."
    },
    {
        "code": "INV_WIDAL_TYPHOID",
        "name": "Widal Agglutination Serology Test",
        "category": "Special Test",
        "biomarker_keys": ["Widal O Titer", "Widal H Titer"],
        "description": "Serological test measuring somatic (O) and flagellar (H) antibodies against Salmonella enterica serovar Typhi."
    }
]

DEFAULT_RULES = [
    {
        "condition_name": "Anemia",
        "recommended_code": "INV_FBC",
        "priority": "High",
        "reason": "Full Blood Count is required to quantify Hemoglobin concentration, Hematocrit, and RBC count."
    },
    {
        "condition_name": "Diabetes",
        "recommended_code": "INV_GLUCOSE_HBA1C",
        "priority": "High",
        "reason": "Fasting Glucose and HbA1c are diagnostic gold standards for glycemic control assessment."
    },
    {
        "condition_name": "Heart Disease",
        "recommended_code": "INV_CARDIAC_MARKERS",
        "priority": "High",
        "reason": "Cardiac Troponin and CRP markers are essential to evaluate cardiac muscle injury and inflammatory stress."
    },
    {
        "condition_name": "Heart Disease",
        "recommended_code": "INV_LIPID_PROFILE",
        "priority": "High",
        "reason": "Lipid panel (Cholesterol, LDL, HDL, Triglycerides) evaluates atherogenic risk factors."
    },
    {
        "condition_name": "Thalassemia",
        "recommended_code": "INV_FBC",
        "priority": "High",
        "reason": "Red cell indices (MCV, MCH) on Full Blood Count evaluate microcytic hypochromic erythrocyte patterns."
    },
    {
        "condition_name": "Thrombocytopenia",
        "recommended_code": "INV_FBC",
        "priority": "High",
        "reason": "Platelet counts from Full Blood Count directly quantify clotting deficit and hemorrhage risk."
    },
    {
        "condition_name": "Typhoid Fever",
        "recommended_code": "INV_WIDAL_TYPHOID",
        "priority": "High",
        "reason": "Widal agglutination serology detects active or past Salmonella Typhi antibody response."
    },
    {
        "condition_name": "Typhoid Fever",
        "recommended_code": "INV_LFT_KFT",
        "priority": "Medium",
        "reason": "Liver enzymes (ALT/AST) evaluate systemic hepatic involvement in Salmonella infections."
    }
]


def seed_clinical_catalogs():
    """Populate default + extended symptom catalog, investigation catalog,
    and rules. Idempotent per-item (checked by unique code), so it's safe
    to run on every deploy and will pick up newly added vocabulary."""
    try:
        # 1. Seed Symptom Catalog — curated defaults + extended vocabulary,
        #    added by code so re-running never duplicates existing entries.
        existing_codes = {row[0] for row in db.session.query(SymptomCatalog.code).all()}
        all_symptoms = DEFAULT_SYMPTOMS + _load_extended_vocabulary()
        added = 0
        for s in all_symptoms:
            if s["code"] in existing_codes:
                continue
            sc = SymptomCatalog(
                code=s["code"],
                display_name=s["display_name"],
                category=s.get("category"),
                synonyms_json=json.dumps(s.get("synonyms", [])),
                description=s.get("description"),
            )
            db.session.add(sc)
            existing_codes.add(s["code"])
            added += 1
        if added:
            db.session.commit()
            logger.info(f"[Seed] Added {added} new SymptomCatalog entries.")

        # 2. Seed Investigation Catalog
        if InvestigationCatalog.query.count() == 0:
            for inv in DEFAULT_INVESTIGATIONS:
                ic = InvestigationCatalog(
                    code=inv["code"],
                    name=inv["name"],
                    category=inv["category"],
                    biomarker_keys_json=json.dumps(inv["biomarker_keys"]),
                    description=inv["description"]
                )
                db.session.add(ic)
            db.session.commit()
            logger.info("[Seed] Seeded default InvestigationCatalog items.")

        # 3. Seed Investigation Rules
        if InvestigationRule.query.count() == 0:
            inv_map = {ic.code: ic.id for ic in InvestigationCatalog.query.all()}
            for r in DEFAULT_RULES:
                inv_id = inv_map.get(r["recommended_code"])
                if inv_id:
                    ir = InvestigationRule(
                        condition_name=r["condition_name"],
                        recommended_investigation_id=inv_id,
                        priority=r["priority"],
                        reason=r["reason"]
                    )
                    db.session.add(ir)
            db.session.commit()
            logger.info("[Seed] Seeded default InvestigationRules items.")

    except Exception as exc:
        db.session.rollback()
        logger.error(f"[Seed] Failed to seed clinical catalogs: {exc}")
