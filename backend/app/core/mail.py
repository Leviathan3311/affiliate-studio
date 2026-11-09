import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

log = logging.getLogger(__name__)


def send(to: str, subject: str, body: str) -> None:
    """Send a plain-text email over SMTP. Without SMTP settings, dev prints it to the log."""
    s = get_settings()
    if not s.smtp_host:
        if s.env == "dev":
            log.warning("SMTP not configured; email to %s:\n%s", to, body)
        else:
            log.error("SMTP not configured; email to %s was not sent", to)
        return
    msg = EmailMessage()
    msg["From"] = s.smtp_from or s.smtp_user
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=20) as smtp:
            smtp.starttls()
            if s.smtp_user:
                smtp.login(s.smtp_user, s.smtp_password)
            smtp.send_message(msg)
    except (OSError, smtplib.SMTPException) as e:
        log.error("Email to %s failed: %s", to, type(e).__name__)
