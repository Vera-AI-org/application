from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from models import template_model, field_model, document_model
from api.schemas import template_schema
from ..llm.llm_service import TemplateLLMService

def generate_and_create_template(db: Session, user_id: int, template_info: template_schema.TemplateGenerationRequest) -> template_model.Template:
    document = db.query(document_model.Document).filter(
        document_model.Document.id == template_info.document_id,
        document_model.Document.user_id == user_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")

    llm_service = TemplateLLMService()
    generated_data = llm_service.generate_template_from_document(
        doc_markdown=document.markdown_content,
        selections=template_info.selections,
        template_name=template_info.name
    )

    fields_from_llm = [
        template_schema.FieldCreate(**f) for f in generated_data.get("fields", [])
    ]

    print(f"Dados gerados pelo LLM: {generated_data}")
    
    template_create_data = template_schema.TemplateCreate(
        name=generated_data.get("name", template_info.name),
        description=generated_data.get("description"),
        segmentation_strategy=generated_data.get("segmentation_strategy"),
        fields=fields_from_llm
    )
    
    return create_user_template(db, user_id, template_create_data)


def create_user_template(db: Session, user_id: int, template: template_schema.TemplateCreate) -> template_model.Template:
    db_template = template_model.Template(
        user_id=user_id,
        name=template.name,
        description=template.description,
        segmentation_strategy=template.segmentation_strategy
    )
    
    db.add(db_template)
    db.commit()
    db.refresh(db_template)

    for field_data in template.fields:
        db_field = field_model.Field(
            template_id=db_template.id,
            **field_data.model_dump()
        )
        db.add(db_field)
    
    db.commit()
    db.refresh(db_template)

    return db_template

def get_templates_by_user(db: Session, user_id: int) -> List[template_model.Template]:
    return db.query(template_model.Template).filter(template_model.Template.user_id == user_id).all()