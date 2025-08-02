import shutil
import uuid
import pymupdf4llm
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session
from models.pattern_model import Pattern
from .llm.llm_service import LLMService
from core.logging import get_logger
from models.document_model import Document
import tempfile

logger = get_logger(__name__)

class DocumentService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    async def upload_file(self, file: UploadFile):
        md_text = await self._extractor_text_from_pdf_to_markdown(file)

        new_document = Document(
                user_id=self.user_id,
                document_md=md_text, 
            )
        
        self.db.add(new_document)
        self.db.commit()
        self.db.refresh(new_document)

        return new_document


    async def _extractor_text_from_pdf_to_markdown(self, file: UploadFile) -> str:
        with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file.seek(0)
            
            md_text = pymupdf4llm.to_markdown(temp_file.name)

        return md_text
    

    async def generate_regex(self, pattern: dict, document_id: int, is_section: bool):
        name, regex = await self._generate_regex_from_selected_text(pattern)
        new_pattern = Pattern(
                user_id= self.user_id,
                document_id= document_id,
                name=name,
                pattern=regex,
                is_section=is_section
            )
        
        self.db.add(new_pattern)
        self.db.commit()
        self.db.refresh(new_pattern)
        return new_pattern
    
    async def _generate_regex_from_selected_text(self, pattern: dict) -> str:
        llm_service = LLMService()
        
        name, regex = llm_service.generate_regex(pattern)
        return name, regex
        
    
    
async def handle_file_upload(db: Session, user_id: int, file: UploadFile):
    service = DocumentService(db=db, user_id=user_id)
    return await service.upload_file(file) 

async def handle_generate_regex(db: Session, user_id: int, pattern: dict, document_id: int, is_section: bool):
    service = DocumentService(db=db, user_id=user_id)
    return await service.generate_regex(pattern, document_id, is_section)
