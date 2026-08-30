"""
Smart Health Sync — Email notifications via Resend HTTP API.

Sends approval/rejection emails to doctors. Silently no-ops when RESEND_API_KEY
is not configured (e.g. local dev), so the verify handlers can fire without
wiring real credentials.
"""

import logging
import os

from flask import current_app

logger = logging.getLogger("smarthealth.mail")


def _is_mail_configured() -> bool:
    """Return True only when RESEND_API_KEY is set in the environment."""
    return bool(os.environ.get("RESEND_API_KEY", "").strip())


def _sender() -> str:
    """Default sender address. Override via MAIL_DEFAULT_SENDER env var."""
    return os.environ.get("MAIL_DEFAULT_SENDER", "Smart Health Sync <onboarding@resend.dev>")


def _login_url() -> str:
    """Absolute login URL using SITE_URL config (falls back to localhost)."""
    site_url = current_app.config.get("SITE_URL", "http://localhost:5000").rstrip("/")
    return f"{site_url}/login"


def notify_doctor_status_change(doctor, action: str) -> None:
    """
    Send an automated email to a doctor on account approval or rejection.

    Silently no-ops when RESEND_API_KEY is not set, logging a single info
    line so the admin can see the skip happened.
    """
    if action not in ("approve", "reject", "reupload"):
        logger.warning("[Mail] Unknown status action: %s", action)
        return

    if not _is_mail_configured():
        logger.info(
            "[Mail] RESEND_API_KEY not configured — skipping status email to %s",
            getattr(doctor, "email", "unknown"),
        )
        return

    try:
        import resend
    except ImportError:
        logger.warning("[Mail] resend package is not installed; skipping email notification.")
        return

    if action == "approve":
        subject = "Smart Health Sync — Account Approved"
        body = (
            f"Dear {getattr(doctor, 'full_name', 'Doctor')},\n\n"
            "We are pleased to inform you that your doctor account at Smart Health Sync "
            "has been approved and is now active.\n\n"
            "You can now log in to the portal and start using our clinical diagnosis tools.\n\n"
            f"Log In Here: {_login_url()}\n\n"
            "Best regards,\n"
            "The Smart Health Sync Team"
        )
    else:
        subject = "Smart Health Sync — Account Registration Status"
        body = (
            f"Dear {getattr(doctor, 'full_name', 'Doctor')},\n\n"
            "Thank you for registering with Smart Health Sync.\n\n"
            "Unfortunately, your doctor registration request was not approved at this time. "
            "Reason: Your uploaded document was rejected or did not meet our verification criteria.\n\n"
            "If you believe this was in error, please log back into your account "
            "to re-submit a valid professional medical certificate or credential for verification.\n\n"
            "Best regards,\n"
            "The Smart Health Sync Team"
        )

    try:
        resend.api_key = os.environ["RESEND_API_KEY"]
        resend.Emails.send(
            {
                "from": _sender(),
                "to": [doctor.email],
                "subject": subject,
                "text": body,
            }
        )
        logger.info(
            "[Mail] Status email sent via Resend to %s for action: %s",
            doctor.email,
            action,
        )
    except Exception as exc:
        logger.exception(
            "[Mail] Resend failed to send status email to %s: %s",
            getattr(doctor, "email", "unknown"),
            exc,
        )


def notify_prediction_ready(doctor, record, result: dict) -> None:
    """Email a doctor that a case's ML prediction has completed."""
    if not _is_mail_configured():
        logger.info(f"[Mail] RESEND_API_KEY not configured — skipping prediction-ready email to {getattr(doctor, 'email', 'unknown')}")
        return
    subject = "Smart Health Sync — Prediction Ready for Review"
    case_ref = record.patient_reference or f"Case #{record.id}"
    doc_email = getattr(doctor, "email", "unknown")
    doc_name = getattr(doctor, "full_name", doc_email) or doc_email
    html_body = f"""
    <div style="font-family:sans-serif; max-width:520px; margin:0 auto;">
      <h2 style="color:#1b3a4b;">Prediction Ready</h2>
      <p>Hi Dr. {doc_name},</p>
      <p>The AI prediction for <strong>{case_ref}</strong> has completed:</p>
      <p style="background:#f4f4f4; padding:12px; border-radius:6px;">
        <strong>Predicted Diagnosis:</strong> {result.get('prediction', 'N/A')}<br>
        <strong>Confidence:</strong> {result.get('confidence', 0):.1f}%
      </p>
      <p>Log in to Smart Health Sync to review the full case and generate the clinical report.</p>
      <p style="color:#888; font-size:12px; margin-top:24px;">This is an automated notification from Smart Health Sync.</p>
    </div>
    """
    try:
        import resend
        resend.api_key = os.environ.get("RESEND_API_KEY")
        resend.Emails.send({
            "from": _sender(),
            "to": [doc_email],
            "subject": subject,
            "html": html_body,
        })
        logger.info(f"[Mail] Prediction-ready email sent to {doc_email}")
    except Exception as exc:
        logger.warning(f"[Mail] Failed to send prediction-ready email to {doc_email}: {exc}")
