import shutil
import uuid
import pymupdf4llm
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session
from .processing.report_processor import ReportDataProcessor
from models.pattern_model import Pattern
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
    

    async def generate_regex(self, pattern: dict, document_id: int):
        name, regex = self._generate_regex_from_selected_text(pattern)
        new_pattern = Pattern(
                user_id=self.user_id,
                document_id= document_id,
                name=name,
                regex=regex,
            )
        
        self.db.add(new_pattern)
        self.db.commit()
        self.db.refresh(new_pattern)

        return new_pattern
    
    async def _generate_regex_from_selected_text(self, pattern: dict) -> str:
        llm_service = LLMService()
        return llm_service.generate_regex(pattern)
        
    
    
async def handle_file_upload(db: Session, user_id: int, file: UploadFile):
    service = DocumentService(db=db, user_id=user_id)
    return await service.upload_file(file) 

async def handle_generate_regex(db: Session, user_id: int, pattern: dict, document_id: int):
    service = DocumentService(db=db, user_id=user_id)
    return await service.generate_regex(pattern, document_id) 
