from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from api.services.template import template_service  
from core.database import get_db
from core.firebase_auth import get_current_user
from api.schemas.user_schema import UserResponse
from api.schemas.template_schema import TemplateCreateResponse, TemplateDto
from api.DTO.create_template_request import CreateTemplateRequest
from typing import List


router = APIRouter(
    prefix="/template",
    tags=["Template"]
)

@router.post("", response_model=TemplateCreateResponse)
async def create_template(
    request: CreateTemplateRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    
    new_template = await template_service.handle_create(
        db=db, 
        user_id=current_user.id, 
        template_data=request
    )

    return new_template


@router.get("", response_model=List[TemplateDto])
async def list_by_authenticated_user(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    templates = await template_service.handle_get_all(
        db=db,
        user_id=current_user.id
    )
    return templates