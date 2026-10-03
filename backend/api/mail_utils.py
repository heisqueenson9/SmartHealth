"""
Smart Health Sync — Centralized Email Service via Resend HTTP API.
Authors: Enock Queenson Eduafo & Christabel Araba Edumadze | University of Ghana 2026

Handles sending all application emails (account verification/approval/rejection,
prediction notifications, welcome emails, password reset, admin alerts).
Reads MAIL_API_KEY securely from environment without hardcoding or logging secrets.
Captures safe Resend Message IDs and returns structured delivery status.
Silently and safely fails gracefully if MAIL_API_KEY is missing or invalid.
"""

import logging
import os
from typing import List, Optional, Union
from flask import current_app

logger = logging.getLogger("smarthealth.mail")


class EmailResult:
    """Structured result wrapper for email operations."""

    def __init__(
        self,
        success: bool,
        status: str,
        message_id: Optional[str] = None,
        message: str = "",
        error: Optional[str] = None,
    ):
        self.success = success
        self.status = status  # "accepted", "failed", "unconfigured", "invalid_recipient"
        self.message_id = message_id
        self.message = message
        self.error = error

    def __bool__(self) -> bool:
        return self.success

    def __repr__(self) -> str:
        return f"<EmailResult success={self.success} status='{self.status}' message_id='{self.message_id}'>"

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "status": self.status,
            "message_id": self.message_id,
            "message": self.message,
            "error": self.error,
        }


def is_mail_configured() -> bool:
    """Return True if MAIL_API_KEY (or fallback RESEND_API_KEY) is set in the environment."""
    key = os.environ.get("MAIL_API_KEY", "").strip() or os.environ.get("RESEND_API_KEY", "").strip()
    return bool(key)


def _get_api_key() -> str:
    """Retrieve Resend API key securely from environment."""
    return os.environ.get("MAIL_API_KEY", "").strip() or os.environ.get("RESEND_API_KEY", "").strip()


def _get_sender() -> str:
    """
    Return sender address.
    Checks MAIL_FROM or MAIL_DEFAULT_SENDER env vars; defaults to Resend test sender:
    'Smart Health Sync <onboarding@resend.dev>'
    """
    sender = os.environ.get("MAIL_FROM", "").strip() or os.environ.get("MAIL_DEFAULT_SENDER", "").strip()
    if not sender:
        sender = "Smart Health Sync <onboarding@resend.dev>"
    return sender


def _get_site_url() -> str:
    """Absolute site URL for links in emails (e.g. login, reset password)."""
    try:
        site_url = current_app.config.get("SITE_URL", "http://localhost:5000")
    except RuntimeError:
        site_url = os.environ.get("SITE_URL", "http://localhost:5000")
    return site_url.rstrip("/")


def _clean_recipient(to: Union[str, List[str]]) -> List[str]:
    """Clean, strip whitespace, and validate recipient email addresses."""
    recipients = []
    items = [to] if isinstance(to, str) else list(to)
    for item in items:
        if isinstance(item, str):
            clean = item.strip()
            if clean and "@" in clean and len(clean) >= 5:
                recipients.append(clean)
    return recipients


def send_email(
    to: Union[str, List[str]],
    subject: str,
    text: Optional[str] = None,
    html: Optional[str] = None,
    sender: Optional[str] = None,
) -> EmailResult:
    """
    Centralized email sender service using official Resend Python SDK.

    Returns EmailResult object (evaluates to True/False for backward compatibility).
    Captures safe Resend Message ID (e.g. msg_12345).
    Guarantees no application/Gunicorn crash on email failure or missing key.
    Logs safely without exposing API keys or secrets.
    """
    if not is_mail_configured():
        logger.info("[Mail] MAIL_API_KEY configured: false — skipping email send.")
        return EmailResult(
            success=False,
            status="unconfigured",
            message="MAIL_API_KEY is not configured in environment.",
            error="MAIL_API_KEY missing",
        )

    api_key = _get_api_key()
    if not api_key:
        logger.info("[Mail] MAIL_API_KEY configured: false — empty key string.")
        return EmailResult(
            success=False,
            status="unconfigured",
            message="MAIL_API_KEY is empty.",
            error="MAIL_API_KEY empty",
        )

    recipients = _clean_recipient(to)
    if not recipients:
        logger.warning("[Mail] Invalid or empty recipient provided.")
        return EmailResult(
            success=False,
            status="invalid_recipient",
            message="Recipient email address is invalid or empty.",
            error="Invalid recipient",
        )

    try:
        import resend
    except ImportError:
        logger.warning("[Mail] resend Python package is not installed; skipping email.")
        return EmailResult(
            success=False,
            status="failed",
            message="resend package not installed.",
            error="ImportError: resend",
        )

    from_addr = sender or _get_sender()

    payload = {
        "from": from_addr,
        "to": recipients,
        "subject": subject,
    }
    if html:
        payload["html"] = html
    if text:
        payload["text"] = text
    if not html and not text:
        payload["text"] = "No message body provided."

    try:
        resend.api_key = api_key
        logger.info("[Mail] MAIL_API_KEY configured: true — attempting email send via Resend.")
        raw_res = resend.Emails.send(payload)

        # Extract Resend Message ID (e.g. msg_123456789 or UUID)
        msg_id = None
        if isinstance(raw_res, dict):
            msg_id = raw_res.get("id")
        elif hasattr(raw_res, "id"):
            msg_id = getattr(raw_res, "id", None)
        elif hasattr(raw_res, "get") and callable(raw_res.get):
            msg_id = raw_res.get("id")

        if msg_id:
            logger.info("[Mail] Email accepted by Resend. Message ID: %s", msg_id)
            return EmailResult(
                success=True,
                status="accepted",
                message_id=str(msg_id),
                message=f"Email request accepted by Resend (Message ID: {msg_id}).",
            )
        else:
            logger.warning("[Mail] Resend API call completed but returned no message ID: %s", type(raw_res).__name__)
            return EmailResult(
                success=False,
                status="failed",
                message_id=None,
                message="Resend request did not yield a valid message ID.",
                error="No message ID returned from Resend.",
            )

    except getattr(resend, "ResendError", Exception) as resend_err:
        err_type = type(resend_err).__name__
        logger.warning("[Mail] Resend API error sending email: %s", err_type)
        return EmailResult(
            success=False,
            status="failed",
            error=err_type,
            message=f"Resend API error: {err_type}",
        )
    except Exception as exc:
        err_type = type(exc).__name__
        logger.warning("[Mail] Network or unexpected error sending email: %s", err_type)
        return EmailResult(
            success=False,
            status="failed",
            error=err_type,
            message=f"Network error sending email: {err_type}",
        )


def notify_doctor_status_change(doctor, action: str) -> EmailResult:
    """Send approval or rejection status email to a doctor."""
    if action not in ("approve", "reject", "reupload"):
        logger.warning("[Mail] Unknown status action: %s", action)
        return EmailResult(success=False, status="invalid_action", message="Unknown status action.")

    doc_email = getattr(doctor, "email", None)
    if not doc_email:
        logger.warning("[Mail] Cannot send doctor status email — doctor has no email address.")
        return EmailResult(success=False, status="invalid_recipient", message="Doctor has no email address.")

    doc_name = getattr(doctor, "full_name", "Doctor") or "Doctor"
    login_url = f"{_get_site_url()}/login"

    if action == "approve":
        subject = "Smart Health Sync — Account Approved"
        text = (
            f"Dear {doc_name},\n\n"
            "We are pleased to inform you that your doctor account at Smart Health Sync "
            "has been approved and is now active.\n\n"
            "You can now log in to the portal and start using our clinical diagnosis tools.\n\n"
            f"Log In Here: {login_url}\n\n"
            "Best regards,\n"
            "The Smart Health Sync Team"
        )
        html = f"""
        <div style="font-family:sans-serif; max-width:520px; margin:0 auto;">
          <h2 style="color:#1b3a4b;">Account Approved</h2>
          <p>Dear {doc_name},</p>
          <p>We are pleased to inform you that your doctor account at <strong>Smart Health Sync</strong> has been approved and is now active.</p>
          <p><a href="{login_url}" style="display:inline-block; padding:10px 18px; background:#2563eb; color:#ffffff; text-decoration:none; border-radius:6px;">Log In to Portal</a></p>
          <p style="color:#888; font-size:12px; margin-top:24px;">Smart Health Sync — University of Ghana 2026</p>
        </div>
        """
    else:
        subject = "Smart Health Sync — Account Registration Status"
        text = (
            f"Dear {doc_name},\n\n"
            "Thank you for registering with Smart Health Sync.\n\n"
            "Unfortunately, your doctor registration request was not approved at this time. "
            "Reason: Your uploaded document was rejected or did not meet our verification criteria.\n\n"
            "If you believe this was in error, please log back into your account "
            "to re-submit a valid professional medical certificate or credential for verification.\n\n"
            "Best regards,\n"
            "The Smart Health Sync Team"
        )
        html = f"""
        <div style="font-family:sans-serif; max-width:520px; margin:0 auto;">
          <h2 style="color:#b91c1c;">Account Registration Update</h2>
          <p>Dear {doc_name},</p>
          <p>Thank you for registering with <strong>Smart Health Sync</strong>.</p>
          <p>Unfortunately, your doctor registration request was not approved at this time because your uploaded document did not meet our verification criteria.</p>
          <p>Please log back into your account to re-submit a valid medical certificate or credential.</p>
          <p><a href="{login_url}">Log In Here</a></p>
          <p style="color:#888; font-size:12px; margin-top:24px;">Smart Health Sync — University of Ghana 2026</p>
        </div>
        """

    return send_email(to=doc_email, subject=subject, text=text, html=html)


def notify_prediction_ready(doctor, record, result: dict) -> EmailResult:
    """Email a doctor that a case's ML prediction has completed."""
    doc_email = getattr(doctor, "email", None)
    if not doc_email:
        logger.warning("[Mail] Cannot send prediction email — doctor has no email address.")
        return EmailResult(success=False, status="invalid_recipient", message="Doctor has no email address.")

    case_ref = getattr(record, "patient_reference", None) or f"Case #{getattr(record, 'id', 'N/A')}"
    doc_name = getattr(doctor, "full_name", doc_email) or doc_email
    subject = f"Smart Health Sync — Prediction Ready for Review ({case_ref})"

    html = f"""
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
    text = (
        f"Hi Dr. {doc_name},\n\n"
        f"The AI prediction for {case_ref} is ready:\n"
        f"Predicted Diagnosis: {result.get('prediction', 'N/A')}\n"
        f"Confidence: {result.get('confidence', 0):.1f}%\n\n"
        "Please log in to review the full case."
    )
    return send_email(to=doc_email, subject=subject, text=text, html=html)


def send_welcome_email(user) -> EmailResult:
    """Send a welcome email to a newly registered patient or doctor."""
    user_email = getattr(user, "email", None)
    if not user_email:
        return EmailResult(success=False, status="invalid_recipient", message="User has no email address.")
    user_name = getattr(user, "full_name", "User") or "User"
    subject = "Welcome to Smart Health Sync"
    text = (
        f"Welcome to Smart Health Sync, {user_name}!\n\n"
        "Your account has been created. Log in at any time to access your clinical dashboard.\n\n"
        f"Log In: {_get_site_url()}/login"
    )
    html = f"""
    <div style="font-family:sans-serif; max-width:520px; margin:0 auto;">
      <h2 style="color:#1b3a4b;">Welcome to Smart Health Sync</h2>
      <p>Hello {user_name},</p>
      <p>Your account has been successfully created. You can now access your clinical diagnostic portal.</p>
      <p><a href="{_get_site_url()}/login" style="display:inline-block; padding:10px 18px; background:#2563eb; color:#ffffff; text-decoration:none; border-radius:6px;">Log In</a></p>
    </div>
    """
    return send_email(to=user_email, subject=subject, text=text, html=html)


def send_password_reset_email(user, reset_url: str) -> EmailResult:
    """Send a password reset instructions email."""
    user_email = getattr(user, "email", None)
    if not user_email:
        return EmailResult(success=False, status="invalid_recipient", message="User has no email address.")
    user_name = getattr(user, "full_name", "User") or "User"
    subject = "Smart Health Sync — Password Reset Request"
    text = (
        f"Hello {user_name},\n\n"
        "We received a request to reset your password. Use the link below to set a new password:\n\n"
        f"{reset_url}\n\n"
        "If you did not request this, please ignore this message."
    )
    html = f"""
    <div style="font-family:sans-serif; max-width:520px; margin:0 auto;">
      <h2 style="color:#1b3a4b;">Reset Your Password</h2>
      <p>Hello {user_name},</p>
      <p>We received a request to reset your password. Click below to continue:</p>
      <p><a href="{reset_url}" style="display:inline-block; padding:10px 18px; background:#2563eb; color:#ffffff; text-decoration:none; border-radius:6px;">Reset Password</a></p>
      <p style="color:#888; font-size:12px;">If you did not request a password reset, you can safely ignore this email.</p>
    </div>
    """
    return send_email(to=user_email, subject=subject, text=text, html=html)
