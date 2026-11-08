import smtplib
from email.message import EmailMessage

from app.config import settings
from app.workers.celery_app import celery


@celery.task(name="send_verification_email", bind=True, max_retries=3, default_retry_delay=10)
def send_verification_email(self, to_email: str, code: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = "Your verification code"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(
        f"Your verification code is: {code}\n\n"
        f"It expires in {settings.VERIFICATION_CODE_TTL_MINUTES} minutes."
    )

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            smtp.send_message(msg)
    except Exception as exc:
        raise self.retry(exc=exc)