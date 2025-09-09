from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from typing import List, Dict, Any
from core.config import settings
from pathlib import Path
import pandas as pd
import io

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / "template"
)

async def send_email_with_attachment(
    email_to: EmailStr,
    subject: str,
    template_name: str,
    template_body: Dict[str, Any],
    attachment_data: List[Dict[str, Any]],
    attachment_filename: str
):
    if not attachment_data:
        return

    df = pd.DataFrame(attachment_data)
    
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=template_body,
        subtype="html",
        attachments=[(attachment_filename, "text/csv", output.getvalue())]
    )

    fm = FastMail(conf)
    await fm.send_message(message, template_name=template_name)