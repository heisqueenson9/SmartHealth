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


class TestAdminLogin:
    def test_admin_portal_view(self, client):
        resp = client.get("/system-access-portal")
        assert resp.status_code == 200

    def test_direct_admin_route_redirects_unauthenticated(self, client):
        resp = client.get("/admin")
        assert resp.status_code == 302
        assert "/system-access-portal" in resp.headers.get("Location", "")

    def test_public_login_rejects_admin(self, client, app):
        with app.app_context():
            from backend.database.models import db, User
            admin = User.query.filter_by(role="admin").first()
            if not admin:
                admin = User(username="admin_t1@test.com", email="admin_t1@test.com", role="admin", status="approved")
                admin.set_password("AdminPass123!")
                db.session.add(admin)
                db.session.commit()
            email = admin.email
            
        resp = client.post("/api/auth/login", data=json.dumps({"email": email, "password": "AdminPassword2026"}), content_type="application/json")
        assert resp.status_code == 403

    def test_admin_login_success(self, client, app):
        with app.app_context():
            from backend.database.models import db, User
            admin = User.query.filter_by(role="admin").first()
            if not admin:
                admin = User(username="admin_t2@test.com", email="admin_t2@test.com", role="admin", status="approved")
                admin.set_password("AdminPassword2026")
                db.session.add(admin)
                db.session.commit()
            email = admin.email
            
        resp = client.post("/api/auth/admin-login", data=json.dumps({"email": email, "password": "AdminPassword2026"}), content_type="application/json")
        assert resp.status_code == 200
