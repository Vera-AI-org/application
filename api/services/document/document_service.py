import pymupdf4llm
import re
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
import pdfplumber
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
    

    async def generate_regex(self, pattern_data: list, document_id: int, is_section: bool):
        regex = await self._generate_regex_from_selected_text(pattern_data)
        new_pattern = Pattern(
                user_id= self.user_id,
                document_id= document_id,
                name="name",
                pattern=regex,
                is_section=is_section
            )
        
        self.db.add(new_pattern)
        self.db.commit()
        self.db.refresh(new_pattern)
        return new_pattern

    async def _generate_regex_from_selected_text(self, pattern_data: list) -> str:
        llm_service = LLMService()

        regex = llm_service.generate_regex(pattern_data)
        return regex
    
    async def _extract_text_from_pdf(self, file: UploadFile) -> str:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file.seek(0)
                
                text = ""
                with pdfplumber.open(temp_file.name) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            return text
        except Exception as e:
            logger.error(f"Falha ao extrair texto do PDF: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Não foi possível processar o arquivo PDF."
            )
        
    async def apply_regex_to_pdf(self, document_id: int, file: UploadFile) -> dict:
        logger.info(f"Iniciando extração para o document_id: {document_id}")

        patterns = self.db.query(Pattern).filter(
            Pattern.document_id == document_id,
            Pattern.user_id == self.user_id
        ).all()

        if not patterns:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nenhum padrão de regex encontrado para o documento com ID {document_id}."
            )

        pdf_text = await self._extract_text_from_pdf(file)

        extracted_data = {}
        for pattern in patterns:
            try:
                matches = re.findall(pattern.pattern, pdf_text, re.DOTALL | re.MULTILINE)
                extracted_data[pattern.name] = matches if matches else ["Nenhum resultado encontrado"]
            except re.error as e:
                logger.warning(f"Regex inválido para o padrão '{pattern.name}' (ID: {pattern.id}): {e}")
                extracted_data[pattern.name] = ["Erro: Regex inválido"]
        
        logger.info(f"Extração para o document_id: {document_id} concluída.")
        return {"filename": file.filename, "extracted_data": extracted_data}

        
    
    
async def handle_file_upload(db: Session, user_id: int, file: UploadFile):
    service = DocumentService(db=db, user_id=user_id)
    return await service.upload_file(file) 

async def handle_generate_regex(db: Session, user_id: int, pattern_data: list, document_id: int, is_section: bool):
    service = DocumentService(db=db, user_id=user_id)
    return await service.generate_regex(pattern_data, document_id, is_section) 

async def handle_apply_regex(db: Session, user_id: int, document_id: int, file: UploadFile):
    service = DocumentService(db=db, user_id=user_id)
    return await service.apply_regex_to_pdf(document_id, file)
