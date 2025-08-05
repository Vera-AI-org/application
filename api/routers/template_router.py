from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..schemas import template_schema
from ..services.template import template_service
from core.database import get_db
from core.firebase_auth import get_current_user
from api.schemas.user_schema import UserResponse

router = APIRouter(
    prefix="/templates",
    tags=["Templates"]
)

@router.post("", response_model=template_schema.Template)
def generate_template(
    template_info: template_schema.TemplateGenerationRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    return template_service.generate_and_create_template(
        db=db, user_id=current_user.id, template_info=template_info
    )

@router.get("", response_model=List[template_schema.Template])
def get_templates(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    return template_service.get_templates_by_user(db=db, user_id=current_user.id)