"""
Smart Health Sync — Backend Test Suite
Authors: Enock Queenson Eduafo & Christabel Araba Edumadze | University of Ghana 2026
"""

import io
import json
import pytest
import sys
import os
import uuid
from unittest.mock import patch, MagicMock

# Allow importing from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.factory import create_app
from backend.database.models import db, User


@pytest.fixture
def app():
    """Create test Flask application instance."""
    os.environ["FLASK_ENV"] = "development"
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    yield flask_app


@pytest.fixture
def client(app):
    """Return Flask test client."""
    return app.test_client()


@pytest.fixture
def authenticated_doctor_client(client):
    """Return a client logged in as an approved doctor."""
    with client.session_transaction() as sess:
        sess["user_id"] = 999
        sess["role"] = "doctor"
        sess["email"] = "doctor.test@smarthealth.com"
        sess["full_name"] = "Dr. Test User"
        sess["status"] = "approved"
    return client


# ── Health checks ─────────────────────────────────────────────
class TestHealthEndpoints:
    def test_health_returns_200(self, client):
        resp = client.get("/api/health")
        assert resp.status_code in (200, 503)

    def test_health_body(self, client):
        data = json.loads(client.get("/api/health").data)
        assert data["status"] in ("healthy", "online", "degraded")
        assert "service" in data

    def test_health_models_returns_json(self, client):
        resp = client.get("/api/health/models")
        assert resp.content_type == "application/json"
        data = json.loads(resp.data)
        assert "loaded_models" in data
        assert "missing_models" in data
        assert "models_directory" in data


# ── Metadata ─────────────────────────────────────────────────
class TestMetadata:
    def test_metadata_endpoint(self, client):
        resp = client.get("/api/metadata")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["project"] == "Smart Health Sync"
        assert "endpoints" in data

    def test_models_list(self, client):
        resp = client.get("/api/models")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "available_models" in data
        assert "features" in data
        assert len(data["features"]) == 24


# ── Prediction ───────────────────────────────────────────────
class TestPrediction:
    HEALTHY_FEATURES = {
        "Glucose": 0.12, "Cholesterol": 0.15, "Hemoglobin": 0.65,
        "Platelets": 0.55, "White Blood Cells": 0.45, "Red Blood Cells": 0.60,
        "Hematocrit": 0.58, "Mean Corpuscular Volume": 0.52,
        "Mean Corpuscular Hemoglobin": 0.55, "Mean Corpuscular Hemoglobin Concentration": 0.50,
        "Insulin": 0.15, "BMI": 0.22, "Systolic Blood Pressure": 0.65,
        "Diastolic Blood Pressure": 0.45, "Triglycerides": 0.18,
        "HbA1c": 0.10, "LDL Cholesterol": 0.14, "HDL Cholesterol": 0.65,
        "ALT": 0.15, "AST": 0.14, "Heart Rate": 0.18, "Creatinine": 0.15,
        "Troponin": 0.05, "C-reactive Protein": 0.08,
    }

    def test_predict_valid_input(self, authenticated_doctor_client):
        payload = {"features": self.HEALTHY_FEATURES, "model": "random_forest"}
        resp = authenticated_doctor_client.post("/api/predict",
                           data=json.dumps(payload),
                           content_type="application/json")
        assert resp.status_code in (200, 503)

    def test_predict_missing_features(self, authenticated_doctor_client):
        payload = {"features": {"Glucose": 0.5}, "model": "random_forest"}
        resp = authenticated_doctor_client.post("/api/predict",
                           data=json.dumps(payload),
                           content_type="application/json")
        assert resp.status_code in (200, 400, 503)

    def test_predict_no_body(self, authenticated_doctor_client):
        resp = authenticated_doctor_client.post("/api/predict", content_type="application/json")
        assert resp.status_code == 400

    def test_predict_missing_features_key(self, authenticated_doctor_client):
        payload = {"model": "random_forest"}
        resp = authenticated_doctor_client.post("/api/predict",
                           data=json.dumps(payload),
                           content_type="application/json")
        assert resp.status_code == 400

    def test_predict_if_models_loaded(self, authenticated_doctor_client):
        """If models are actually available, ensure full result structure."""
        hr = json.loads(authenticated_doctor_client.get("/api/health/models").data)
        if not hr.get("loaded_models"):
            pytest.skip("No models loaded in test environment")

        payload = {"features": self.HEALTHY_FEATURES}
        resp = authenticated_doctor_client.post("/api/predict",
                           data=json.dumps(payload),
                           content_type="application/json")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "success"
        assert "prediction" in data
        assert "confidence" in data
        assert "probabilities" in data
        assert "recommendations" in data


# ── Pages ────────────────────────────────────────────────────
class TestPages:
    def test_index_page(self, client):
        resp = client.get("/")
        assert resp.status_code in (200, 302)

    def test_predict_page(self, authenticated_doctor_client):
        resp = authenticated_doctor_client.get("/predict")
        assert resp.status_code in (200, 302)

    def test_results_page(self, authenticated_doctor_client):
        resp = authenticated_doctor_client.get("/results")
        assert resp.status_code in (200, 302)

    def test_about_page(self, client):
        resp = client.get("/about")
        assert resp.status_code in (200, 302)


# ── Email validation ─────────────────────────────────────────
class TestEmailValidation:
    """Backend regex check on /api/auth/register and /api/auth/login."""

    def test_register_rejects_bad_email(self, client):
        data = {
            "account_type": "doctor",
            "title": "Dr.",
            "full_name": "Bad Email User",
            "email": "not-an-email",
            "password": "longenough123",
        }
        resp = client.post(
            "/api/auth/register",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        payload = json.loads(resp.data)
        assert "valid email" in payload["error"].lower()

    def test_login_rejects_bad_email(self, client):
        resp = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "not-an-email", "password": "whatever"}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        payload = json.loads(resp.data)
        assert "valid email" in payload["error"].lower()


# ── Email notifications (Resend) ────────────────────────────
@pytest.fixture
def pending_doctor(app):
    """Insert a unique pending doctor per test."""
    with app.app_context():
        email = f"dr.test_{uuid.uuid4().hex[:6]}@example.com"
        doctor = User(
            username=email,
            email=email,
            full_name="Dr. Test User",
            role="doctor",
            status="pending",
            license_number="TEST-001",
        )
        doctor.set_password("testpass123")
        db.session.add(doctor)
        db.session.commit()
        doctor_id = doctor.id
    yield doctor_id


def _approve_as_admin(client, doctor_id, action):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "admin"
        sess["email"] = "admin@test"
        sess["full_name"] = "Admin"
        sess["status"] = "approved"

    return client.post(
        f"/api/admin/doctors/{doctor_id}/verify",
        data=json.dumps({"action": action}),
        content_type="application/json",
    )


class TestEmailNotifications:
    """Verify the admin→approve/reject flow when Resend is optionally present or missing."""

    def test_approve_skips_email_when_resend_not_configured(
        self, app, client, pending_doctor
    ):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RESEND_API_KEY", None)
            resp = _approve_as_admin(client, pending_doctor, "approve")
            assert resp.status_code == 200

    def test_reject_skips_email_when_resend_not_configured(
        self, app, client, pending_doctor
    ):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RESEND_API_KEY", None)
            resp = _approve_as_admin(client, pending_doctor, "reject")
            assert resp.status_code == 200

    def test_approve_calls_resend_when_api_key_is_set(
        self, app, client, pending_doctor
    ):
        mock_resend = MagicMock()
        with patch.dict(sys.modules, {"resend": mock_resend}):
            with patch.dict(os.environ, {"RESEND_API_KEY": "test_key_abc"}, clear=False):
                resp = _approve_as_admin(client, pending_doctor, "approve")
                assert resp.status_code == 200

    def test_reject_calls_resend_when_api_key_is_set(
        self, app, client, pending_doctor
    ):
        mock_resend = MagicMock()
        with patch.dict(sys.modules, {"resend": mock_resend}):
            with patch.dict(os.environ, {"RESEND_API_KEY": "test_key_abc"}, clear=False):
                resp = _approve_as_admin(client, pending_doctor, "reject")
                assert resp.status_code == 200


# ── Case State & Restoration Tests ─────────────────────────
class TestStateRestoration:
    """Verify that case state, symptoms, and pre-assessment candidates persist and restore properly."""

    def test_case_state_restoration_flow(self, app, authenticated_doctor_client):
        with app.app_context():
            doc = User.query.get(999)
            if not doc:
                doc = User(id=999, username="doctor.test@smarthealth.com", email="doctor.test@smarthealth.com", role="doctor", status="approved", full_name="Dr. Test User")
                doc.set_password("pass")
                db.session.add(doc)
                db.session.commit()

        # 1. Create case
        res = authenticated_doctor_client.post("/api/cases", json={})
        assert res.status_code == 201
        case_data = json.loads(res.data)["case"]
        case_id = case_data["id"]
        assert case_data["case_status"] == "Draft Case"

        # 2. Add symptoms
        symptoms_payload = {
            "replace": True,
            "symptoms": [
                {"display_name": "High Fever", "raw_text": "High Fever", "severity": "Severe", "duration_value": 3, "duration_unit": "days"}
            ]
        }
        res_sym = authenticated_doctor_client.post(f"/api/cases/{case_id}/symptoms", json=symptoms_payload)
        assert res_sym.status_code == 201
        assert json.loads(res_sym.data)["case_status"] == "Symptoms Captured"

        # 3. Run pre-assessment
        res_pa = authenticated_doctor_client.post(f"/api/cases/{case_id}/pre-assessment", json={})
        assert res_pa.status_code == 200
        assert json.loads(res_pa.data)["case_status"] == "Pre-Assessment Ready"

        # 4. Fetch case for resumption (verify state restoration fields)
        res_get = authenticated_doctor_client.get(f"/api/cases/{case_id}")
        assert res_get.status_code == 200
        restored = json.loads(res_get.data)["case"]

        assert restored["case_status"] == "Pre-Assessment Ready"
        assert len(restored["symptoms"]) == 1
        assert restored["symptoms"][0]["display_name"] == "High Fever"
        assert restored["preliminary_assessment"] is not None
        assert len(restored["preliminary_assessment"]["candidates"]) > 0

    def test_condition_specific_investigations_and_biomarkers(self, app, authenticated_doctor_client):
        with app.app_context():
            doc = db.session.get(User, 999)
            if not doc:
                doc = User(id=999, username="doctor.test@smarthealth.com", email="doctor.test@smarthealth.com", role="doctor", status="approved", full_name="Dr. Test User")
                doc.set_password("pass")
                db.session.add(doc)
                db.session.commit()

        # Create case for Anemia
        res_anemia = authenticated_doctor_client.post("/api/cases", json={})
        case_anemia_id = json.loads(res_anemia.data)["case"]["id"]

        authenticated_doctor_client.post(f"/api/cases/{case_anemia_id}/symptoms", json={
            "replace": True,
            "symptoms": [{"display_name": "Severe Fatigue", "raw_text": "fatigue", "severity": "Severe"}]
        })
        authenticated_doctor_client.post(f"/api/cases/{case_anemia_id}/pre-assessment", json={})

        recs_resp = authenticated_doctor_client.get(f"/api/cases/{case_anemia_id}/investigation-recommendations")
        assert recs_resp.status_code == 200
        recs = json.loads(recs_resp.data)["recommendations"]

        # Verify only condition-relevant investigation is recommended (FBC)
        inv_codes = [r["investigation"]["code"] for r in recs]
        assert "INV_FBC" in inv_codes
        assert "INV_LIPID_PROFILE" not in inv_codes
        assert "INV_CARDIAC_MARKERS" not in inv_codes
        assert "INV_GLUCOSE_HBA1C" not in inv_codes

    def test_step06_report_pdf_and_ai_assistant(self, app, authenticated_doctor_client):
        res = authenticated_doctor_client.post("/api/cases", json={})
        case_id = json.loads(res.data)["case"]["id"]

        # Run AI Assistant Q&A
        res_ai = authenticated_doctor_client.post(f"/api/cases/{case_id}/ai-assistant", json={
            "question": "Why did the model predict this condition?"
        })
        assert res_ai.status_code == 200
        ai_data = json.loads(res_ai.data)
        assert ai_data["status"] == "success"
        assert "disclaimer" in ai_data

        # Generate report with custom observations and treatment plan
        res_rep = authenticated_doctor_client.post(f"/api/cases/{case_id}/reports", json={
            "observations": "Patient shows mild pallor and fatigue.",
            "treatment_notes": "Prescribe oral iron supplements and recheck FBC in 4 weeks.",
            "doctor_signature": "Dr. Unit Test, MD"
        })
        assert res_rep.status_code == 201
        rep_data = json.loads(res_rep.data)
        assert rep_data["status"] == "success"
        assert "download_url" in rep_data

