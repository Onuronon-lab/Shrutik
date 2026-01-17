from fastapi_mail import ConnectionConfig, FastMail, MessageSchema

from app.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


async def send_auth_email(email: str, token: str, task_type: str):

    if task_type == "verify":

        link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        subject = "Complete Your Registration - Shrutik"
    else:
        link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        subject = "Password Reset Request - Shrutik"

    html = f"""
    <h3>Shrutik Voice Platform</h3>
    <p>Please click the link below to {task_type} your account:</p>
    <a href="{link}" style="background:#007bff;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">Confirm Action</a>
    <p>If you didn't request this, please ignore this email.</p>
    """

    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=html,
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message)
