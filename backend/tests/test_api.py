"""
Smart Health Sync — Backend Test Suite
Authors: Enock Queenson Eduafo & Christabel Araba Edumadze | University of Ghana 2026
"""

import io
import json
import pytest
import sys
import os
from unittest.mock import patch

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


# ── Health checks ─────────────────────────────────────────────
class TestHealthEndpoints:
    def test_health_returns_200(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_health_body(self, client):
        data = json.loads(client.get("/api/health").data)
        assert data["status"] == "online"
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

    def _login_doctor(self, client):
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["role"] = "doctor"
            sess["email"] = "dr.test@example.com"
            sess["full_name"] = "Dr. Test"
            sess["status"] = "approved"

    def test_predict_valid_input(self, client):
        self._login_doctor(client)
        payload = {"features": self.HEALTHY_FEATURES, "model": "random_forest"}
        resp = client.post("/api/predict",
                           data=json.dumps(payload),
                           content_type="application/json")
        assert resp.status_code in (200, 403, 503)

    def test_predict_missing_features(self, client):
        self._login_doctor(client)
        payload = {"features": {"Glucose": 0.5}, "model": "random_forest"}
        resp = client.post("/api/predict",
                           data=json.dumps(payload),
                           content_type="application/json")
        assert resp.status_code in (200, 400, 403, 503)

    def test_predict_no_body(self, client):
        self._login_doctor(client)
        resp = client.post("/api/predict", content_type="application/json")
        assert resp.status_code in (200, 400, 403)

    def test_predict_missing_features_key(self, client):
        self._login_doctor(client)
        payload = {"model": "random_forest"}
        resp = client.post("/api/predict",
                           data=json.dumps(payload),
                           content_type="application/json")
        assert resp.status_code in (200, 400, 403)

    def test_predict_if_models_loaded(self, client):
        """If models are actually available, ensure full result structure."""
        self._login_doctor(client)
        hr = json.loads(client.get("/api/health/models").data)
        if not hr.get("loaded_models"):
            pytest.skip("No models loaded in test environment")

        payload = {"features": self.HEALTHY_FEATURES}
        resp = client.post("/api/predict",
                           data=json.dumps(payload),
                           content_type="application/json")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "success"
        assert "prediction" in data or "record_id" in data


# ── Pages ────────────────────────────────────────────────────
class TestPages:
    def test_index_page(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_predict_page(self, client):
        resp = client.get("/predict")
        assert resp.status_code in (200, 302)

    def test_results_page(self, client):
        resp = client.get("/results")
        assert resp.status_code == 200

    def test_about_page(self, client):
        resp = client.get("/about")
        assert resp.status_code == 200


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
    """Insert a pending doctor directly and return the User object."""
    from backend.database.models import Notification
    with app.app_context():
        existing = User.query.filter_by(email="dr.test@example.com").first()
        if existing:
            Notification.query.filter_by(user_id=existing.id).delete()
            db.session.delete(existing)
            db.session.commit()

        doctor = User(
            username="dr.test@example.com",
            email="dr.test@example.com",
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
        "/api/auth/verify",
        data=json.dumps({"doctor_id": doctor_id, "action": action}),
        content_type="application/json",
    )


class TestEmailNotifications:
    """Verify the admin→approve/reject flow short-circuits when Resend is unset,
    and actually sends when RESEND_API_KEY is configured."""

    def test_approve_skips_email_when_resend_not_configured(
        self, app, client, pending_doctor
    ):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RESEND_API_KEY", None)

            try:
                import resend
                with patch("resend.Emails.send") as mock_send:
                    resp = _approve_as_admin(client, pending_doctor, "approve")
                    assert resp.status_code == 200
                    assert mock_send.call_count == 0
            except ImportError:
                resp = _approve_as_admin(client, pending_doctor, "approve")
                assert resp.status_code == 200

    def test_reject_skips_email_when_resend_not_configured(
        self, app, client, pending_doctor
    ):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RESEND_API_KEY", None)

            try:
                import resend
                with patch("resend.Emails.send") as mock_send:
                    resp = _approve_as_admin(client, pending_doctor, "reject")
                    assert resp.status_code == 200
                    assert mock_send.call_count == 0
            except ImportError:
                resp = _approve_as_admin(client, pending_doctor, "reject")
                assert resp.status_code == 200

    def test_approve_calls_resend_when_api_key_is_set(
        self, app, client, pending_doctor
    ):
        with patch.dict(os.environ, {"RESEND_API_KEY": "test_key_abc"}, clear=False):
            try:
                import resend
                with patch("resend.Emails.send") as mock_send:
                    resp = _approve_as_admin(client, pending_doctor, "approve")
                    assert resp.status_code == 200
                    assert mock_send.call_count == 1
            except ImportError:
                resp = _approve_as_admin(client, pending_doctor, "approve")
                assert resp.status_code == 200

    def test_reject_calls_resend_when_api_key_is_set(
        self, app, client, pending_doctor
    ):
        with patch.dict(os.environ, {"RESEND_API_KEY": "test_key_abc"}, clear=False):
            try:
                import resend
                with patch("resend.Emails.send") as mock_send:
                    resp = _approve_as_admin(client, pending_doctor, "reject")
                    assert resp.status_code == 200
                    assert mock_send.call_count == 1
            except ImportError:
                resp = _approve_as_admin(client, pending_doctor, "reject")
                assert resp.status_code == 200
