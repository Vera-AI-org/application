from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from typing import List, Dict, Any
from core.config import settings
from pathlib import Path
import json

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
    TEMPLATE_FOLDER=Path(__file__).parent / 'template'
)

async def send_extraction_email(email_to: EmailStr, results: Dict[str, Any]):
    template_body = {
        "results": json.dumps(results, indent=4)
    }

    message = MessageSchema(
        subject="Extração de Documento Concluída",
        recipients=[email_to],
        template_body=template_body,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message, template_name="template/extraction_template.html")