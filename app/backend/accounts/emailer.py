"""Transactional email over SMTP (Mailtrap in production).

Configuration (environment):
    OM_SMTP_HOST, OM_SMTP_PORT, OM_SMTP_USER, OM_SMTP_PASSWORD, OM_SMTP_FROM
    OM_PUBLIC_URL  (default https://openmagnetics.com — used to build links)

Emails are sent from FastAPI background tasks; a failure is logged loudly and
never breaks the request that queued it. Endpoints whose whole purpose is the
email (password reset) return 503 when SMTP is not configured instead of
pretending to have sent something.
"""
import os
import smtplib
import sys
from email.message import EmailMessage


def smtp_configured() -> bool:
    return all(os.getenv(v) for v in ("OM_SMTP_HOST", "OM_SMTP_PORT", "OM_SMTP_USER", "OM_SMTP_PASSWORD", "OM_SMTP_FROM"))


def public_url() -> str:
    return os.getenv("OM_PUBLIC_URL", "https://openmagnetics.com").rstrip("/")


def send_email(to: str, subject: str, body: str):
    if not smtp_configured():
        raise RuntimeError("SMTP is not configured (OM_SMTP_* environment variables missing)")
    message = EmailMessage()
    message["From"] = os.getenv("OM_SMTP_FROM")
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(os.getenv("OM_SMTP_HOST"), int(os.getenv("OM_SMTP_PORT"))) as server:
        server.starttls()
        server.login(os.getenv("OM_SMTP_USER"), os.getenv("OM_SMTP_PASSWORD"))
        server.send_message(message)


def send_email_background(to: str, subject: str, body: str):
    """Wrapper for BackgroundTasks: log failures loudly, never raise into the void."""
    try:
        send_email(to, subject, body)
    except Exception as error:  # noqa: BLE001 — background task, log and surface in server logs
        print(f"EMAIL SEND FAILED to={to} subject={subject!r}: {error}", file=sys.stderr, flush=True)


def verification_email(token: str):
    link = f"{public_url()}/verify_email?token={token}"
    return ("Verify your OpenMagnetics email",
            f"Welcome to OpenMagnetics!\n\n"
            f"Click to verify your email address:\n{link}\n\n"
            f"Verifying lets you recover your password. The link is valid for 7 days.\n"
            f"If you did not create this account, ignore this email.")


def password_reset_email(token: str):
    link = f"{public_url()}/reset_password?token={token}"
    return ("Reset your OpenMagnetics password",
            f"A password reset was requested for your OpenMagnetics account.\n\n"
            f"Click to set a new password:\n{link}\n\n"
            f"The link is valid for 1 hour. If you did not request this, ignore this email.")
