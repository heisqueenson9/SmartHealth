"""
Smart Health Sync — API Routes (RESTful endpoints)
Authors: Enock Queenson Eduafo & Christabel Araba Edumadze | University of Ghana 2026
"""

import json
import logging
import os
from flask import Blueprint, request, jsonify, session, current_app

from backend.database.models import db, DiagnosticRecord, User, Patient, DoctorPatientConnection, DoctorTechnicianConnection
from backend.ml.model_manager import model_manager
from backend.ml.preprocessing.normalization import normalize_input


logger  = logging.getLogger("smarthealth.api")
api_bp  = Blueprint("api", __name__)


@api_bp.errorhandler(Exception)
def _handle_api_exception(exc):
    """Blueprint-wide safety net. Catches anything not already caught inside
    an individual view function, rolls back the DB session so a failed
    transaction can't poison the next query on this connection, logs the
    full traceback, and returns clean JSON instead of a bare 500 page."""
    from werkzeug.exceptions import HTTPException
    if isinstance(exc, HTTPException):
        return exc  # let normal 404s/405s/etc pass through unchanged
    db.session.rollback()
    logger.exception(f"[API] Unhandled exception: {exc}")
    return jsonify({
        "error": "Internal server error.",
        "status": "failed",
        "details": str(exc) if current_app.debug else None,
    }), 500


# ── /api/health ──────────────────────────────────────────────
@api_bp.route("/health", methods=["GET"])
def health():
    """Readiness health check verifying DB connectivity and ML models.
    
    Always returns 200 so Render's health check doesn't tear down the
    service, but includes degraded status and error details in the
    response body for debugging.
    """
    from sqlalchemy import text
    checks = {
        "database": False,
        "models": False,
    }
    errors = {}

    # Check startup status
    startup_error = current_app.config.get("_STARTUP_ERROR")
    if startup_error:
        errors["startup"] = startup_error

    try:
        db.session.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as exc:
        logger.exception("Database health check failed: %s", exc)
        errors["database"] = str(exc)

    try:
        report = model_manager.health_report()
        checks["models"] = bool(
            report.get("loaded_models") and report.get("scaler_loaded") and report.get("encoder_loaded")
        )
        if not checks["models"]:
            errors["models"] = {
                "loaded": report.get("loaded_models", []),
                "missing": report.get("missing_models", []),
                "corrupted": report.get("corrupted_models", []),
            }
    except Exception as exc:
        logger.exception("Model health check failed.")
        errors["models"] = str(exc)

    ready = all(checks.values())
    result = {
        "status": "healthy" if ready else "degraded",
        "service": "Smart Health Sync API",
        "version": "2.0.0",
        "checks": checks,
    }
    if errors:
        result["errors"] = errors

    # Always return 200 so Render keeps the service alive for debugging
    return jsonify(result), 200


# ── /api/health/models ───────────────────────────────────────
@api_bp.route("/health/models", methods=["GET"])
def health_models():
    """
    Detailed ML model health status.

    Returns:
        JSON with loaded/missing/corrupted model lists and directory info.
    """
    report = model_manager.health_report()
    status_code = 200 if report["loaded_models"] else 503
    return jsonify(report), status_code


# ── /api/predict ─────────────────────────────────────────────
@api_bp.route("/predict", methods=["POST"])
def predict():
    """
    Clinical diagnostic inference endpoint.

    Accepts:
        POST JSON body:
        {
            "features": {
                "Glucose": 0.72,
                "Cholesterol": 0.45,
                ... (24 biomarkers)
            },
            "model": "random_forest"  (optional)
        }

    Returns:
        Structured prediction with confidence, probabilities, and recommendations.
    """
    try:
        # Check permissions: must be verified doctor or admin
        role = session.get("role")
        status = session.get("status")
        if role != "admin" and (role != "doctor" or status != "approved"):
            return jsonify({
                "error": "Access denied. Diagnostic features require a verified doctor account.",
                "status": "failed"
            }), 403

        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({
                "error":  "Missing or malformed JSON body.",
                "status": "failed",
            }), 400

        features_dict = data.get("features")
        if features_dict is None:
            return jsonify({
                "error":   "Missing 'features' key in request body.",
                "status": "failed",
            }), 400

        if not isinstance(features_dict, dict):
            return jsonify({
                "error":  "'features' must be a JSON object (dict).",
                "status": "failed",
            }), 400

        category = str(data.get("category", "all")).lower().strip()

        # Raw clinical healthy baseline — used to fill any missing biomarkers.
        # model_manager.predict() applies StandardScaler internally, so we pass
        # raw clinical values (not pre-normalised 0-1 values).
        HEALTHY_BASELINE = {
            "Glucose": 85.0, "Cholesterol": 180.0, "Hemoglobin": 15.0,
            "Platelets": 250.0, "White Blood Cells": 7.0, "Red Blood Cells": 4.8,
            "Hematocrit": 42.0, "Mean Corpuscular Volume": 88.0,
            "Mean Corpuscular Hemoglobin": 30.0, "Mean Corpuscular Hemoglobin Concentration": 33.5,
            "Insulin": 10.0, "BMI": 22.0, "Systolic Blood Pressure": 120.0,
            "Diastolic Blood Pressure": 80.0, "Triglycerides": 110.0,
            "HbA1c": 5.2, "LDL Cholesterol": 90.0, "HDL Cholesterol": 55.0,
            "ALT": 24.0, "AST": 22.0, "Heart Rate": 72.0, "Creatinine": 0.9,
            "Troponin": 0.01, "C-reactive Protein": 2.0,
        }

        # Validate that entered values are numeric
        for f_name, f_val in features_dict.items():
            try:
                float(f_val)
            except (ValueError, TypeError):
                return jsonify({
                    "error": f"Biomarker '{f_name}' must be a numeric value.",
                    "status": "failed"
                }), 400

        # Merge entered raw values over the healthy baseline
        full_features = HEALTHY_BASELINE.copy()
        for k, v in features_dict.items():
            try:
                full_features[k] = float(v)
            except (ValueError, TypeError):
                pass

        model_key = "random_forest"
        patient_ref = str(data.get("patient_reference", "")).strip() or None
        linked_patient_id = data.get("patient_id")

        if linked_patient_id:
            from backend.database.models import Patient
            patient = db.session.get(Patient, int(linked_patient_id))
            if patient:
                if not patient_ref or patient_ref.startswith("[Auto") or patient_ref.strip() == f"{patient.full_name}":
                    import random
                    rand_suffix = "".join(random.choices("0123456789ABCDEF", k=6))
                    initials = "".join([w[0].upper() for w in patient.full_name.split() if w])[:2]
                    patient_ref = f"SHS-{initials}-{rand_suffix}"
        elif not patient_ref:
            import random
            rand_suffix = "".join(random.choices("0123456789ABCDEF", k=6))
            patient_ref = f"SHS-GEN-{rand_suffix}"

        # Custom logic for Typhoid
        if category == "typhoid":
            raw_widal_o = float(features_dict.get("Widal O Titer", 0.5))
            raw_widal_h = float(features_dict.get("Widal H Titer", 0.5))

            def normalize_widal(val):
                if val > 1.0:
                    if val >= 320: return 0.95
                    elif val >= 160: return 0.85
                    elif val >= 80: return 0.70
                    elif val >= 40: return 0.40
                    else: return 0.20
                return val

            widal_o = normalize_widal(raw_widal_o)
            widal_h = normalize_widal(raw_widal_h)
            wbc = float(features_dict.get("White Blood Cells", 0.45))
            ast = float(features_dict.get("AST", 0.14))
            alt = float(features_dict.get("ALT", 0.15))

            symptoms = data.get("symptoms", {})
            present_symptoms = [name for name, present in symptoms.items() if present]

            symptom_labels = {
                "fever": "Prolonged High Fever",
                "abdominal_pain": "Abdominal Pain/Cramps",
                "headache": "Severe Headache",
                "diarrhea_constipation": "Diarrhea/Constipation",
                "fatigue": "Severe Fatigue & Weakness"
            }
            symptom_strs = [symptom_labels[s] for s in present_symptoms if s in symptom_labels]

            # Clinical criteria for Typhoid Fever
            has_elevated_titers = widal_o > 0.55 or widal_h > 0.55
            has_fever = symptoms.get("fever", False)
            has_other_symptoms_count = sum([
                symptoms.get("abdominal_pain", False),
                symptoms.get("headache", False),
                symptoms.get("diarrhea_constipation", False),
                symptoms.get("fatigue", False)
            ])

            has_typhoid = has_elevated_titers and (has_fever or has_other_symptoms_count >= 2)

            if has_typhoid:
                pred_label = "Typhoid Fever"
                
                # Dynamic confidence based on symptoms and titers
                symptom_score = 0
                if has_fever: symptom_score += 30
                if symptoms.get("abdominal_pain"): symptom_score += 20
                if symptoms.get("headache"): symptom_score += 15
                if symptoms.get("diarrhea_constipation"): symptom_score += 15
                if symptoms.get("fatigue"): symptom_score += 10

                lab_score = 0
                if widal_o > 0.55: lab_score += (widal_o - 0.55) / 0.45 * 40
                if widal_h > 0.55: lab_score += (widal_h - 0.55) / 0.45 * 30
                if wbc < 0.4 or wbc > 0.7: lab_score += 15
                if ast > 0.5 or alt > 0.5: lab_score += 15

                confidence = round(45.0 + (symptom_score + lab_score) * 0.45, 2)
                confidence = min(95.0, max(55.0, confidence))

                if symptom_strs:
                    symptom_text = ", and ".join([", ".join(symptom_strs[:-1]), symptom_strs[-1]]) if len(symptom_strs) > 1 else symptom_strs[0]
                    desc = f"Elevated Widal titers and clinical presentation of {symptom_text} strongly suggest active Typhoid Fever."
                else:
                    desc = "Elevated Widal test titers and clinical symptoms indicate active Typhoid Fever."

                exps = []
                if raw_widal_o > 1.0:
                    exps.append(f"Widal O Titer is elevated at 1:{int(raw_widal_o)} dilution (somatically positive).")
                else:
                    exps.append(f"Widal O Titer normalized score is elevated ({widal_o:.2f}).")
                if raw_widal_h > 1.0:
                    exps.append(f"Widal H Titer is elevated at 1:{int(raw_widal_h)} dilution (flagellar positive).")
                else:
                    exps.append(f"Widal H Titer normalized score is elevated ({widal_h:.2f}).")
                if wbc < 0.4:
                    exps.append(f"White Blood Cell count is low-normal ({wbc:.2f} score), which is characteristic of Salmonella infection.")
                elif wbc > 0.7:
                    exps.append(f"White Blood Cell count is elevated ({wbc:.2f} score), indicating active system-wide inflammatory response.")
                if ast > 0.5 or alt > 0.5:
                    exps.append(f"Hepatic biomarkers AST ({ast:.2f}) / ALT ({alt:.2f}) indicate mild liver involvement or cell stress.")
                if symptom_strs:
                    exps.append(f"Patient presents with key clinical signs: {', '.join(symptom_strs)}.")
                
                recs = [
                    "Initiate clinical review for targeted antibiotic therapy (e.g. Ciprofloxacin or Ceftriaxone as per local protocols).",
                    "Monitor core body temperature daily and maintain strict oral hydration.",
                    "Practice strict hand hygiene and food/water safety guidelines to prevent transmission."
                ]
            else:
                pred_label = "Healthy"

                # Dynamic confidence for healthy verdict
                if has_elevated_titers and not (has_fever or has_other_symptoms_count >= 2):
                    confidence = round(60.0 + (1.0 - max(widal_o, widal_h)) * 30.0, 2)
                    desc = "Elevated Widal titers detected without active clinical symptoms (Fever/Abdominal pain). Suggests past exposure or vaccination, not active infection."
                    exps = [f"Elevated somatic/flagellar titers (O: {widal_o:.2f}, H: {widal_h:.2f}) suggest immunogenic exposure or history, but lack of diagnostic clinical symptoms rules out active Typhoid Fever."]
                    recs = [
                        "Monitor patient for onset of clinical symptoms (fever, chills, abdominal pain).",
                        "Evaluate clinical history for past Typhoid vaccine or prior infections."
                    ]
                elif symptom_strs:
                    confidence = round(55.0 + (1.0 - max(widal_o, widal_h)) * 25.0, 2)
                    desc = f"Patient presents with symptoms of {', '.join(symptom_strs)}, but laboratory Widal test titers are normal, making Typhoid Fever unlikely."
                    exps = [
                        "Widal titers (O and H) do not show clinical significance for Salmonella infection.",
                        f"Reported symptoms ({', '.join(symptom_strs)}) may be related to other non-Salmonella febrile illnesses (e.g., malaria, gastroenteritis)."
                    ]
                    recs = [
                        "Investigate alternative causes of reported febrile/clinical symptoms (e.g., malaria, gastroenteritis).",
                        "Monitor symptoms and repeat clinical review if fever persists."
                    ]
                else:
                    confidence = round(75.0 + (1.0 - max(widal_o, widal_h)) * 20.0, 2)
                    desc = "Widal titers and liver biomarkers are within physiological baselines with no reported symptoms."
                    exps = ["Widal O and H titers do not indicate clinical significance for Salmonella infection."]
                    recs = ["Maintain regular sanitary and hygiene practices."]

                confidence = min(98.0, max(50.0, confidence))

            result = {
                "prediction": pred_label,
                "confidence": confidence,
                "probabilities": {pred_label: confidence, "Healthy" if pred_label != "Healthy" else "Typhoid Fever": round(100 - confidence, 2)},
                "feature_importance": {
                    "Widal O Titer": 40.0,
                    "Widal H Titer": 35.0,
                    "White Blood Cells": 15.0,
                    "AST": 5.0,
                    "ALT": 5.0
                },
                "description": desc,
                "explanations": exps,
                "symptoms": symptom_strs,
                "recommendations": recs + [
                    "Consult a licensed medical professional for formal clinical review.",
                    "Ensure all biomarker inputs match your latest laboratory report."
                ],
                "model_used": "rule_based_typhoid",
                "status": "success",
            }
        else:
            result = model_manager.predict(full_features, model_key)

        user_id = session.get("user_id")
        if user_id:
            try:
                draft_id = data.get("draft_id") or data.get("record_id")
                record = None
                if draft_id and role in ("doctor", "admin"):
                    record = DiagnosticRecord.query.filter_by(id=int(draft_id), user_id=user_id, status="draft").first()
                
                if record:
                    record.biomarkers_json = json.dumps(features_dict)
                    record.result_json = json.dumps(result)
                    record.prediction_label = result["prediction"]
                    record.confidence_score = result["confidence"]
                    record.model_version = result.get("model_used")
                    record.status = "draft"
                else:
                    record = DiagnosticRecord(
                        user_id=user_id,
                        patient_reference=patient_ref,
                        biomarkers_json=json.dumps(features_dict),
                        result_json=json.dumps(result),
                        prediction_label=result["prediction"],
                        confidence_score=result["confidence"],
                        model_version=result.get("model_used"),
                        status="draft",
                    )
                    if linked_patient_id is not None:
                        from backend.database.models import Patient
                        patient = db.session.get(Patient, int(linked_patient_id))
                        if patient:
                            record.patient_id = patient.id
                    db.session.add(record)
                
                db.session.flush() # get record.id
                
                # Add notification
                from backend.database.models import Notification, Patient
                p_name = patient_ref
                if record.patient_id:
                    patient = db.session.get(Patient, record.patient_id)
                    if patient:
                        p_name = patient.full_name
                
                notif = Notification(
                    user_id=user_id,
                    message=f"Prediction completed for patient case {p_name}."
                )
                db.session.add(notif)
                
                db.session.commit()
                result["record_id"] = record.id
            except Exception as db_exc:
                db.session.rollback()
                logger.warning(f"[API] Could not persist diagnostic record: {db_exc}")

        logger.info(
            f"[API] Prediction: {result['prediction']} | "
            f"confidence={result['confidence']}% | model={result['model_used']}"
        )
        return jsonify(result), 200

    except ValueError as ve:
        logger.warning(f"[API] Validation error: {ve}")
        return jsonify({
            "error":  str(ve),
            "status": "failed",
            "available_features": model_manager.features,
        }), 400

    except RuntimeError as re:
        logger.error(f"[API] Model runtime error: {re}")
        return jsonify({
            "error":  "Diagnostic models not available.",
            "details": {
                "message":         str(re),
                "missing_models":  model_manager.missing_models,
                "corrupted_models":model_manager.corrupted_models,
                "models_directory":str(model_manager.models_dir),
            },
            "status": "failed",
        }), 503

    except Exception as exc:
        logger.exception(f"[API] Unexpected error during prediction: {exc}")
        return jsonify({
            "error":  "Internal server error.",
            "status": "failed",
        }), 500


# ── /api/history ─────────────────────────────────────────────
@api_bp.route("/history", methods=["GET"])
def diagnosis_history():
    """Return diagnosis history for the logged-in user (or all for admin)."""
    user_id = session.get("user_id")
    role = session.get("role")
    if not user_id:
        return jsonify({"error": "Authentication required."}), 401

    if role == "admin":
        records = DiagnosticRecord.query.order_by(DiagnosticRecord.created_at.desc()).limit(100).all()
    elif role == "doctor" and session.get("status") == "approved":
        records = (
            DiagnosticRecord.query.filter_by(user_id=user_id)
            .order_by(DiagnosticRecord.created_at.desc())
            .limit(100)
            .all()
        )
    else:
        return jsonify({"error": "Access denied."}), 403

    return jsonify({
        "status": "success",
        "records": [r.to_dict() for r in records],
    }), 200


# ── /api/history/<id> ────────────────────────────────────────
@api_bp.route("/history/<int:record_id>", methods=["GET"])
def diagnosis_record(record_id):
    """Return a single diagnosis record."""
    user_id = session.get("user_id")
    role = session.get("role")
    if not user_id:
        return jsonify({"error": "Authentication required."}), 401

    record = db.session.get(DiagnosticRecord, record_id)
    if not record:
        return jsonify({"error": "Record not found."}), 404

    if role == "admin":
        pass
    elif role == "doctor" and int(record.user_id) == int(user_id):
        pass
    else:
        return jsonify({"error": "Access denied."}), 403

    return jsonify({"status": "success", "record": record.to_dict()}), 200


# ── /api/models ──────────────────────────────────────────────
@api_bp.route("/models", methods=["GET"])
def list_models():
    """Return metadata about available ML classifiers."""
    return jsonify({
        "available_models": list(model_manager.loaded_models.keys()),
        "default_model":    "random_forest",
        "features":         model_manager.features,
        "classes":          model_manager.classes,
        "model_metadata":   _build_metadata(),
    }), 200


# ── /api/metadata ────────────────────────────────────────────
@api_bp.route("/metadata", methods=["GET"])
def metadata():
    """API metadata root."""
    return jsonify({
        "project":   "Smart Health Sync",
        "version":   "2.0.0",
        "developer": {
            "names":       "Enock Queenson Eduafo & Christabel Araba Edumadze",
            "student_ids": "11014444 & 11348914",
            "institution": "University of Ghana",
            "supervisor":  "Professor Solomon Mensah",
            "year":        "2026",
        },
        "endpoints": {
            "/api/health":        "GET  — System health check",
            "/api/health/models": "GET  — ML model health report",
            "/api/predict":       "POST — Clinical diagnostic inference",
            "/api/history":       "GET  — Diagnosis history",
            "/api/models":        "GET  — Available classifiers",
        },
        "supported_conditions": model_manager.classes,
    }), 200


# ── Helpers ──────────────────────────────────────────────────
def _build_metadata() -> dict:
    """Build classifier metadata from results_summary if available."""
    base = {
        "random_forest":       {"accuracy": 0.9507, "framework": "scikit-learn", "status": "production"},
        "svm":                 {"accuracy": 0.9489, "framework": "scikit-learn", "status": "valid"},
        "decision_tree":       {"accuracy": 0.9261, "framework": "scikit-learn", "status": "valid"},
        "logistic_regression": {"accuracy": 0.8187, "framework": "scikit-learn", "status": "baseline"},
    }
    if model_manager.summary:
        for m in model_manager.summary.get("models", []):
            key = m.get("name", "").lower().replace(" ", "_")
            key_map = {
                "random_forest": "random_forest",
                "support_vector_machine": "svm",
                "decision_tree": "decision_tree",
                "logistic_regression": "logistic_regression",
            }
            mapped = key_map.get(key)
            if mapped:
                base[mapped].update({
                    "accuracy":  m.get("accuracy"),
                    "precision": m.get("precision"),
                    "recall":    m.get("recall"),
                    "f1_score":  m.get("f1_score"),
                    "cv_mean":   m.get("cv_mean"),
                })
    return base





# ── POST /history/<id>/explain ───────────────────────────────
@api_bp.route("/history/<int:record_id>/explain", methods=["POST"])
def explain_diagnosis(record_id):
    """Call Groq API to answer patient questions about a diagnosis report."""
    import os
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Authentication required."}), 401
        
    record = db.session.get(DiagnosticRecord, record_id)
    if not record:
        return jsonify({"error": "Diagnosis record not found."}), 404
        
    # Security check: only the linked patient, diagnosing doctor, or admin can query
    role = session.get("role")
    if role == "patient":
        from backend.database.models import Patient
        profile = Patient.query.filter_by(user_id=user_id).first()
        if not profile or record.patient_id != profile.id:
            return jsonify({"error": "Access denied."}), 403
        if record.status != "approved":
            return jsonify({"error": "Access denied. Diagnosis is not finalized."}), 403
    elif role == "doctor":
        if int(record.user_id) != int(user_id):
            return jsonify({"error": "Access denied."}), 403
    elif role != "admin":
        return jsonify({"error": "Access denied."}), 403
        
    data = request.get_json(force=True, silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Message is required."}), 400
        
    groq_api_key = current_app.config.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        return jsonify({
            "status": "error",
            "reply": "The AI explainer assistant is currently offline (missing configuration). Please consult your healthcare provider directly for any questions."
        }), 200
        
    try:
        import json
        
        # Format biomarker data for context
        biomarkers = json.loads(record.biomarkers_json) if record.biomarkers_json else {}
        biomarkers_list = []
        for k, v in biomarkers.items():
            biomarkers_list.append(f"- {k}: {v:.2f}")
        biomarkers_text = "\n".join(biomarkers_list)
        
        system_prompt = (
            "You are an empathetic, clear, and professional clinical explanation assistant for Smart Health Sync.\n"
            "Explain the patient's diagnosis report context clearly and answer their questions simply. Use clear language and bullet points.\n"
            "Explain what each high/low biomarker indicates related to their condition.\n"
            "IMPORTANT: Always include a short disclaimer that you are an academic AI assistant prototype and they should verify details with their doctor.\n\n"
            f"REPORT DETAILS:\n"
            f"Predicted Condition: {record.prediction_label}\n"
            f"AI Confidence: {record.confidence_score:.1f}%\n"
            f"Doctor's Remarks: {record.doctor_remarks or 'No remarks added by doctor yet.'}\n\n"
            f"BIOMARKER LEVEL SCORES (normalised 0.0 to 1.0):\n"
            f"{biomarkers_text}"
        )
        
        try:
            from groq import Groq
            client = Groq(api_key=groq_api_key)
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.5,
                max_tokens=800
            )
            reply = completion.choices[0].message.content
            return jsonify({"status": "success", "reply": reply}), 200
        except ImportError:
            # Fallback to standard requests if SDK is not installed
            import requests
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "temperature": 0.5,
                "max_tokens": 800
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=15)
            if res.status_code != 200:
                logger.warning(f"Groq API returned status {res.status_code}: {res.text}")
                return jsonify({
                    "status": "error",
                    "reply": "The AI explainer is temporarily busy. Please try again shortly or speak with your doctor."
                }), 200
                
            res_data = res.json()
            reply = res_data["choices"][0]["message"]["content"]
            return jsonify({"status": "success", "reply": reply}), 200
            
    except Exception as e:
        logger.exception(f"Error calling Groq API: {e}")
        return jsonify({
            "status": "error",
            "reply": "An error occurred while calling the AI model. Please speak to your doctor."
        }), 200


@api_bp.route("/history/<int:record_id>/approve", methods=["POST"])
def approve_diagnosis(record_id):
    """Doctor approves a diagnosis draft, adding remarks, observations, treatment notes, and finalizing."""
    user_id = session.get("user_id")
    role = session.get("role")
    
    if not user_id or role not in ("doctor", "admin"):
        return jsonify({"error": "Access denied. Doctor account required."}), 403
        
    record = db.session.get(DiagnosticRecord, record_id)
    if not record:
        return jsonify({"error": "Diagnosis record not found."}), 404
        
    if role == "doctor" and int(record.user_id) != int(user_id):
        return jsonify({"error": "Access denied. You can only sign off on your own diagnoses."}), 403

    biomarkers_check = json.loads(record.biomarkers_json) if record.biomarkers_json else {}
    if not biomarkers_check:
        return jsonify({
            "error": "This case has no clinical data yet. Complete Symptoms, Investigations, and Lab Results before approving."
        }), 409
        
    data = request.get_json(force=True, silent=True) or {}
    remarks = data.get("remarks", "").strip()
    model_key = "random_forest"
    
    # Extract review details
    final_diag = data.get("final_diagnosis", "").strip()
    observations = data.get("observations", "").strip()
    treatment_notes = data.get("treatment_notes", "").strip()
    ai_exp = data.get("ai_explanation", "").strip()
    sections = data.get("report_sections")  # Expect list
    signature = data.get("doctor_signature", "").strip()
    
    try:
        biomarkers = json.loads(record.biomarkers_json) if record.biomarkers_json else {}
        result = model_manager.predict(biomarkers, model_key)
        
        # If user didn't supply final_diag, fallback to the model prediction
        if not final_diag:
            final_diag = result["prediction"]
            
        record.prediction_label = final_diag
        record.confidence_score = result["confidence"]
        record.model_version = result.get("model_used")
        
        # Merge updated fields into result_json
        result["prediction"] = final_diag
        result["description"] = observations or result.get("description")
        result["recommendations"] = [treatment_notes] if treatment_notes else result.get("recommendations", [])
        record.result_json = json.dumps(result)
    except Exception as exc:
        logger.warning(f"Error running model {model_key} on draft: {exc}")
        if not final_diag:
            final_diag = record.prediction_label
            
    record.prediction_label = final_diag
    record.doctor_remarks = remarks or None
    record.final_diagnosis = final_diag
    record.observations = observations or None
    record.treatment_notes = treatment_notes or None
    record.ai_explanation = ai_exp or None
    record.report_sections = json.dumps(sections) if sections is not None else None
    record.doctor_signature = signature or None
    record.status = "approved"
    
    # Add notification
    from backend.database.models import Notification, Patient
    p_name = record.patient_reference or f"SHS-{record.id}"
    if record.patient_id:
        patient = db.session.get(Patient, record.patient_id)
        if patient:
            p_name = patient.full_name
            
    notif = Notification(
        user_id=user_id,
        message=f"Report successfully generated for patient case {p_name}."
    )
    db.session.add(notif)
    db.session.commit()
    
    # Force refresh the record and ensure relationships are loaded to prevent empty JSON/PDF data
    db.session.refresh(record)
    if record.patient_id and not record.patient:
        from backend.database.models import Patient
        record.patient = db.session.get(Patient, record.patient_id)
    
    logger.info(f"[API] Doctor {user_id} approved record {record_id} as finalized.")
    return jsonify({
        "status": "success",
        "message": "Diagnosis successfully approved and final report generated.",
        "record": record.to_dict()
    }), 200


# ── POST /api/technician/connect ────────────────────────────
@api_bp.route("/technician/connect", methods=["POST"])
def technician_connect_doctor():
    user_id = session.get("user_id")
    role = session.get("role")
    if not user_id or role != "technician":
        return jsonify({"error": "Unauthorized. Technician access required."}), 403
    data = request.get_json(force=True, silent=True) or {}
    doctor_id = data.get("doctor_id")
    if not doctor_id:
        return jsonify({"error": "Doctor ID is required."}), 400
    doctor = User.query.filter_by(id=doctor_id, role="doctor", status="approved").first()
    if not doctor:
        return jsonify({"error": "Verified doctor not found."}), 404
    from backend.database.models import DoctorTechnicianConnection
    existing = DoctorTechnicianConnection.query.filter_by(doctor_id=doctor.id, technician_id=user_id).first()
    if existing:
        if existing.status == "rejected":
            existing.status = "pending"
            existing.created_at = datetime.now(timezone.utc)
            db.session.commit()
            return jsonify({"status": "success", "message": "Connection request re-submitted."}), 200
        return jsonify({"error": f"Connection request is already {existing.status}."}), 400
    connection = DoctorTechnicianConnection(doctor_id=doctor.id, technician_id=user_id, status="pending")
    db.session.add(connection)
    db.session.commit()
    return jsonify({"status": "success", "message": "Connection request sent successfully."}), 201


# ── POST /api/doctor/respond-technician ──────────────────────
@api_bp.route("/doctor/respond-technician", methods=["POST"])
def doctor_respond_technician():
    user_id = session.get("user_id")
    role = session.get("role")
    if not user_id or role != "doctor":
        return jsonify({"error": "Unauthorized. Doctor access required."}), 403
    data = request.get_json(force=True, silent=True) or {}
    connection_id = data.get("connection_id")
    action = data.get("action")  # approve or reject
    if not connection_id or action not in ("approve", "reject"):
        return jsonify({"error": "Connection ID and valid action (approve/reject) are required."}), 400
    from backend.database.models import DoctorTechnicianConnection
    connection = DoctorTechnicianConnection.query.filter_by(id=connection_id, doctor_id=user_id).first()
    if not connection:
        return jsonify({"error": "Connection request not found."}), 404
    connection.status = "approved" if action == "approve" else "rejected"
    db.session.commit()
    return jsonify({
        "status": "success",
        "message": f"Connection successfully {connection.status}d.",
        "connection": {"id": connection.id, "status": connection.status}
    }), 200


# ── GET /api/doctor/<id>/patients ────────────────────────────
@api_bp.route("/doctor/<int:doctor_id>/patients", methods=["GET"])
def doctor_patients(doctor_id):
    user_id = session.get("user_id")
    role = session.get("role")
    if not user_id:
        return jsonify({"error": "Authentication required."}), 401
    
    if role == "technician":
        from backend.database.models import DoctorTechnicianConnection
        conn = DoctorTechnicianConnection.query.filter_by(doctor_id=doctor_id, technician_id=user_id, status="approved").first()
        if not conn:
            return jsonify({"error": "Access denied. You are not an approved technician for this doctor."}), 403
    elif role == "doctor" and int(user_id) == int(doctor_id):
        pass
    elif role == "admin":
        pass
    else:
        return jsonify({"error": "Access denied."}), 403
        
    from backend.database.models import DoctorPatientConnection
    connections = DoctorPatientConnection.query.filter_by(doctor_id=doctor_id, status="approved").all()
    patients_list = []
    for conn in connections:
        p = conn.patient
        patients_list.append({
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "email": p.user.email if p.user else "",
            "patient_uuid": p.patient_uuid
        })
    return jsonify({"status": "success", "patients": patients_list}), 200


# ── POST /api/technician/submit-biomarkers ───────────────────
@api_bp.route("/technician/submit-biomarkers", methods=["POST"])
def technician_submit_biomarkers():
    user_id = session.get("user_id")
    role = session.get("role")
    if not user_id or role != "technician":
        return jsonify({"error": "Unauthorized. Technician access required."}), 403
    data = request.get_json(force=True, silent=True) or {}
    doctor_id = data.get("doctor_id")
    patient_id = data.get("patient_id")
    features = data.get("features")
    patient_ref = data.get("patient_reference", "").strip() or None
    
    if not doctor_id or not patient_id or not features:
        return jsonify({"error": "Doctor ID, Patient ID, and Biomarkers features are required."}), 400

    if not isinstance(features, dict):
        return jsonify({"error": "Biomarkers features must be a JSON object (dict)."}), 400

    # Validate biomarker ranges:
    for f_name, f_val in features.items():
        try:
            val_f = float(f_val)
            if val_f < 0.0 or val_f > 1.0:
                return jsonify({
                    "error": f"Biomarker '{f_name}' value {f_val} is out of bounds (must be between 0.0 and 1.0)."
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                "error": f"Biomarker '{f_name}' must be a numeric value."
            }), 400
        
    from backend.database.models import DoctorTechnicianConnection, Patient
    conn = DoctorTechnicianConnection.query.filter_by(doctor_id=doctor_id, technician_id=user_id, status="approved").first()
    if not conn:
        return jsonify({"error": "Access denied. You are not approved by this doctor."}), 403
        
    patient = db.session.get(Patient, int(patient_id))
    if not patient:
        return jsonify({"error": "Patient not found."}), 404
        
    if not patient_ref:
        import random
        rand_suffix = "".join(random.choices("0123456789ABCDEF", k=6))
        patient_ref = f"SHS-{patient.first_name[0].upper()}{patient.last_name[0].upper()}-{rand_suffix}"
        
    try:
        result = model_manager.predict(features, "random_forest")
    except Exception as exc:
        return jsonify({"error": f"Model inference error: {str(exc)}"}), 500
        
    record = DiagnosticRecord(
        user_id=doctor_id,
        patient_id=patient.id,
        patient_reference=patient_ref,
        biomarkers_json=json.dumps(features),
        result_json=json.dumps(result),
        prediction_label=result["prediction"],
        confidence_score=result["confidence"],
        model_version=result.get("model_used"),
        status="draft",
    )
    db.session.add(record)
    db.session.commit()
    
    return jsonify({"status": "success", "message": "Biomarkers submitted as draft successfully.", "record_id": record.id}), 201


# ── GET /api/history/<id>/preview-models ──────────────────────
@api_bp.route("/history/<int:record_id>/preview-models", methods=["GET"])
def preview_models(record_id):
    user_id = session.get("user_id")
    role = session.get("role")
    if not user_id:
        return jsonify({"error": "Authentication required."}), 401
        
    record = db.session.get(DiagnosticRecord, record_id)
    if not record:
        return jsonify({"error": "Record not found."}), 404
        
    if role == "doctor" and int(record.user_id) != int(user_id):
        return jsonify({"error": "Access denied."}), 403
    elif role == "technician":
        from backend.database.models import DoctorTechnicianConnection
        conn = DoctorTechnicianConnection.query.filter_by(doctor_id=record.user_id, technician_id=user_id, status="approved").first()
        if not conn:
            return jsonify({"error": "Access denied."}), 403
    elif role != "admin":
        return jsonify({"error": "Access denied."}), 403
        
    biomarkers = json.loads(record.biomarkers_json) if record.biomarkers_json else {}
    predictions = {}
    for model_key in ["random_forest", "svm", "decision_tree", "logistic_regression"]:
        try:
            res = model_manager.predict(biomarkers, model_key)
            predictions[model_key] = {
                "prediction": res["prediction"],
                "confidence": res["confidence"],
                "probabilities": res.get("probabilities", {})
            }
        except Exception as exc:
            predictions[model_key] = {"error": str(exc)}
            
    return jsonify({"status": "success", "predictions": predictions}), 200


# ── GET /api/doctor/patient/<int:patient_id>/drafts ──────────
@api_bp.route("/doctor/patient/<int:patient_id>/drafts", methods=["GET"])
def get_patient_drafts(patient_id):
    user_id = session.get("user_id")
    role = session.get("role")
    if not user_id or role != "doctor":
        return jsonify({"error": "Unauthorized. Doctor access required."}), 403
        
    drafts = DiagnosticRecord.query.filter_by(
        user_id=user_id,
        patient_id=patient_id,
        status="draft"
    ).order_by(DiagnosticRecord.created_at.desc()).all()
    
    return jsonify({
        "status": "success",
        "drafts": [{
            "id": d.id,
            "patient_reference": d.patient_reference,
            "created_at": d.created_at.strftime('%d %b %Y, %H:%M') if d.created_at else '',
            "biomarkers": json.loads(d.biomarkers_json) if d.biomarkers_json else {}
        } for d in drafts]
    }), 200


# ── Patient CRUD Endpoints for Doctors ─────────────────────────

@api_bp.route("/patients", methods=["POST"])
def create_patient():
    user_id = session.get("user_id")
    role = session.get("role")
    if not user_id or role != "doctor":
        return jsonify({"error": "Unauthorized. Doctor access required."}), 403

    data = request.get_json(force=True, silent=True) or {}
    full_name = data.get("full_name", "").strip()
    date_of_birth_str = data.get("date_of_birth", "").strip()
    gender = data.get("gender", "").strip()
    clinical_notes = data.get("clinical_notes", "").strip() or None

    if not full_name or not date_of_birth_str or not gender:
        return jsonify({"error": "Full Name, Date of Birth, and Gender are required."}), 400

    try:
        import datetime
        date_of_birth = datetime.datetime.strptime(date_of_birth_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format for Date of Birth. Use YYYY-MM-DD."}), 400

    today = datetime.date.today()
    if date_of_birth > today:
        return jsonify({"error": "Date of Birth cannot be in the future."}), 400

    age_val = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))

    patient_uuid = data.get("patient_uuid", "").strip()
    if not patient_uuid:
        import random
        rand_suffix = "".join(random.choices("0123456789ABCDEF", k=6))
        patient_uuid = f"PAT-{rand_suffix}"

    names = full_name.split(None, 1)
    first_name = names[0] if names else "Unknown"
    last_name = names[1] if len(names) > 1 else ""

    patient = Patient(
        patient_uuid=patient_uuid,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        full_name=full_name,
        age=age_val,
        gender=gender,
        clinical_notes=clinical_notes,
        is_archived=False,
        doctor_id=user_id
    )

    db.session.add(patient)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Patient case created successfully.",
        "patient": {
            "id": patient.id,
            "patient_uuid": patient.patient_uuid,
            "full_name": patient.full_name,
            "date_of_birth": patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else None,
            "age": patient.age,
            "gender": patient.gender,
            "clinical_notes": patient.clinical_notes,
            "is_archived": patient.is_archived,
            "created_at": patient.created_at.strftime('%Y-%m-%d %H:%M:%S') if patient.created_at else None
        }
    }), 201


@api_bp.route("/patients", methods=["GET"])
def list_patients():
    user_id = session.get("user_id")
    role = session.get("role")
    if not user_id or role not in ("doctor", "admin"):
        return jsonify({"error": "Unauthorized."}), 403

    query = Patient.query
    if role == "doctor":
        query = query.filter_by(doctor_id=user_id)

    # Search query parameter
    search = request.args.get("search", "").strip()
    if search:
        query = query.filter(Patient.full_name.ilike(f"%{search}%") | Patient.patient_uuid.ilike(f"%{search}%"))

    # Include archived parameter
    include_archived = request.args.get("include_archived", "false").lower() == "true"
    if not include_archived:
        query = query.filter_by(is_archived=False)

    patients = query.order_by(Patient.created_at.desc()).all()

    return jsonify({
        "status": "success",
        "patients": [{
            "id": p.id,
            "patient_uuid": p.patient_uuid,
            "full_name": p.full_name,
            "age": p.age,
            "gender": p.gender,
            "clinical_notes": p.clinical_notes,
            "is_archived": p.is_archived,
            "created_at": p.created_at.strftime('%Y-%m-%d %H:%M:%S') if p.created_at else None
        } for p in patients]
    }), 200


@api_bp.route("/patients/<int:patient_id>", methods=["PUT"])
def edit_patient(patient_id):
    user_id = session.get("user_id")
    role = session.get("role")
    if not user_id or role != "doctor":
        return jsonify({"error": "Unauthorized."}), 403

    patient = Patient.query.filter_by(id=patient_id, doctor_id=user_id).first()
    if not patient:
        return jsonify({"error": "Patient case not found."}), 404

    data = request.get_json(force=True, silent=True) or {}
    full_name = data.get("full_name", "").strip()
    date_of_birth_str = data.get("date_of_birth", "").strip()
    gender = data.get("gender", "").strip()
    clinical_notes = data.get("clinical_notes", "").strip() or None

    if full_name:
        patient.full_name = full_name
        names = full_name.split(None, 1)
        patient.first_name = names[0] if names else "Unknown"
        patient.last_name = names[1] if len(names) > 1 else ""

    if date_of_birth_str:
        try:
            import datetime
            date_of_birth = datetime.datetime.strptime(date_of_birth_str, "%Y-%m-%d").date()
            
            today = datetime.date.today()
            if date_of_birth > today:
                return jsonify({"error": "Date of Birth cannot be in the future."}), 400
                
            patient.date_of_birth = date_of_birth
            patient.age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
        except ValueError:
            return jsonify({"error": "Invalid date format for Date of Birth. Use YYYY-MM-DD."}), 400

    if gender:
        patient.gender = gender
    patient.clinical_notes = clinical_notes

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Patient case updated successfully.",
        "patient": {
            "id": patient.id,
            "patient_uuid": patient.patient_uuid,
            "full_name": patient.full_name,
            "date_of_birth": patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else None,
            "age": patient.age,
            "gender": patient.gender,
            "clinical_notes": patient.clinical_notes,
            "is_archived": patient.is_archived
        }
    }), 200


@api_bp.route("/patients/<int:patient_id>/archive", methods=["POST"])
def archive_patient(patient_id):
    user_id = session.get("user_id")
    role = session.get("role")
    if not user_id or role != "doctor":
        return jsonify({"error": "Unauthorized."}), 403

    patient = Patient.query.filter_by(id=patient_id, doctor_id=user_id).first()
    if not patient:
        return jsonify({"error": "Patient case not found."}), 404

    data = request.get_json(force=True, silent=True) or {}
    archive_val = data.get("archive", True)

    patient.is_archived = bool(archive_val)
    db.session.commit()

    action_word = "archived" if patient.is_archived else "restored"
    return jsonify({
        "status": "success",
        "message": f"Patient case successfully {action_word}.",
        "patient": {
            "id": patient.id,
            "is_archived": patient.is_archived
        }
    }), 200


# ── AI Explanation Generation ─────────────────────────────────
@api_bp.route("/history/<int:record_id>/generate-explanation", methods=["POST"])
def generate_explanation(record_id):
    """Generate a patient-friendly simplified explanation of a diagnosis."""
    user_id = session.get("user_id")
    role = session.get("role")
    if not user_id or role not in ("doctor", "admin"):
        return jsonify({"error": "Unauthorized."}), 403

    record = db.session.get(DiagnosticRecord, record_id)
    if not record:
        return jsonify({"error": "Record not found."}), 404

    # Extract info
    import json
    biomarkers = json.loads(record.biomarkers_json) if record.biomarkers_json else {}
    diagnosis = record.prediction_label or "Healthy"
    
    # Check if Groq key exists, we can try to call it!
    groq_api_key = current_app.config.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
    if groq_api_key:
        try:
            biomarkers_list = []
            for k, v in biomarkers.items():
                biomarkers_list.append(f"- {k}: {v:.2f}")
            biomarkers_text = "\n".join(biomarkers_list)
            
            system_prompt = (
                "You are an empathetic, clear, and professional clinical assistant.\n"
                "Explain the patient's diagnosis context clearly and simply. Use clear language and bullet points.\n"
                "Explain what each biomarker indicates related to their condition.\n"
                "IMPORTANT: Always include a short disclaimer that you are an academic AI assistant prototype and they should verify details with their doctor."
            )
            user_prompt = (
                f"Predicted Condition: {diagnosis}\n"
                f"AI Confidence: {record.confidence_score:.1f}%\n\n"
                f"BIOMARKER LEVEL SCORES (normalised 0.0 to 1.0):\n"
                f"{biomarkers_text}"
            )
            
            # Try SDK first
            try:
                from groq import Groq
                client = Groq(api_key=groq_api_key)
                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.5,
                    max_tokens=800
                )
                explanation = completion.choices[0].message.content
                return jsonify({
                    "status": "success",
                    "explanation": explanation
                }), 200
            except ImportError:
                import requests
                headers = {
                    "Authorization": f"Bearer {groq_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 800
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=15)
                if res.status_code == 200:
                    res_data = res.json()
                    explanation = res_data["choices"][0]["message"]["content"]
                    return jsonify({
                        "status": "success",
                        "explanation": explanation
                    }), 200
                else:
                    logger.warning(f"Groq API returned status {res.status_code}: {res.text}")
        except Exception as e:
            logger.exception(f"Error calling Groq API for explanation: {e}")

    # High-quality rule-based fallback / primary generator
    diag_lower = diagnosis.lower()
    explanation = ""
    
    if "diabetes" in diag_lower:
        explanation = (
            "Your Fasting Glucose and HbA1c levels are higher than normal. "
            "This suggests Type 2 Diabetes Mellitus, a condition where the body does not process blood sugar properly. "
            "To manage this condition, we advise following your prescribed medication plan, maintaining a low-sugar diet, "
            "and incorporating regular physical activity (such as 30 minutes of walking daily)."
        )
    elif "anemia" in diag_lower or "thalasse" in diag_lower:
        explanation = (
            "Your red blood cell counts, haemoglobin, or haematocrit values are below the normal physiological ranges. "
            "This indicates Anemia, which reduces the blood's capacity to carry oxygen, causing feelings of tiredness or weakness. "
            "Increasing dietary iron intake, discussing iron supplements, and scheduling a follow-up blood count in 4 weeks is recommended."
        )
    elif "heart" in diag_lower or "cardio" in diag_lower:
        explanation = (
            "Your blood tests show elevated cardiovascular biomarkers (such as cholesterol, triglycerides, or troponin), "
            "suggesting cardiovascular stress or heart disease risk. "
            "We recommend immediate consultation with a cardiologist, limiting saturated fats and sodium in your meals, "
            "and regularly monitoring blood pressure levels."
        )
    elif "typhoid" in diag_lower:
        explanation = (
            "Your Widal O and H Titer results show a flagellar or somatic antibody reaction above safe baseline thresholds. "
            "This indicates a Typhoid Fever infection. "
            "It is highly important to take your complete course of prescribed antibiotics, drink clean/boiled water, "
            "maintain hand hygiene, and rest until you recover fully."
        )
    elif "thromboc" in diag_lower:
        explanation = (
            "Your platelet count is significantly lower than the normal baseline. "
            "This indicates Thrombocytopenia, which means your blood may have difficulty clotting. "
            "We advise avoiding medications like aspirin/ibuprofen (which thin the blood), monitoring for abnormal bruising or bleeding, "
            "and consulting a haematologist."
        )
    else:
        explanation = (
            f"Your biomarker results indicate a diagnosis of {diagnosis}. "
            "Please review this with your primary physician to understand your specific lab work details, "
            "adhere to the recommended treatment protocol, and lead a balanced, healthy lifestyle."
        )

    return jsonify({
        "status": "success",
        "explanation": explanation
    }), 200


# ── Notifications API ─────────────────────────────────────────
@api_bp.route("/notifications", methods=["GET"])
def get_notifications():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized."}), 401
    
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 5, type=int)
    
    from backend.database.models import Notification
    query = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    
    return jsonify({
        "status": "success",
        "notifications": [n.to_dict() for n in pagination.items],
        "unread_count": unread_count,
        "page": page,
        "per_page": per_page,
        "total_pages": pagination.pages,
        "total_count": pagination.total,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    }), 200


@api_bp.route("/notifications/read-all", methods=["POST"])
def read_all_notifications():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized."}), 401
    
    from backend.database.models import Notification
    unread = Notification.query.filter_by(user_id=user_id, is_read=False).all()
    for n in unread:
        n.is_read = True
    db.session.commit()
    return jsonify({"status": "success", "message": "All notifications marked as read."}), 200


@api_bp.route("/notifications/<int:notif_id>/read", methods=["POST"])
def read_notification(notif_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized."}), 401
    
    from backend.database.models import Notification
    n = Notification.query.filter_by(id=notif_id, user_id=user_id).first()
    if n:
        n.is_read = True
        db.session.commit()
    return jsonify({"status": "success"}), 200


# ── Super Admin Doctor Verification & Management ──────────────
@api_bp.route("/admin/doctors", methods=["GET"])
def admin_get_doctors():
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized."}), 403
    
    search_q = request.args.get("search", "").strip()
    from backend.database.models import User
    query = User.query.filter_by(role="doctor")
    
    if search_q:
        query = query.filter(User.full_name.ilike(f"%{search_q}%") | User.email.ilike(f"%{search_q}%") | User.license_number.ilike(f"%{search_q}%"))
        
    doctors = query.order_by(User.created_at.desc()).all()
    
    return jsonify({
        "status": "success",
        "doctors": [{
            "id": d.id,
            "full_name": d.full_name,
            "email": d.email,
            "license_number": d.license_number,
            "specialization": d.specialization,
            "hospital": d.hospital,
            "proof_filename": d.proof_filename,
            "status": d.status,
            "created_at": d.created_at.strftime('%Y-%m-%d %H:%M:%S') if d.created_at else None
        } for d in doctors]
    }), 200


@api_bp.route("/admin/doctors/<int:doctor_id>/verify", methods=["POST"])
def admin_verify_doctor(doctor_id):
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized."}), 403
        
    data = request.get_json(force=True, silent=True) or {}
    action = data.get("action", "").strip()  # approve, reject, reupload
    
    if action not in ("approve", "reject", "reupload"):
        return jsonify({"error": "Invalid action."}), 400
        
    from backend.database.models import User, Notification
    doctor = User.query.filter_by(id=doctor_id, role="doctor").first()
    if not doctor:
        return jsonify({"error": "Doctor account not found."}), 404
        
    if action == "approve":
        doctor.status = "approved"
        msg = "Your account has been approved. Full system access is granted."
    elif action == "reject":
        doctor.status = "rejected"
        msg = "Your uploaded document was rejected. Please upload a valid professional document."
    else:  # reupload request
        doctor.status = "rejected"
        msg = "Your document requires re-upload. Please submit a valid professional certificate."
        
    # Add persistent notification for doctor
    notif = Notification(
        user_id=doctor.id,
        message=msg
    )
    db.session.add(notif)
    db.session.commit()

    # Send email notification after commit (no-op if SMTP not configured)
    from backend.api.mail_utils import notify_doctor_status_change
    notify_doctor_status_change(doctor, action)
        
    return jsonify({
        "status": "success",
        "message": f"Doctor status updated to {doctor.status}.",
        "doctor_status": doctor.status
    }), 200


@api_bp.route("/admin/doctors/<int:doctor_id>/toggle-status", methods=["POST"])
def admin_toggle_doctor_status(doctor_id):
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized."}), 403
        
    from backend.database.models import User
    doctor = User.query.filter_by(id=doctor_id, role="doctor").first()
    if not doctor:
        return jsonify({"error": "Doctor not found."}), 404
        
    # Toggle active/deactive by changing status between approved and pending/rejected
    if doctor.status == "approved":
        doctor.status = "pending"  # deactivates
    else:
        doctor.status = "approved"  # activates
        
    db.session.commit()
    return jsonify({
        "status": "success",
        "message": f"Doctor status toggled to {doctor.status}.",
        "doctor_status": doctor.status
    }), 200


@api_bp.route("/admin/doctors/<int:doctor_id>", methods=["DELETE"])
def admin_delete_doctor(doctor_id):
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized."}), 403

    from backend.database.models import (
        User, DiagnosticRecord, Patient, Notification,
        DoctorPatientConnection, DoctorTechnicianConnection,
    )
    doctor = User.query.filter_by(id=doctor_id, role="doctor").first()
    if not doctor:
        return jsonify({"error": "Doctor not found."}), 404

    case_count = DiagnosticRecord.query.filter_by(user_id=doctor_id).count()
    if case_count > 0:
        return jsonify({
            "error": (
                f"This doctor has {case_count} clinical case(s) on record and cannot be "
                "permanently deleted, to preserve the patient record history. "
                "Use Deactivate instead to remove their system access."
            )
        }), 409

    # No case history — safe to remove. Clean up references that would
    # otherwise still violate foreign-key constraints.
    Patient.query.filter_by(doctor_id=doctor_id).update({"doctor_id": None})
    Notification.query.filter_by(user_id=doctor_id).delete()
    DoctorPatientConnection.query.filter_by(doctor_id=doctor_id).delete()
    DoctorTechnicianConnection.query.filter(
        (DoctorTechnicianConnection.doctor_id == doctor_id)
        | (DoctorTechnicianConnection.technician_id == doctor_id)
    ).delete(synchronize_session=False)

    db.session.delete(doctor)
    db.session.commit()
    return jsonify({"status": "success", "message": "Doctor account permanently deleted."}), 200


# ── Super Admin Dataset Management ────────────────────────────
@api_bp.route("/admin/datasets", methods=["GET"])
def admin_get_datasets():
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized."}), 403
        
    datasets_dir = os.path.abspath(current_app.root_path + "/../data")
    files = []
    if os.path.exists(datasets_dir):
        for f in os.listdir(datasets_dir):
            if f.endswith(".csv"):
                path = os.path.join(datasets_dir, f)
                stat = os.stat(path)
                # Count lines
                try:
                    with open(path, "r", encoding="utf-8") as f_obj:
                        lines = sum(1 for _ in f_obj)
                except Exception:
                    lines = "N/A"
                files.append({
                    "name": f,
                    "size": stat.st_size,
                    "lines": lines
                })
    return jsonify({"status": "success", "datasets": files}), 200


@api_bp.route("/admin/datasets/upload", methods=["POST"])
def admin_upload_dataset():
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized."}), 403
        
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400
        
    file = request.files["file"]
    filename = file.filename
    if not filename.endswith(".csv") or filename not in ("train_data.csv", "test_data.csv"):
        return jsonify({"error": "Only replacement of 'train_data.csv' or 'test_data.csv' is allowed."}), 400
        
    datasets_dir = os.path.abspath(current_app.root_path + "/../data")
    os.makedirs(datasets_dir, exist_ok=True)
    target_path = os.path.join(datasets_dir, filename)
    
    file.save(target_path)
    return jsonify({"status": "success", "message": f"Successfully replaced {filename} dataset."}), 200


@api_bp.route("/admin/datasets/<string:filename>", methods=["DELETE"])
def admin_delete_dataset(filename):
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized."}), 403
        
    if filename not in ("train_data.csv", "test_data.csv"):
        return jsonify({"error": "Invalid dataset filename."}), 400
        
    datasets_dir = os.path.abspath(current_app.root_path + "/../data")
    target_path = os.path.join(datasets_dir, filename)
    
    if os.path.exists(target_path):
        os.remove(target_path)
        return jsonify({"status": "success", "message": f"Deleted {filename} dataset."}), 200
    return jsonify({"error": "File not found."}), 404


# ── Super Admin Model Management & Retraining ─────────────────
@api_bp.route("/admin/model-metrics", methods=["GET"])
def admin_get_model_metrics():
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized."}), 403
        
    return jsonify({
        "status": "success",
        "models": _build_metadata(),
        "model_manager_status": model_manager.health_report()
    }), 200


@api_bp.route("/admin/model/retrain", methods=["POST"])
def admin_retrain_model():
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized."}), 403
        
    import threading
    
    def run_training_pipeline_bg():
        try:
            logger.info("[Retrain] Triggered background retraining pipeline.")
            from backend.ml.training.train import TrainingPipeline
            pipeline = TrainingPipeline()
            pipeline.train_and_evaluate()
            pipeline.save_summary()
            
            # Reload models in the singleton model manager
            model_manager._initialised = False
            model_manager.__init__()
            
            logger.info("[Retrain] Background retraining and reload completed successfully.")
        except Exception as e:
            logger.exception(f"[Retrain] Retraining failed: {e}")
            
    thread = threading.Thread(target=run_training_pipeline_bg)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "status": "success",
        "message": "Retraining pipeline launched successfully. Check system logs for progress."
    }), 200



# ── New Clinical Workflow Endpoints (v2.0 Spec) ──────────────────────────────

@api_bp.route("/symptoms", methods=["GET"])
def search_symptoms():
    query_str = request.args.get("query", "").strip().lower()
    from backend.database.models import SymptomCatalog
    
    if not query_str:
        symptoms = SymptomCatalog.query.limit(20).all()
    else:
        symptoms = SymptomCatalog.query.filter(
            SymptomCatalog.display_name.ilike(f"%{query_str}%") |
            SymptomCatalog.code.ilike(f"%{query_str}%") |
            SymptomCatalog.synonyms_json.ilike(f"%{query_str}%")
        ).limit(30).all()
        
    return jsonify({
        "status": "success",
        "symptoms": [s.to_dict() for s in symptoms]
    }), 200


def get_authorized_case(case_id, allow_admin=True):
    """
    Authorization helper to enforce patient/case security.
    Verifies authentication, role, approval status, case existence, and doctor ownership.
    """
    user_id = session.get("user_id")
    role = session.get("role")
    if not user_id:
        return None, (jsonify({"error": "Authentication required."}), 401)
    if role == "doctor":
        current_user = db.session.get(User, user_id)
        if not current_user or current_user.status != "approved":
            return None, (jsonify({"error": "Approved doctor account required. If you were recently approved, please log out and log back in."}), 403)
    elif role == "admin":
        if not allow_admin:
            return None, (jsonify({"error": "Admin access not permitted."}), 403)
    elif role != "technician":
        return None, (jsonify({"error": "Doctor or admin access required."}), 403)

    record = db.session.get(DiagnosticRecord, case_id)
    if not record:
        return None, (jsonify({"error": "Case not found."}), 404)

    if role == "doctor" and record.user_id != user_id:
        return None, (jsonify({"error": "Access denied to this case."}), 403)

    return record, None


@api_bp.route("/cases", methods=["POST"])
def create_case():
    """
    Dedicated endpoint to initialize a new clinical case record.
    Separates case creation from prediction inference per specification.
    """
    user_id = session.get("user_id")
    role = session.get("role")
    if not user_id:
        return jsonify({"error": "Authentication required."}), 401
    if role not in ("doctor", "admin"):
        return jsonify({"error": "Doctor or admin access required."}), 403
    if role == "doctor":
        current_user = db.session.get(User, user_id)
        if not current_user or current_user.status != "approved":
            return jsonify({"error": "Approved doctor account required."}), 403

    try:
        data = request.get_json(force=True, silent=True) or {}
        patient_id = data.get("patient_id")
        patient_reference = str(data.get("patient_reference", "")).strip() or None

        patient = None
        if patient_id is not None:
            try:
                p_id = int(patient_id)
                patient = db.session.get(Patient, p_id)
            except (TypeError, ValueError):
                patient = None

        if patient:
            patient_reference = patient.patient_uuid
        elif not patient_reference:
            import uuid
            from datetime import datetime, timezone
            date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
            patient_reference = f"SHS-GEN-{date_str}-{uuid.uuid4().hex[:6].upper()}"

        record = DiagnosticRecord(
            user_id=user_id,
            patient_id=patient.id if patient else None,
            patient_reference=patient_reference,
            biomarkers_json=json.dumps({}),
            result_json=json.dumps({}),
            prediction_label="Pending Assessment",
            confidence_score=0.0,
            status="draft",
            case_status="Draft Case",
        )
        db.session.add(record)
        db.session.commit()

        return jsonify({
            "status": "success",
            "case": record.to_dict()
        }), 201
    except Exception as exc:
        db.session.rollback()
        logger.exception(f"[API] Error in create_case: {exc}")
        return jsonify({
            "error": "Internal server error.",
            "status": "failed",
            "details": str(exc) if current_app.debug else None,
        }), 500


@api_bp.route("/cases/<int:case_id>", methods=["GET"])
def get_case(case_id):
    """Fetch case details by ID for workflow resumption."""
    record, err_resp = get_authorized_case(case_id)
    if err_resp:
        return err_resp
    return jsonify({"status": "success", "case": record.to_dict()}), 200


@api_bp.route("/cases/<int:case_id>/symptoms", methods=["POST"])
def capture_case_symptoms(case_id):
    record, err_resp = get_authorized_case(case_id)
    if err_resp:
        return err_resp

    try:
        data = request.get_json(force=True, silent=True) or {}
        symptoms_list = data.get("symptoms", [])
        if not isinstance(symptoms_list, list):
            return jsonify({"error": "'symptoms' must be a list."}), 400
            
        from backend.database.models import PatientCaseSymptom, SymptomCatalog
        
        if data.get("replace", False):
            if symptoms_list or data.get("allow_empty", False):
                PatientCaseSymptom.query.filter_by(case_id=case_id).delete()
            
        added_symptoms = []
        catalog_items = SymptomCatalog.query.all()
        
        for item in symptoms_list:
            if not isinstance(item, dict):
                continue
            raw_text = str(item.get("raw_text", "")).strip() or str(item.get("display_name", "")).strip()
            if not raw_text:
                continue
                
            display_name = item.get("display_name", raw_text).strip()
            source = item.get("source", "selected") # selected | typed | other
            duration_val = item.get("duration_value")
            duration_unit = item.get("duration_unit", "days")
            severity = item.get("severity", "Moderate")
            notes = item.get("notes", "")
            
            matched_catalog = None
            standard_symptom_id = item.get("standard_symptom_id")
            
            if standard_symptom_id:
                matched_catalog = db.session.get(SymptomCatalog, standard_symptom_id)
            else:
                raw_lower = raw_text.lower()
                for cat in catalog_items:
                    if cat.display_name.lower() == raw_lower or cat.code.lower() == raw_lower:
                        matched_catalog = cat
                        break
                    syns = cat.to_dict().get("synonyms", [])
                    if any(syn.lower() == raw_lower for syn in syns):
                        matched_catalog = cat
                        break
                        
            pcs = PatientCaseSymptom(
                case_id=case_id,
                standard_symptom_id=matched_catalog.id if matched_catalog else None,
                display_name=matched_catalog.display_name if matched_catalog else display_name,
                raw_text=raw_text,
                source=source,
                duration_value=int(duration_val) if duration_val is not None else None,
                duration_unit=duration_unit,
                severity=severity,
                notes=notes,
                mapping_confidence=1.0 if matched_catalog else 0.5,
                created_by=session.get("user_id")
            )
            db.session.add(pcs)
            added_symptoms.append(pcs)
            
        record.case_status = "Symptoms Captured"
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"Successfully captured {len(added_symptoms)} symptoms for case.",
            "case_status": record.case_status,
            "symptoms": [s.to_dict() for s in PatientCaseSymptom.query.filter_by(case_id=case_id).all()]
        }), 201
    except Exception as exc:
        db.session.rollback()
        logger.exception(f"[API] Error in capture_case_symptoms: {exc}")
        return jsonify({
            "error": "Internal server error.",
            "status": "failed",
            "details": str(exc) if current_app.debug else None,
        }), 500


@api_bp.route("/cases/<int:case_id>/symptoms/<int:symptom_id>", methods=["PATCH"])
def update_case_symptom(case_id, symptom_id):
    record, err_resp = get_authorized_case(case_id)
    if err_resp:
        return err_resp

    try:
        from backend.database.models import PatientCaseSymptom
        pcs = PatientCaseSymptom.query.filter_by(id=symptom_id, case_id=case_id).first()
        if not pcs:
            return jsonify({"error": "Symptom entry not found."}), 404
            
        data = request.get_json(force=True, silent=True) or {}
        if "duration_value" in data: pcs.duration_value = data["duration_value"]
        if "duration_unit" in data: pcs.duration_unit = data["duration_unit"]
        if "severity" in data: pcs.severity = data["severity"]
        if "notes" in data: pcs.notes = data["notes"]
        
        db.session.commit()
        return jsonify({"status": "success", "symptom": pcs.to_dict()}), 200
    except Exception as exc:
        db.session.rollback()
        logger.exception(f"[API] Error in update_case_symptom: {exc}")
        return jsonify({
            "error": "Internal server error.",
            "status": "failed",
            "details": str(exc) if current_app.debug else None,
        }), 500


def _generate_ai_rationales(candidates, symptom_names):
    """Generate a clinically-grounded, symptom-specific explanation for each
    preliminary candidate using Groq, if configured. Falls back silently to
    each candidate's existing rule-based rationale on any failure — this
    never blocks the assessment from completing."""
    groq_api_key = current_app.config.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
    if not groq_api_key or not candidates:
        return candidates
    try:
        candidate_lines = "\n".join(
            f"- {c['condition_name']} (score: {c['score']}%): currently explained as \"{c['rationale']}\""
            for c in candidates
        )
        system_prompt = (
            "You are a clinical reasoning assistant for a diagnostic support tool. "
            "For each candidate condition below, write ONE concise sentence (max 30 words) explaining "
            "why the patient's specific reported symptoms support that condition at that score, "
            "using real clinical reasoning. Do not invent symptoms not listed. "
            "Return ONLY a JSON array of strings, one per candidate, in the same order given. No other text."
        )
        user_prompt = (
            f"Reported symptoms: {', '.join(symptom_names) if symptom_names else 'none specified'}\n\n"
            f"Candidates:\n{candidate_lines}"
        )
        reply_text = None
        try:
            from groq import Groq
            client = Groq(api_key=groq_api_key)
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            reply_text = completion.choices[0].message.content
        except ImportError:
            import requests
            headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 500,
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=12)
            if res.status_code == 200:
                reply_text = res.json()["choices"][0]["message"]["content"]
        if reply_text:
            cleaned = reply_text.strip().strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
            explanations = json.loads(cleaned)
            if isinstance(explanations, list) and len(explanations) == len(candidates):
                for c, explanation in zip(candidates, explanations):
                    c["rationale"] = explanation
                    c["ai_generated"] = True
    except Exception as exc:
        logger.warning(f"[AI Rationale] Falling back to rule-based explanations: {exc}")
    return candidates


@api_bp.route("/cases/<int:case_id>/pre-assessment", methods=["POST"])
def run_pre_assessment(case_id):
    record, err_resp = get_authorized_case(case_id)
    if err_resp:
        return err_resp

    try:
        from backend.database.models import PatientCaseSymptom, PreliminaryAssessment, AssessmentCandidate
        
        symptoms = PatientCaseSymptom.query.filter_by(case_id=case_id).all()
        symptom_names = [s.display_name.lower() for s in symptoms]
        symptom_texts = [s.raw_text.lower() for s in symptoms]
        all_sym_strings = set(symptom_names + symptom_texts)
        
        candidates_scores = []
        
        # 1. Anemia
        anemia_matches = [s for s in all_sym_strings if any(t in s for t in ["fatigue", "pallor", "dizziness", "breath", "pale"])]
        if anemia_matches:
            score = round(40.0 + len(anemia_matches) * 20.0, 1)
            score = min(92.0, score)
            candidates_scores.append({
                "condition_name": "Anemia",
                "score": score,
                "rationale": f"Reported symptoms ({', '.join(set(anemia_matches))}) suggest reduced oxygen-carrying capacity or microcytic/macrocytic anemia.",
                "supported_by_biomarker_model": True
            })

        # 2. Diabetes
        diabetes_matches = [s for s in all_sym_strings if any(t in s for t in ["thirst", "urination", "weight loss", "polyuria", "polydipsia"])]
        if diabetes_matches:
            score = round(50.0 + len(diabetes_matches) * 20.0, 1)
            score = min(94.0, score)
            candidates_scores.append({
                "condition_name": "Diabetes",
                "score": score,
                "rationale": f"Presentation of osmotic symptoms ({', '.join(set(diabetes_matches))}) indicates potential chronic metabolic glycemic dysregulation.",
                "supported_by_biomarker_model": True
            })

        # 3. Heart Disease
        heart_matches = [s for s in all_sym_strings if any(t in s for t in ["chest", "pain", "palpitations", "pulse", "breath", "angina"])]
        if heart_matches:
            score = round(45.0 + len(heart_matches) * 22.0, 1)
            score = min(90.0, score)
            candidates_scores.append({
                "condition_name": "Heart Disease",
                "score": score,
                "rationale": f"Thoracic and cardiac indicators ({', '.join(set(heart_matches))}) warrant immediate cardiovascular risk evaluation.",
                "supported_by_biomarker_model": True
            })

        # 4. Thrombocytopenia
        thromb_matches = [s for s in all_sym_strings if any(t in s for t in ["bruising", "bleeding", "petechiae", "purpura", "gums", "nosebleed"])]
        if thromb_matches:
            score = round(55.0 + len(thromb_matches) * 20.0, 1)
            score = min(92.0, score)
            candidates_scores.append({
                "condition_name": "Thrombocytopenia",
                "score": score,
                "rationale": f"Hemorrhagic and mucosal bleeding signs ({', '.join(set(thromb_matches))}) suggest platelet depletion or clotting dysfunction.",
                "supported_by_biomarker_model": True
            })

        # 5. Thalassemia
        thal_matches = [s for s in all_sym_strings if any(t in s for t in ["fatigue", "pallor", "jaundice", "yellow"])]
        if len(thal_matches) >= 2:
            score = round(35.0 + len(thal_matches) * 15.0, 1)
            candidates_scores.append({
                "condition_name": "Thalassemia",
                "score": score,
                "rationale": f"Chronic anemia signs with possible hemolytic presentation suggest hereditary hemoglobinopathy.",
                "supported_by_biomarker_model": True
            })

        # 6. Typhoid Fever (Not supported by biomarker classifier model)
        typhoid_matches = [s for s in all_sym_strings if any(t in s for t in ["fever", "abdominal", "headache", "diarrhea", "cramps"])]
        if any("fever" in m for m in typhoid_matches) and len(typhoid_matches) >= 2:
            score = round(50.0 + len(typhoid_matches) * 15.0, 1)
            score = min(93.0, score)
            candidates_scores.append({
                "condition_name": "Typhoid Fever",
                "score": score,
                "rationale": f"Febrile gastroenteritis cluster ({', '.join(set(typhoid_matches))}) indicates possible systemic Salmonella enterica infection.",
                "supported_by_biomarker_model": False
            })

        if not candidates_scores and symptoms:
            candidates_scores.append({
                "condition_name": "Anemia",
                "score": 40.0,
                "rationale": "General constitutional symptoms reported; baseline hematological screening recommended.",
                "supported_by_biomarker_model": True
            })

        candidates_scores.sort(key=lambda x: x["score"], reverse=True)
        candidates_scores = _generate_ai_rationales(candidates_scores, list(set(symptom_names)))

        pa = PreliminaryAssessment(
            case_id=case_id,
            status="completed",
            summary_text=f"Preliminary consideration identified {len(candidates_scores)} possible condition(s) for investigation based on {len(symptoms)} reported symptoms."
        )
        db.session.add(pa)
        db.session.flush()

        for idx, c in enumerate(candidates_scores, 1):
            ac = AssessmentCandidate(
                assessment_id=pa.id,
                condition_name=c["condition_name"],
                rank=idx,
                score=c["score"],
                rationale=c["rationale"],
                supported_by_biomarker_model=c["supported_by_biomarker_model"],
                unsupported_note=None if c["supported_by_biomarker_model"] else "No biomarker prediction model available in current system"
            )
            db.session.add(ac)

        record.case_status = "Pre-Assessment Ready"
        db.session.commit()

        return jsonify({
            "status": "success",
            "case_status": record.case_status,
            "preliminary_assessment": pa.to_dict()
        }), 200
    except Exception as exc:
        db.session.rollback()
        logger.exception(f"[API] Error in run_pre_assessment: {exc}")
        return jsonify({
            "error": "Internal server error.",
            "status": "failed",
            "details": str(exc) if current_app.debug else None,
        }), 500


@api_bp.route("/cases/<int:case_id>/investigation-recommendations", methods=["GET"])
def get_investigation_recommendations(case_id):
    record, err_resp = get_authorized_case(case_id)
    if err_resp:
        return err_resp

    try:
        from backend.database.models import PreliminaryAssessment, InvestigationRule, InvestigationCatalog
        
        pa = PreliminaryAssessment.query.filter_by(case_id=case_id).order_by(PreliminaryAssessment.created_at.desc()).first()
        if not pa:
            return jsonify({
                "status": "success",
                "recommendations": []
            }), 200

        candidates = pa.candidates.all()
        cond_names = [c.condition_name for c in candidates]

        rules = InvestigationRule.query.filter(InvestigationRule.condition_name.in_(cond_names)).all()
        
        recs = []
        seen_inv_ids = set()
        for r in rules:
            if r.recommended_investigation_id not in seen_inv_ids:
                seen_inv_ids.add(r.recommended_investigation_id)
                recs.append({
                    "investigation_id": r.recommended_investigation_id,
                    "investigation": r.recommended_investigation.to_dict(),
                    "priority": r.priority,
                    "reason": r.reason,
                    "source_rule_id": r.id,
                    "doctor_selected": True,
                    "required_for_model": True
                })

        return jsonify({
            "status": "success",
            "recommendations": recs
        }), 200
    except Exception as exc:
        db.session.rollback()
        logger.exception(f"[API] Error in get_investigation_recommendations: {exc}")
        return jsonify({
            "error": "Internal server error.",
            "status": "failed",
            "details": str(exc) if current_app.debug else None,
        }), 500


@api_bp.route("/cases/<int:case_id>/investigations", methods=["POST"])
def select_case_investigations(case_id):
    record, err_resp = get_authorized_case(case_id)
    if err_resp:
        return err_resp

    try:
        data = request.get_json(force=True, silent=True) or {}
        selections = data.get("investigations", [])
        if not isinstance(selections, list):
            return jsonify({"error": "'investigations' must be a list."}), 400
            
        from backend.database.models import CaseInvestigation, InvestigationCatalog
        
        CaseInvestigation.query.filter_by(case_id=case_id).delete()
        
        created = []
        for item in selections:
            if not isinstance(item, dict):
                continue
            inv_id = item.get("investigation_id")
            if not inv_id: continue
            
            ci = CaseInvestigation(
                case_id=case_id,
                investigation_id=inv_id,
                priority=item.get("priority", "High"),
                reason=item.get("reason", "Doctor selected investigation"),
                source_rule_id=item.get("source_rule_id"),
                doctor_selected=item.get("doctor_selected", True),
                status="selected",
                result_type=item.get("result_type", "numeric"),
                required_for_model=item.get("required_for_model", True)
            )
            db.session.add(ci)
            created.append(ci)
            
        record.case_status = "Investigations Selected"
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"Successfully selected {len(created)} investigation(s).",
            "case_status": record.case_status,
            "investigations": [c.to_dict() for c in CaseInvestigation.query.filter_by(case_id=case_id).all()]
        }), 201
    except Exception as exc:
        db.session.rollback()
        logger.exception(f"[API] Error in select_case_investigations: {exc}")
        return jsonify({
            "error": "Internal server error.",
            "status": "failed",
            "details": str(exc) if current_app.debug else None,
        }), 500


@api_bp.route("/cases/<int:case_id>/investigations/<int:inv_id>/status", methods=["PATCH"])
def update_investigation_status(case_id, inv_id):
    record, err_resp = get_authorized_case(case_id)
    if err_resp:
        return err_resp

    try:
        from backend.database.models import CaseInvestigation
        ci = CaseInvestigation.query.filter_by(id=inv_id, case_id=case_id).first()
        if not ci:
            return jsonify({"error": "Case investigation not found."}), 404
            
        data = request.get_json(force=True, silent=True) or {}
        if "status" in data: ci.status = data["status"]
        if "doctor_selected" in data: ci.doctor_selected = bool(data["doctor_selected"])
        
        db.session.commit()
        return jsonify({"status": "success", "investigation": ci.to_dict()}), 200
    except Exception as exc:
        db.session.rollback()
        logger.exception(f"[API] Error in update_investigation_status: {exc}")
        return jsonify({
            "error": "Internal server error.",
            "status": "failed",
            "details": str(exc) if current_app.debug else None,
        }), 500


@api_bp.route("/cases/<int:case_id>/investigations/<int:inv_id>/results", methods=["POST"])
def enter_investigation_results(case_id, inv_id):
    record, err_resp = get_authorized_case(case_id)
    if err_resp:
        return err_resp

    try:
        from backend.database.models import CaseInvestigation, InvestigationResult
        ci = CaseInvestigation.query.filter_by(id=inv_id, case_id=case_id).first()
        if not ci:
            return jsonify({"error": "Case investigation not found."}), 404
            
        data = request.get_json(force=True, silent=True) or {}
        results_dict = data.get("results", {})
        if not isinstance(results_dict, dict):
            return jsonify({"error": "'results' must be a JSON dictionary of biomarker key-values."}), 400
            
        InvestigationResult.query.filter_by(case_investigation_id=ci.id).delete()
        
        added_results = []
        current_biomarkers = json.loads(record.biomarkers_json) if record.biomarkers_json else {}
        
        for key, val in results_dict.items():
            try:
                val_f = float(val)
            except (ValueError, TypeError):
                continue
                
            ir = InvestigationResult(
                case_investigation_id=ci.id,
                biomarker_key=key,
                raw_value=val_f,
                normalized_value=None,
                unit=data.get("units", {}).get(key, "")
            )
            db.session.add(ir)
            added_results.append(ir)
            current_biomarkers[key] = val_f

        ci.status = "completed"
        record.biomarkers_json = json.dumps(current_biomarkers)
        record.case_status = "Results Available"
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"Successfully recorded {len(added_results)} result(s).",
            "case_status": record.case_status,
            "investigation": ci.to_dict(),
            "biomarkers": current_biomarkers
        }), 201
    except Exception as exc:
        db.session.rollback()
        logger.exception(f"[API] Error in enter_investigation_results: {exc}")
        return jsonify({
            "error": "Internal server error.",
            "status": "failed",
            "details": str(exc) if current_app.debug else None,
        }), 500


@api_bp.route("/cases/<int:case_id>/predictions", methods=["POST"])
def run_case_prediction(case_id):
    record, err_resp = get_authorized_case(case_id)
    if err_resp:
        return err_resp

    try:
        data = request.get_json(force=True, silent=True) or {}
        model_key = data.get("model", "random_forest")

        biomarkers = data.get("features")
        if not biomarkers:
            biomarkers = json.loads(record.biomarkers_json) if record.biomarkers_json else {}
        if not biomarkers:
            return jsonify({"error": "No biomarker investigation results available to run prediction."}), 400

        HEALTHY_BASELINE = {
            "Glucose": 85.0, "Cholesterol": 180.0, "Hemoglobin": 15.0,
            "Platelets": 250.0, "White Blood Cells": 7.0, "Red Blood Cells": 4.8,
            "Hematocrit": 42.0, "Mean Corpuscular Volume": 88.0,
            "Mean Corpuscular Hemoglobin": 30.0, "Mean Corpuscular Hemoglobin Concentration": 33.5,
            "Insulin": 10.0, "BMI": 22.0, "Systolic Blood Pressure": 120.0,
            "Diastolic Blood Pressure": 80.0, "Triglycerides": 110.0,
            "HbA1c": 5.2, "LDL Cholesterol": 90.0, "HDL Cholesterol": 55.0,
            "ALT": 24.0, "AST": 22.0, "Heart Rate": 72.0, "Creatinine": 0.9,
            "Troponin": 0.01, "C-reactive Protein": 2.0,
        }

        full_features = HEALTHY_BASELINE.copy()
        entered_keys = []
        for k, v in biomarkers.items():
            try:
                full_features[k] = float(v)
                if k in HEALTHY_BASELINE:
                    entered_keys.append(k)
            except (ValueError, TypeError):
                pass

        # ── CRITICAL PATH: the actual prediction. If this fails, we genuinely
        # have nothing to return, so this part alone stays inside the outer
        # try/except. Everything below this point is a side-effect. ──
        res = model_manager.predict(full_features, model_key)

        features_actually_entered = sorted(entered_keys)
        features_defaulted = sorted(set(HEALTHY_BASELINE.keys()) - set(entered_keys))
        coverage_pct = round(len(features_actually_entered) / len(HEALTHY_BASELINE) * 100, 1)

        record.prediction_label = res["prediction"]
        record.confidence_score = res["confidence"]
        record.model_version = res.get("model_used")
        record.result_json = json.dumps(res)
        record.case_status = "Prediction Available"
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception(f"[API] Error in run_case_prediction (critical path): {exc}")
        return jsonify({
            "error": "Internal server error.",
            "status": "failed",
            "details": str(exc) if current_app.debug else None,
        }), 500

    # ── EVERYTHING BELOW IS A SIDE-EFFECT. The prediction already succeeded
    # and is already saved. Nothing past this point is allowed to turn a
    # successful prediction into an error response. ──
    try:
        from backend.database.models import ModelPrediction
        mp = ModelPrediction(
            case_id=case_id,
            model_name=res.get("model_used", model_key),
            model_version="v2.0.0-clean",
            predicted_diagnosis=res["prediction"],
            probability=res["confidence"],
            probability_scores_json=json.dumps(res.get("probabilities", {})),
            feature_importance_json=json.dumps(res.get("feature_importance", {})),
            data_coverage_json=json.dumps({
                "entered": features_actually_entered,
                "defaulted": features_defaulted,
                "coverage_pct": coverage_pct,
            })
        )
        db.session.add(mp)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.warning(f"[API] Prediction succeeded but history logging failed (non-fatal): {exc}")

    try:
        from backend.database.models import Notification, User
        notif_message = f"Prediction ready for case {record.patient_reference or ('#' + str(record.id))}"
        recipients = set()
        if record.user_id:
            recipients.add(record.user_id)
        for admin_user in User.query.filter_by(role="admin").all():
            recipients.add(admin_user.id)
        for uid in recipients:
            db.session.add(Notification(user_id=uid, message=notif_message))
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.warning(f"[API] Prediction succeeded but notification creation failed (non-fatal): {exc}")

    try:
        from backend.api.mail_utils import notify_prediction_ready
        from backend.database.models import User
        author = db.session.get(User, record.user_id) if record.user_id else None
        if author and author.email:
            notify_prediction_ready(author, record, res)
    except Exception as exc:
        logger.warning(f"[API] Prediction succeeded but email notification failed (non-fatal): {exc}")

    return jsonify({
        "status": "success",
        "predicted_diagnosis": res["prediction"],
        "confidence": res["confidence"],
        "case_status": record.case_status,
        "prediction_details": res,
        "data_coverage": {
            "entered_count": len(features_actually_entered),
            "total_count": len(HEALTHY_BASELINE),
            "coverage_pct": coverage_pct,
            "defaulted_features": features_defaulted,
        },
    }), 200


@api_bp.route("/cases/<int:case_id>/ai-summary", methods=["POST"])
def generate_case_ai_summary(case_id):
    record, err_resp = get_authorized_case(case_id)
    if err_resp:
        return err_resp

    try:
        from backend.database.models import PatientCaseSymptom, PreliminaryAssessment, CaseInvestigation, AISummary
        
        symptoms = PatientCaseSymptom.query.filter_by(case_id=case_id).all()
        sym_str = ", ".join([f"{s.display_name} ({s.severity})" for s in symptoms]) if symptoms else "None reported"
        
        pa = PreliminaryAssessment.query.filter_by(case_id=case_id).order_by(PreliminaryAssessment.created_at.desc()).first()
        cand_str = ", ".join([f"{c.condition_name} ({c.score}%)" for c in pa.candidates.all()]) if pa else "None"
        
        invs = CaseInvestigation.query.filter_by(case_id=case_id).all()
        inv_str = ", ".join([ci.investigation.name for ci in invs if ci.investigation]) if invs else "None selected"
        
        pred_label = record.prediction_label or "Pending"
        confidence = record.confidence_score or 0.0
        
        data = request.get_json(force=True, silent=True) or {}
        doc_notes = data.get("doctor_notes", record.doctor_remarks or "")
        
        symptoms_narrative = f"Patient presented with key symptoms: {sym_str}."
        assessment_narrative = f"Preliminary clinical considerations identified potential differential conditions: {cand_str}."
        results_narrative = f"Targeted investigations ordered/completed: {inv_str}."
        prediction_narrative = f"Algorithmic ML prediction yields a Predicted Diagnosis of {pred_label} with {confidence:.1f}% confidence."
        
        summary_text = (
            "CLINICAL WORKFLOW SUMMARY:\n"
            f"1. Presentation: {symptoms_narrative}\n"
            f"2. Pre-Assessment: {assessment_narrative}\n"
            f"3. Investigations: {results_narrative}\n"
            f"4. ML Inference: {prediction_narrative}\n"
            f"5. Doctor Remarks: {doc_notes if doc_notes else 'No additional clinical remarks.'}\n\n"
            "Disclaimer: Smart Health Sync provides decision support tools; diagnosis remains the responsibility of the attending physician."
        )

        ais = AISummary(
            case_id=case_id,
            summary_text=summary_text,
            symptoms_narrative=symptoms_narrative,
            assessment_narrative=assessment_narrative,
            results_narrative=results_narrative,
            prediction_narrative=prediction_narrative,
            doctor_notes=doc_notes
        )
        db.session.add(ais)
        record.ai_explanation = summary_text
        record.case_status = "Case Reviewed"
        db.session.commit()

        return jsonify({
            "status": "success",
            "case_status": record.case_status,
            "ai_summary": ais.to_dict(),
            "ai_explanation": summary_text
        }), 200
    except Exception as exc:
        db.session.rollback()
        logger.exception(f"[API] Error in generate_case_ai_summary: {exc}")
        return jsonify({
            "error": "Internal server error.",
            "status": "failed",
            "details": str(exc) if current_app.debug else None,
        }), 500


@api_bp.route("/ai/chat", methods=["POST"])
def ai_chat_global():
    data = request.get_json(force=True, silent=True) or {}
    case_id = data.get("case_id")
    if case_id:
        try:
            case_id = int(case_id)
            return ask_ai_case(case_id)
        except ValueError:
            pass
    
    user_message = str(data.get("message") or data.get("question") or "").strip()
    if not user_message:
        return jsonify({"error": "Message is required."}), 400

    conversation_history = data.get("conversation", [])
    if not isinstance(conversation_history, list):
        conversation_history = []

    system_prompt = (
        "You are SmartHealth AI, a conversational health education and clinical decision-support assistant. "
        "Answer the user's exact question accurately, directly, and concisely. "
        "Answer general health, wellness, nutrition, exercise, sleep, stress management, and medical terminology questions naturally. "
        "If potentially life-threatening symptoms (e.g., severe chest pain, sudden paralysis, loss of consciousness) are mentioned, recommend immediate emergency medical care."
    )

    groq_api_key = current_app.config.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
    answer = None

    if groq_api_key:
        import urllib.request
        import json as py_json
        
        messages = [{"role": "system", "content": system_prompt}]
        for item in conversation_history[-6:]:
            if isinstance(item, dict) and item.get("role") in ("user", "assistant") and item.get("content"):
                messages.append({"role": item["role"], "content": str(item["content"])})
        messages.append({"role": "user", "content": user_message})

        groq_models = ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.6-27b", "llama-3.3-70b-versatile", "llama3-8b-8192"]
        
        for groq_model in groq_models:
            try:
                req_payload = py_json.dumps({
                    "model": groq_model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 800
                }).encode("utf-8")

                req = urllib.request.Request(
                    "https://api.groq.com/openai/v1/chat/completions",
                    data=req_payload,
                    headers={
                        "Authorization": f"Bearer {groq_api_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "SmartHealth-ClinicalAI/2026"
                    },
                    method="POST"
                )

                with urllib.request.urlopen(req, timeout=15) as response:
                    res_body = py_json.loads(response.read().decode("utf-8"))
                    if res_body.get("choices") and len(res_body["choices"]) > 0:
                        answer = res_body["choices"][0]["message"]["content"].strip()
                        break
            except Exception as groq_err:
                logger.warning(f"[AI Chat] Groq model '{groq_model}' attempt failed: {groq_err}.")

    if not answer:
        if groq_api_key:
            logger.error("[AI Chat] All Groq models failed — falling back to templated reasoning engine.")
        else:
            logger.warning("[AI Chat] GROQ_API_KEY not configured — using templated fallback engine.")

        q_lower = user_message.lower()
        if "food" in q_lower or "eat" in q_lower or "diet" in q_lower or "breakfast" in q_lower:
            answer = "A balanced daily diet emphasizes whole foods: fruits, vegetables, whole grains, lean proteins, healthy fats, and adequate hydration."
        elif "exercise" in q_lower or "workout" in q_lower or "walking" in q_lower:
            answer = "Aim for at least 150 minutes of moderate-intensity exercise per week, such as brisk walking, cycling, or swimming."
        elif "sleep" in q_lower or "rest" in q_lower:
            answer = "Healthy sleep habits involve maintaining a consistent sleep schedule and targeting 7 to 9 hours of restorative sleep per night."
        else:
            answer = f"Regarding your health inquiry ('{user_message}'): Maintaining regular physical activity, balanced nutrition, adequate sleep, and routine medical checkups supports overall wellness."

    disclaimer = "Clinical Decision-Support Notice: AI answers provide general health education and decision support only. Always consult a healthcare professional for clinical advice."

    return jsonify({
        "status": "success",
        "message": user_message,
        "question": user_message,
        "answer": answer,
        "disclaimer": disclaimer
    }), 200


@api_bp.route("/cases/<int:case_id>/ask-ai", methods=["POST"])
@api_bp.route("/cases/<int:case_id>/ai-assistant", methods=["POST"])
def ask_ai_case(case_id):
    record, err_resp = get_authorized_case(case_id)
    if err_resp:
        return err_resp

    try:
        data = request.get_json(force=True, silent=True) or {}
        user_question = str(data.get("message") or data.get("question") or "").strip()
        if not user_question:
            return jsonify({"error": "Question is required."}), 400

        conversation_history = data.get("conversation", [])
        if not isinstance(conversation_history, list):
            conversation_history = []

        from backend.database.models import PatientCaseSymptom, PreliminaryAssessment, CaseInvestigation
        
        symptoms = PatientCaseSymptom.query.filter_by(case_id=case_id).all()
        sym_list = [f"{s.display_name} (Severity: {s.severity or 'unspecified'}, Duration: {s.duration_value or ''} {s.duration_unit or ''})".strip() for s in symptoms]
        sym_str = ", ".join(sym_list) if sym_list else "None reported"

        pa = PreliminaryAssessment.query.filter_by(case_id=case_id).order_by(PreliminaryAssessment.created_at.desc()).first()
        cand_list = [f"{c.condition_name} ({c.score:.1f}% probability) - {c.rationale or ''}".strip() for c in pa.candidates.all()] if pa else []
        cand_str = "; ".join(cand_list) if cand_list else "None"

        invs = CaseInvestigation.query.filter_by(case_id=case_id).all()
        inv_list = [ci.investigation.name for ci in invs if ci.investigation]
        inv_str = ", ".join(inv_list) if inv_list else "None selected"

        biomarkers = json.loads(record.biomarkers_json) if record.biomarkers_json else {}
        bio_str = ", ".join([f"{k}: {v}" for k, v in biomarkers.items()]) if biomarkers else "None entered"

        pred_label = record.prediction_label or "Pending"
        confidence = f"{record.confidence_score:.1f}%" if record.confidence_score else "N/A"
        model_version = record.model_version or "random_forest"
        obs_str = (record.observations or record.doctor_remarks or "None").strip()
        treat_str = (record.treatment_notes or "None").strip()

        system_prompt = (
            "You are SmartHealth's Clinical AI Assistant, a general health education and clinical decision-support conversational assistant. "
            "Answer the user's exact question accurately, directly, and concisely.\n\n"
            "BEHAVIOR RULES:\n"
            "1. Mode A (Case-Specific Questions): When questions concern the current patient case or refer to 'this patient', 'the result', 'the prediction', 'this biomarker', or case details, use the supplied patient case context accurately.\n"
            "2. Mode B (General Health & Wellness Questions): When questions ask about general health topics (e.g., nutrition, exercise, sleep, hydration, stress, general disease prevention, medical terms), answer naturally as a general health educator WITHOUT forcing them into the patient's case or starting responses with 'Based on the patient's prediction...'.\n"
            "3. Multi-Turn Context: Maintain natural, continuous conversation context across follow-up questions.\n"
            "4. Fact Precision: Never invent patient data, laboratory values, symptoms, diagnoses, or treatment facts not present in the supplied case.\n"
            "5. Clinical Distinction: Clearly distinguish between ML model pattern predictions ('The ML model predicted...') and confirmed clinical diagnoses.\n"
            "6. Emergency / Urgent Symptoms: If potentially life-threatening or urgent symptoms (e.g. severe chest pain, sudden paralysis, loss of consciousness) are mentioned, recommend immediate emergency medical care.\n"
            "7. Directness: Answer the user's exact question first. Do not repeat the entire case summary unless specifically requested.\n\n"
            f"CURRENT PATIENT CASE CONTEXT (Use ONLY when question relates to current patient case):\n"
            f"- Case ID: #{case_id}\n"
            f"- Presenting Symptoms: {sym_str}\n"
            f"- Preliminary Differential Considerations: {cand_str}\n"
            f"- Investigations Ordered/Performed: {inv_str}\n"
            f"- Actual Entered Biomarkers: {bio_str}\n"
            f"- ML Model Verdict: {pred_label} (Model: {model_version}, Confidence: {confidence})\n"
            f"- Doctor Observations: {obs_str}\n"
            f"- Doctor Treatment Plan: {treat_str}"
        )

        groq_api_key = current_app.config.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
        answer = None

        if groq_api_key:
            import urllib.request
            import json as py_json
            
            messages = [{"role": "system", "content": system_prompt}]
            for item in conversation_history[-6:]:
                if isinstance(item, dict) and item.get("role") in ("user", "assistant") and item.get("content"):
                    messages.append({"role": item["role"], "content": str(item["content"])})
            messages.append({"role": "user", "content": user_question})

            groq_models = ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.6-27b", "llama-3.3-70b-versatile", "llama3-8b-8192"]
            
            for groq_model in groq_models:
                try:
                    req_payload = py_json.dumps({
                        "model": groq_model,
                        "messages": messages,
                        "temperature": 0.3,
                        "max_tokens": 800
                    }).encode("utf-8")

                    req = urllib.request.Request(
                        "https://api.groq.com/openai/v1/chat/completions",
                        data=req_payload,
                        headers={
                            "Authorization": f"Bearer {groq_api_key}",
                            "Content-Type": "application/json",
                            "User-Agent": "SmartHealth-ClinicalAI/2026"
                        },
                        method="POST"
                    )

                    with urllib.request.urlopen(req, timeout=15) as response:
                        res_body = py_json.loads(response.read().decode("utf-8"))
                        if res_body.get("choices") and len(res_body["choices"]) > 0:
                            answer = res_body["choices"][0]["message"]["content"].strip()
                            break
                except Exception as groq_err:
                    logger.warning(f"[Ask AI] Groq model '{groq_model}' attempt failed: {groq_err}.")

        if not answer:
            if groq_api_key:
                logger.error("[Ask AI] All Groq models failed — falling back to templated reasoning engine.")
            else:
                logger.warning("[Ask AI] GROQ_API_KEY not configured — using templated fallback engine.")
            # High-Quality Clinical & Health Fallback Engine
            q_lower = user_question.lower()

            # Mode B: General Health & Wellness Questions
            if "food" in q_lower or "eat" in q_lower or "diet" in q_lower or "nutrition" in q_lower or "breakfast" in q_lower:
                if "iron" in q_lower:
                    answer = "Iron-rich foods include red meat, poultry, seafood, spinach, legumes (beans, lentils), tofu, pumpkin seeds, and iron-fortified cereals. Pairing plant-based iron with Vitamin C enhances absorption."
                elif "breakfast" in q_lower:
                    answer = "Healthy breakfast options include oatmeal topped with nuts and berries, eggs with whole-grain toast and spinach, Greek yogurt with fruit, or a smoothie with leafy greens and protein powder."
                else:
                    answer = "A balanced daily diet emphasizes whole foods: fruits, vegetables, whole grains (oats, quinoa, brown rice), lean proteins (fish, poultry, beans), healthy fats (olive oil, nuts, avocados), and adequate hydration."

            elif "exercise" in q_lower or "walking" in q_lower or "physical activity" in q_lower or "20 minutes" in q_lower or "workout" in q_lower:
                if "20 minutes" in q_lower or "short" in q_lower or "time" in q_lower:
                    answer = "Even 20 minutes of daily activity provides substantial cardiovascular and metabolic benefits. A 20-minute brisk walk, bodyweight circuit (squats, push-ups, lunges), or stationary cycling is highly effective."
                elif "walking" in q_lower:
                    answer = "Regular walking improves cardiovascular fitness, supports joint health, enhances mood, assists weight management, and helps regulate blood glucose levels. Aiming for 30 minutes daily is a great target."
                else:
                    answer = "For general wellness, health guidelines recommend at least 150 minutes of moderate-intensity aerobic exercise (such as brisk walking or swimming) per week, combined with strength training 2 days a week."

            elif "sleep" in q_lower or "insomnia" in q_lower or "rest" in q_lower:
                answer = "Healthy sleep habits include maintaining a consistent sleep schedule, keeping the bedroom dark and cool, avoiding screens 30–60 minutes before bed, and limiting caffeine or heavy meals in the evening. Most adults require 7–9 hours per night."

            elif "water" in q_lower or "hydration" in q_lower or "drink" in q_lower:
                answer = "Adults generally require about 2 to 3 liters (8–12 cups) of fluid per day, depending on climate, activity level, and overall health. Adequate hydration supports kidney function, energy, and circulation."

            elif "heart" in q_lower or "cardiovascular" in q_lower:
                answer = "To maintain heart health: engage in regular aerobic exercise, eat a fiber-rich diet low in saturated fats, keep blood pressure and cholesterol in check, manage stress, avoid smoking, and maintain a healthy weight."

            elif "headache" in q_lower or "headaches" in q_lower:
                answer = "Common causes of headaches include tension/stress, dehydration, lack of sleep, eye strain, caffeine withdrawal, or sinus pressure. Sudden or severe 'thunderclap' headaches warrant immediate medical evaluation."

            elif "resting heart rate" in q_lower or "heart rate" in q_lower:
                answer = "A normal resting heart rate for adults ranges from 60 to 100 beats per minute (bpm). Well-conditioned athletes may have resting heart rates as low as 40–60 bpm."

            # Mode A: Case-Specific Questions
            else:
                matched_bio_key = None
                for key in biomarkers.keys():
                    if key.lower() in q_lower:
                        matched_bio_key = key
                        break
                
                if matched_bio_key:
                    val = biomarkers[matched_bio_key]
                    answer = f"For this patient, **{matched_bio_key}** is recorded as **{val}**. In evaluating **{pred_label}**, this biomarker provides specific physiological evidence. "
                    if "hba1c" in matched_bio_key.lower():
                        answer += f"An HbA1c of {val}% measures 2–3 month average glycemic control."
                    elif "platelet" in matched_bio_key.lower():
                        answer += f"A platelet count of {val} reflects megakaryocyte thrombopoiesis and clotting capability."
                    elif "creatinine" in matched_bio_key.lower():
                        answer += f"A creatinine of {val} mg/dL assesses renal filtration capacity."
                    elif "glucose" in matched_bio_key.lower():
                        answer += f"A blood glucose level of {val} mg/dL reflects current circulating glycemia."
                    elif "hemoglobin" in matched_bio_key.lower():
                        answer += f"A hemoglobin concentration of {val} g/dL reflects oxygen transport capability."
                
                elif "hba1c" in q_lower:
                    if "HbA1c" in biomarkers:
                        answer = f"The patient's HbA1c level is **{biomarkers['HbA1c']}%**. HbA1c reflects average blood glucose control over the preceding 8–12 weeks."
                    else:
                        answer = "HbA1c was not included in the lab panel for this case. In clinical practice, HbA1c evaluates long-term glycemic control (≥ 6.5% indicates Diabetes)."
                
                elif "platelet" in q_lower:
                    if "Platelets" in biomarkers:
                        answer = f"The patient's platelet count is **{biomarkers['Platelets']} x10³/µL**, evaluating thrombopoiesis and hemostatic capacity."
                    else:
                        answer = "Platelet count was not recorded in this patient's lab panel."
                
                elif "creatinine" in q_lower:
                    if "Creatinine" in biomarkers:
                        answer = f"The patient's serum creatinine is **{biomarkers['Creatinine']} mg/dL**, assessing renal clearance."
                    else:
                        answer = "Creatinine was not recorded in this patient's lab panel."

                elif "confidence" in q_lower or "score" in q_lower or "%" in q_lower:
                    answer = (
                        f"The confidence score of **{confidence}** represents the ML model's ({model_version}) pattern similarity density "
                        f"between this patient's biomarker inputs and the reference distribution for **{pred_label}**. "
                        "It reflects statistical pattern match probability, but requires clinical correlation."
                    )

                elif "why" in q_lower or "predict" in q_lower or "reason" in q_lower:
                    answer = (
                        f"The model predicted **{pred_label}** with **{confidence}** confidence because the patient's presenting symptoms "
                        f"({sym_str}) and laboratory values ({bio_str}) strongly aligned with the model's trained pattern clusters for {pred_label}."
                    )

                elif "difference" in q_lower or "versus" in q_lower or "vs" in q_lower or "compared" in q_lower:
                    answer = (
                        f"In this case, preliminary considerations identified potential candidates: {cand_str}. "
                        f"The ML biomarker model predicted **{pred_label}** based on the entered laboratory values ({bio_str})."
                    )

                elif "simple" in q_lower or "terms" in q_lower:
                    answer = (
                        f"In simple terms: The patient presented with {sym_str}. Lab tests showed {bio_str}. "
                        f"The decision-support algorithm evaluated these findings and identified **{pred_label}** as the primary prediction."
                    )

                elif "verify" in q_lower or "confirm" in q_lower or "information" in q_lower or "help" in q_lower:
                    answer = (
                        f"To verify the prediction of **{pred_label}**, the attending clinician can review confirmatory diagnostic testing, "
                        f"monitor clinical symptoms, and evaluate targeted follow-up investigations ({inv_str})."
                    )

                else:
                    answer = (
                        f"Regarding '{user_question}': For Case #{case_id} (Predicted: {pred_label}, Confidence: {confidence}), "
                        f"the patient presented with symptoms ({sym_str}) and recorded biomarkers ({bio_str})."
                    )

        disclaimer = "Clinical Decision-Support Notice: AI answers assist clinician decision-making and do not replace professional judgment or confirmed diagnosis."

        return jsonify({
            "status": "success",
            "question": user_question,
            "answer": answer,
            "disclaimer": disclaimer,
            "context": {
                "prediction": pred_label,
                "confidence": confidence,
                "biomarkers": bio_str
            }
        }), 200

    except Exception as exc:
        logger.exception(f"[API] Error in ask_ai_case: {exc}")
        return jsonify({
            "error": "Unable to generate an AI response right now. Please try again.",
            "status": "failed",
            "details": str(exc) if current_app.debug else None,
        }), 500


@api_bp.route("/cases/<int:case_id>/reports", methods=["POST"])
def build_case_report(case_id):
    record, err_resp = get_authorized_case(case_id)
    if err_resp:
        return err_resp

    try:
        data = request.get_json(force=True, silent=True) or {}
        sections = data.get("sections", [
            "Patient Details", "Presenting Symptoms", "Preliminary Assessment",
            "Recommended Investigations", "Investigations Performed", "Results/Biomarkers",
            "Predicted Diagnosis", "AI Clinical Summary", "Doctor Notes", "Doctor Identity/Signature"
        ])
        signature = data.get("doctor_signature", f"Dr. User #{session.get('user_id')}")

        if "observations" in data:
            record.observations = data["observations"]
        if "treatment_notes" in data:
            record.treatment_notes = data["treatment_notes"]
        if "doctor_remarks" in data:
            record.doctor_remarks = data["doctor_remarks"]
        if "final_diagnosis" in data:
            record.final_diagnosis = data["final_diagnosis"]
        if "ai_explanation" in data:
            record.ai_explanation = data["ai_explanation"]

        import uuid
        report_uuid = f"REP-{uuid.uuid4().hex[:8].upper()}"
        pdf_filename = f"Report_{report_uuid}.pdf"

        from backend.api.pdf_report import generate_case_report_pdf
        output_path = os.path.join(current_app.config["REPORTS_FOLDER"], pdf_filename)
        generate_case_report_pdf(record, sections, signature, output_path)

        from backend.database.models import GeneratedReport
        gr = GeneratedReport(
            case_id=case_id,
            report_uuid=report_uuid,
            selected_sections_json=json.dumps(sections),
            doctor_signature=signature,
            pdf_filename=pdf_filename
        )
        db.session.add(gr)
        
        record.report_sections = json.dumps(sections)
        record.doctor_signature = signature
        record.status = "approved"
        record.case_status = "Reported/Archived"
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Report generated successfully.",
            "case_status": record.case_status,
            "report": gr.to_dict(),
            "download_url": f"/api/cases/{case_id}/reports/{report_uuid}/download",
        }), 201
    except Exception as exc:
        db.session.rollback()
        logger.exception(f"[API] Error in build_case_report: {exc}")
        return jsonify({
            "error": "Internal server error.",
            "status": "failed",
            "details": str(exc) if current_app.debug else None,
        }), 500


@api_bp.route("/cases/<int:case_id>/reports/<string:report_uuid>/download", methods=["GET"])
def download_case_report(case_id, report_uuid):
    """Serve a previously generated PDF, regenerating it on the fly if the
    file itself didn't survive a redeploy (Render's disk is ephemeral) —
    all the source data lives in the database, so this is always possible."""
    from flask import send_from_directory
    record, err_resp = get_authorized_case(case_id)
    if err_resp:
        return err_resp

    from backend.database.models import GeneratedReport
    gr = GeneratedReport.query.filter_by(case_id=case_id, report_uuid=report_uuid).first()
    if not gr:
        return jsonify({"error": "Report not found."}), 404

    reports_folder = current_app.config["REPORTS_FOLDER"]
    full_path = os.path.join(reports_folder, gr.pdf_filename)

    if not os.path.exists(full_path):
        from backend.api.pdf_report import generate_case_report_pdf
        sections = json.loads(gr.selected_sections_json) if gr.selected_sections_json else []
        generate_case_report_pdf(record, sections, gr.doctor_signature, full_path)

    return send_from_directory(reports_folder, gr.pdf_filename, as_attachment=True, download_name=gr.pdf_filename)
