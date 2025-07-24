import shutil
import uuid
import pymupdf4llm
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session
from .processing.report_processor import ReportDataProcessor
from models.document_model import Document
from .llm.llm_service import LLMService
from core.logging import get_logger

logger = get_logger(__name__)

class DocumentService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    async def upload_file(self, file: UploadFile):
        md_text = self._extractor_text_from_pdf_to_markdown(file)
        new_document = Document(
                user_id=self.user_id,
                document_md=md_text,
            )
        
        self.db.add(new_document)
        self.db.commit()
        self.db.refresh(new_document)

        return new_document


    async def _extractor_text_from_pdf_to_markdown(self, file: UploadFile) -> str:
        logger.info("Extracting text from pdf to markdown.")
        file_bytes = file.read()
        md_text = pymupdf4llm.to_markdown(file_bytes)
        return md_text
    
    
    
async def handle_file_upload(db: Session, user_id: int, file: UploadFile):
    service = DocumentService(db=db, user_id=user_id)
    return await service.upload_file(file) 
