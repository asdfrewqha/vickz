from email.message import EmailMessage
import smtplib
import ssl

from starlette.templating import Jinja2Templates

from app.core.settings import settings
from app.core.celery_config import celery_app
from app.core.logging import get_logger

logger = get_logger()


@celery_app.task
def send_confirmation_email(to_email: str, code: str) -> None:
    templates = Jinja2Templates(directory="templates")
    template = templates.get_template(name="email_confirmation.html")
    html_content = template.render(code=code)
    message = EmailMessage()
    message.add_alternative(html_content, subtype="html")
    message["From"] = settings.email_settings.email_username
    message["To"] = to_email
    message["Subject"] = f"Email confirmation <{code}>"
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(host=settings.email_settings.email_host, port=settings.email_settings.email_port, context=context) as smtp:
        smtp.login(
            user=settings.email_settings.email_username,
            password=settings.email_settings.email_password.get_secret_value(),
        )
        smtp.send_message(msg=message)
    logger.info("Email sent")
    return True


@celery_app.task
def send_confirmation_email_pwd(to_email: str, token: str) -> None:
    confirmation_url = f"{settings.frontend_url}/edit-password-confirm?token={token}"

    templates = Jinja2Templates(directory="templates")
    template = templates.get_template(name="pwd_confirmation.html")
    html_content = template.render(confirmation_url=confirmation_url, token=token)
    message = EmailMessage()
    message.add_alternative(html_content, subtype="html")
    message["From"] = settings.email_settings.email_username
    message["To"] = to_email
    message["Subject"] = "Password editing confirmation"
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(host=settings.email_settings.email_host, port=settings.email_settings.email_port, context=context) as smtp:
        smtp.login(
            user=settings.email_settings.email_username,
            password=settings.email_settings.email_password.get_secret_value(),
        )
        smtp.send_message(msg=message)
    logger.info("Email sent")
    return True
