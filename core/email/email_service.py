from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from typing import List, Dict, Any
from core.config import settings
from pathlib import Path
from io import BytesIO
import csv
import io
from starlette.datastructures import UploadFile
from io import BytesIO

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
    TEMPLATE_FOLDER=Path(__file__).parent / "template",
)


async def send_email_with_attachment(
    email_to: EmailStr,
    subject: str,
    template_name: str,
    template_body: Dict[str, Any],
    attachment_data: List[Dict[str, Any]],
    attachment_filename: str,
):
    fm = FastMail(conf)

    attachments = []

    if attachment_data:
        fieldnames = set()
        for row in attachment_data:
            fieldnames.update(row.keys())
        fieldnames = list(fieldnames)

        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(attachment_data)
        buffer.seek(0)

        attachments = [
            UploadFile(
                filename=attachment_filename,
                file=BytesIO(buffer.getvalue().encode("utf-8")),
            )
        ]

    print("subject", subject)
    print("email_to", email_to)
    print("template_body", template_body)
    print("attachments", attachments)

    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=template_body,
        subtype=MessageType.html,
        attachments=attachments,
    )

    await fm.send_message(message, template_name=template_name)
