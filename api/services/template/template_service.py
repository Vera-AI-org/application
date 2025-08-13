import pymupdf4llm
import re
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
import pdfplumber
from models.pattern_model import Pattern
from api.DTO.create_template_request import CreateTemplateRequest
from models.template_model import Template
import tempfile
from core.logging import get_logger

logger = get_logger(__name__)

class TemplateService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    async def create(self, template_data: CreateTemplateRequest):

        new_template = Template(
                user_id=self.user_id,
                document_id=template_data.document_id,
                name=template_data.name
            )
        
        if template_data.pattern_ids:
            patterns_to_associate = self.db.query(Pattern).filter(
                Pattern.id.in_(template_data.pattern_ids),
                Pattern.user_id == self.user_id
            ).all()

            if len(patterns_to_associate) != len(template_data.pattern_ids):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Um ou mais IDs de pattern não foram encontrados ou você não tem permissão para acessá-los."
                )
            
            new_template.patterns = patterns_to_associate

        self.db.add(new_template)
        self.db.commit()
        self.db.refresh(new_template)

        logger.info(f"Template '{new_template.name}' (ID: {new_template.id}) criado com sucesso.")
        return new_template
    
    async def _get_pattern_by_id(self, pattern_id: int):
        pattern = self.db.query(Pattern).filter(
            Pattern.id == pattern_id,
            Pattern.user_id == self.user_id 
        ).first()

        if not pattern:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Pattern not found or permission denied"
            )
        
        return pattern
    async def get_all_by_user(self) -> list[Template]:
        logger.info(f"Buscando todos os templates para o usuário ID: {self.user_id}")
        templates = self.db.query(Template).filter(Template.user_id == self.user_id).order_by(Template.name).all()
        return templates
    
    
async def handle_create(db: Session, user_id: int, template_data: CreateTemplateRequest):
    service = TemplateService(db=db, user_id=user_id)
    return await service.create(template_data) 

async def handle_get_all(db: Session, user_id: int):
    service = TemplateService(db=db, user_id=user_id)
    return await service.get_all_by_user()