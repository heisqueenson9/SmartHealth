"""
Smart Health Sync — Email notifications via Resend HTTP API.

Sends approval/rejection emails to doctors. Silently no-ops when RESEND_API_KEY
is not configured (e.g. local dev), so the verify handlers can fire without
wiring real credentials.
"""

import logging
import os

logger = logging.getLogger("smarthealth.mail")


def _is_mail_configured() -> bool:
    """Return True only when RESEND_API_KEY is set in the environment."""
    return bool(os.environ.get("RESEND_API_KEY", "").strip())


def _sender() -> str:
    """Default sender address. Override via MAIL_DEFAULT_SENDER env var."""
    return os.environ.get("MAIL_DEFAULT_SENDER", "Smart Health Sync <onboarding@resend.dev>")


def _login_url() -> str:
    """Best-effort absolute login URL; falls back to /login."""
    try:
        from flask import url_for
        return url_for("views.login_page", _external=True)
    except Exception:
        return "/login"


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
