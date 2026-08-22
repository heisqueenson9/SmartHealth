"""
Smart Health Sync — Database Models
Authors: Enock Queenson Eduafo & Christabel Araba Edumadze | University of Ghana 2026
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    """System users (Administrators / Healthcare Providers)."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='provider')  # admin, doctor, patient
    full_name = db.Column(db.String(120), nullable=True)
    hospital = db.Column(db.String(120), nullable=True)
    specialization = db.Column(db.String(120), nullable=True)
    license_number = db.Column(db.String(64), nullable=True)
    proof_filename = db.Column(db.String(256), nullable=True)
    proof_data = db.Column(db.LargeBinary, nullable=True)
    proof_mimetype = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='pending')  # approved, pending, rejected
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    records = db.relationship(
        'DiagnosticRecord',
        backref='author',
        lazy='dynamic',
        foreign_keys='DiagnosticRecord.user_id',
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Patient(db.Model):
    """Patient profile linked to a registered patient user account."""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, unique=True, index=True)
    patient_uuid = db.Column(db.String(36), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10))
    blood_group = db.Column(db.String(5))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Doctor Case Management fields
    full_name = db.Column(db.String(120), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    clinical_notes = db.Column(db.Text, nullable=True)
    is_archived = db.Column(db.Boolean, default=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    user = db.relationship('User', backref=db.backref('patient_profile', uselist=False), foreign_keys=[user_id])
    doctor = db.relationship('User', backref=db.backref('doctor_patients', lazy='dynamic'), foreign_keys=[doctor_id])
    diagnostic_history = db.relationship(
        'DiagnosticRecord',
        backref='patient',
        lazy='dynamic',
        foreign_keys='DiagnosticRecord.patient_id',
    )


class DoctorPatientConnection(db.Model):
    """Relationship between a doctor (User) and a patient (Patient profile)."""
    __tablename__ = 'doctor_patient_connections'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    doctor = db.relationship('User', backref=db.backref('patient_connections', lazy='dynamic'))
    patient = db.relationship('Patient', backref=db.backref('doctor_connections', lazy='dynamic'))


class DoctorTechnicianConnection(db.Model):
    """Relationship between a doctor (User) and a technician (User)."""
    __tablename__ = 'doctor_technician_connections'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref=db.backref('technician_connections', lazy='dynamic'))
    technician = db.relationship('User', foreign_keys=[technician_id], backref=db.backref('doctor_connections_tech', lazy='dynamic'))


class DiagnosticRecord(db.Model):
    """Records of specific AI-powered diagnostic sessions."""
    __tablename__ = 'diagnostic_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_reference = db.Column(db.String(64), nullable=True)
    biomarkers_json = db.Column(db.Text, nullable=True)
    result_json = db.Column(db.Text, nullable=True)
    prediction_label = db.Column(db.String(64), nullable=False, default='Pending Assessment')
    confidence_score = db.Column(db.Float, nullable=False, default=0.0)
    model_version = db.Column(db.String(32), nullable=True)
    status = db.Column(db.String(32), default='draft')  # draft, approved, archived
    case_status = db.Column(db.String(64), default='Draft Case') # Draft Case -> Symptoms Captured -> Pre-Assessment Ready -> Investigations Selected -> Results Available -> Prediction Available -> Case Reviewed -> Reported/Archived
    doctor_remarks = db.Column(db.Text, nullable=True)
    
    # New review module columns
    final_diagnosis = db.Column(db.String(120), nullable=True)
    observations = db.Column(db.Text, nullable=True)
    treatment_notes = db.Column(db.Text, nullable=True)
    ai_explanation = db.Column(db.Text, nullable=True)
    report_sections = db.Column(db.Text, nullable=True)
    doctor_signature = db.Column(db.String(120), nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Additive relationships
    case_symptoms = db.relationship('PatientCaseSymptom', backref='case', lazy='dynamic', cascade='all, delete-orphan')
    preliminary_assessments = db.relationship('PreliminaryAssessment', backref='case', lazy='dynamic', cascade='all, delete-orphan')
    case_investigations = db.relationship('CaseInvestigation', backref='case', lazy='dynamic', cascade='all, delete-orphan')
    predictions = db.relationship('ModelPrediction', backref='case', lazy='dynamic', cascade='all, delete-orphan')
    ai_summaries = db.relationship('AISummary', backref='case', lazy='dynamic', cascade='all, delete-orphan')
    reports = db.relationship('GeneratedReport', backref='case', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        import json
        p_dict = {}
        if self.patient:
            p_dict = {
                "patient_name": f"{self.patient.first_name or ''} {self.patient.last_name or ''}".strip() or self.patient.full_name,
                "patient_uuid": self.patient.patient_uuid,
                "patient_dob": self.patient.date_of_birth.strftime('%d %b %Y') if self.patient.date_of_birth else '—',
                "patient_gender": self.patient.gender or '—',
                "patient_email": self.patient.user.email if (self.patient.user and self.patient.user.email) else '—'
            }
        
        symptoms_data = [s.to_dict() for s in self.case_symptoms.all()]
        pa_latest = self.preliminary_assessments.order_by(PreliminaryAssessment.created_at.desc()).first()
        pa_data = pa_latest.to_dict() if pa_latest else None
        investigations_data = [inv.to_dict() for inv in self.case_investigations.all()]

        base_dict = {
            "id": self.id,
            "patient_reference": self.patient_reference,
            "prediction": self.prediction_label,
            "predicted_diagnosis": self.prediction_label,
            "confidence": self.confidence_score,
            "model_used": self.model_version,
            "status": self.status,
            "case_status": self.case_status or 'Draft Case',
            "doctor_remarks": self.doctor_remarks,
            "final_diagnosis": self.final_diagnosis,
            "observations": self.observations,
            "treatment_notes": self.treatment_notes,
            "ai_explanation": self.ai_explanation,
            "report_sections": json.loads(self.report_sections) if self.report_sections else None,
            "doctor_signature": self.doctor_signature,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "biomarkers": json.loads(self.biomarkers_json) if self.biomarkers_json else {},
            "result": json.loads(self.result_json) if self.result_json else {},
            "symptoms": symptoms_data,
            "preliminary_assessment": pa_data,
            "investigations": investigations_data,
        }
        base_dict.update(p_dict)
        return base_dict


class Notification(db.Model):
    """Notification alerts for doctors and admins."""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ModelAuditLog(db.Model):
    """Audit logging for model performance and usage tracking."""
    __tablename__ = 'model_audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    model_key = db.Column(db.String(64), nullable=False)
    action = db.Column(db.String(64))  # load, predict, update
    status = db.Column(db.String(20))  # success, failure
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ─── Additive Workflow Schema Extensions ───────────────────────

class SymptomCatalog(db.Model):
    """Standardized catalog of medical symptoms."""
    __tablename__ = 'symptom_catalog'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(64), nullable=True)
    synonyms_json = db.Column(db.Text, nullable=True) # list of synonym strings
    description = db.Column(db.Text, nullable=True)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "code": self.code,
            "display_name": self.display_name,
            "category": self.category,
            "synonyms": json.loads(self.synonyms_json) if self.synonyms_json else [],
            "description": self.description
        }


class PatientCaseSymptom(db.Model):
    """Symptom entry captured for a patient case session."""
    __tablename__ = 'patient_case_symptoms'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('diagnostic_records.id'), nullable=False, index=True)
    standard_symptom_id = db.Column(db.Integer, db.ForeignKey('symptom_catalog.id'), nullable=True)
    display_name = db.Column(db.String(120), nullable=False)
    raw_text = db.Column(db.String(256), nullable=False)
    source = db.Column(db.String(20), default='selected') # selected, typed, other
    duration_value = db.Column(db.Integer, nullable=True)
    duration_unit = db.Column(db.String(20), default='days') # days, weeks, months, hours
    severity = db.Column(db.String(20), default='Moderate') # Mild, Moderate, Severe
    notes = db.Column(db.Text, nullable=True)
    mapping_confidence = db.Column(db.Float, default=1.0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    standard_symptom = db.relationship('SymptomCatalog', backref='case_references')

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "standard_symptom_id": self.standard_symptom_id,
            "display_name": self.display_name,
            "raw_text": self.raw_text,
            "source": self.source,
            "duration_value": self.duration_value,
            "duration_unit": self.duration_unit,
            "severity": self.severity,
            "notes": self.notes,
            "mapping_confidence": self.mapping_confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class PreliminaryAssessment(db.Model):
    """Pre-assessment analysis generated from patient presentation."""
    __tablename__ = 'preliminary_assessments'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('diagnostic_records.id'), nullable=False, index=True)
    status = db.Column(db.String(32), default='completed')
    summary_text = db.Column(db.Text, nullable=True)
    disclaimer = db.Column(db.Text, default="This is a preliminary clinical consideration based on reported symptoms, not a confirmed diagnosis.")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    candidates = db.relationship('AssessmentCandidate', backref='assessment', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "status": self.status,
            "summary_text": self.summary_text,
            "disclaimer": self.disclaimer,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "candidates": [c.to_dict() for c in self.candidates.order_by(AssessmentCandidate.rank).all()]
        }


class AssessmentCandidate(db.Model):
    """Candidate condition identified during preliminary assessment."""
    __tablename__ = 'assessment_candidates'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('preliminary_assessments.id'), nullable=False, index=True)
    condition_name = db.Column(db.String(120), nullable=False)
    rank = db.Column(db.Integer, nullable=False, default=1)
    score = db.Column(db.Float, default=0.0)
    rationale = db.Column(db.Text, nullable=True)
    supported_by_biomarker_model = db.Column(db.Boolean, default=False)
    unsupported_note = db.Column(db.String(256), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "condition_name": self.condition_name,
            "rank": self.rank,
            "score": self.score,
            "rationale": self.rationale,
            "supported_by_biomarker_model": self.supported_by_biomarker_model,
            "unsupported_note": self.unsupported_note
        }


class InvestigationCatalog(db.Model):
    """Catalog of supported lab tests and diagnostic investigations."""
    __tablename__ = 'investigation_catalog'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(64), default='Laboratory') # Laboratory, Imaging, Vital Signs, Special Test
    biomarker_keys_json = db.Column(db.Text, nullable=True) # list of FEATURE_ORDER keys
    description = db.Column(db.Text, nullable=True)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "category": self.category,
            "biomarker_keys": json.loads(self.biomarker_keys_json) if self.biomarker_keys_json else [],
            "description": self.description
        }


class InvestigationRule(db.Model):
    """Clinical rule mapping candidate conditions/symptoms to recommended investigations."""
    __tablename__ = 'investigation_rules'

    id = db.Column(db.Integer, primary_key=True)
    condition_name = db.Column(db.String(120), nullable=False, index=True)
    symptom_trigger_json = db.Column(db.Text, nullable=True)
    recommended_investigation_id = db.Column(db.Integer, db.ForeignKey('investigation_catalog.id'), nullable=False)
    priority = db.Column(db.String(20), default='High') # High, Medium, Low
    reason = db.Column(db.Text, nullable=False)

    recommended_investigation = db.relationship('InvestigationCatalog')


class CaseInvestigation(db.Model):
    """Investigations ordered/selected for a specific patient case."""
    __tablename__ = 'case_investigations'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('diagnostic_records.id'), nullable=False, index=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigation_catalog.id'), nullable=False)
    priority = db.Column(db.String(20), default='High')
    reason = db.Column(db.Text, nullable=True)
    source_rule_id = db.Column(db.Integer, nullable=True)
    doctor_selected = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(32), default='selected') # recommended, selected, pending, completed, cancelled
    result_type = db.Column(db.String(32), default='numeric') # numeric, categorical, text, panel
    required_for_model = db.Column(db.Boolean, default=True)

    investigation = db.relationship('InvestigationCatalog')
    results = db.relationship('InvestigationResult', backref='case_investigation', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "investigation_id": self.investigation_id,
            "investigation_name": self.investigation.name if self.investigation else "Unknown Test",
            "category": self.investigation.category if self.investigation else "Laboratory",
            "priority": self.priority,
            "reason": self.reason,
            "doctor_selected": self.doctor_selected,
            "status": self.status,
            "result_type": self.result_type,
            "required_for_model": self.required_for_model,
            "investigation": self.investigation.to_dict() if self.investigation else None,
            "results": [r.to_dict() for r in self.results.all()]
        }


class InvestigationResult(db.Model):
    """Clinical test results / biomarker values entered for a case investigation."""
    __tablename__ = 'investigation_results'

    id = db.Column(db.Integer, primary_key=True)
    case_investigation_id = db.Column(db.Integer, db.ForeignKey('case_investigations.id'), nullable=False, index=True)
    biomarker_key = db.Column(db.String(64), nullable=False)
    raw_value = db.Column(db.Float, nullable=False)
    normalized_value = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(32), nullable=True)
    measured_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "case_investigation_id": self.case_investigation_id,
            "biomarker_key": self.biomarker_key,
            "raw_value": self.raw_value,
            "normalized_value": self.normalized_value,
            "unit": self.unit,
            "measured_at": self.measured_at.isoformat() if self.measured_at else None
        }


class ModelPrediction(db.Model):
    """Supervised biomarker ML model inference result for a case."""
    __tablename__ = 'model_predictions'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('diagnostic_records.id'), nullable=False, index=True)
    model_name = db.Column(db.String(64), nullable=False)
    model_version = db.Column(db.String(32), nullable=True)
    predicted_diagnosis = db.Column(db.String(120), nullable=False)
    probability = db.Column(db.Float, nullable=False)
    probability_scores_json = db.Column(db.Text, nullable=True)
    feature_importance_json = db.Column(db.Text, nullable=True)
    data_coverage_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "case_id": self.case_id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "predicted_diagnosis": self.predicted_diagnosis,
            "probability": self.probability,
            "probability_scores": json.loads(self.probability_scores_json) if self.probability_scores_json else {},
            "feature_importance": json.loads(self.feature_importance_json) if self.feature_importance_json else {},
            "data_coverage": json.loads(self.data_coverage_json) if self.data_coverage_json else {},
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class AISummary(db.Model):
    """Expanded AI clinical summary narrating the entire case workflow."""
    __tablename__ = 'ai_summaries'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('diagnostic_records.id'), nullable=False, index=True)
    summary_text = db.Column(db.Text, nullable=False)
    symptoms_narrative = db.Column(db.Text, nullable=True)
    assessment_narrative = db.Column(db.Text, nullable=True)
    results_narrative = db.Column(db.Text, nullable=True)
    prediction_narrative = db.Column(db.Text, nullable=True)
    doctor_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "case_id": self.case_id,
            "summary_text": self.summary_text,
            "symptoms_narrative": self.symptoms_narrative,
            "assessment_narrative": self.assessment_narrative,
            "results_narrative": self.results_narrative,
            "prediction_narrative": self.prediction_narrative,
            "doctor_notes": self.doctor_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class GeneratedReport(db.Model):
    """Metadata for generated clinical reports."""
    __tablename__ = 'generated_reports'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('diagnostic_records.id'), nullable=False, index=True)
    report_uuid = db.Column(db.String(64), unique=True, nullable=False)
    selected_sections_json = db.Column(db.Text, nullable=True)
    doctor_signature = db.Column(db.String(120), nullable=True)
    pdf_filename = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "case_id": self.case_id,
            "report_uuid": self.report_uuid,
            "selected_sections": json.loads(self.selected_sections_json) if self.selected_sections_json else [],
            "doctor_signature": self.doctor_signature,
            "pdf_filename": self.pdf_filename,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
