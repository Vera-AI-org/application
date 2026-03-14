from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.firebase_auth import get_current_user
from api.schemas.user_schema import UserResponse
from api.schemas.template_schema import TemplateCreate, TemplateResponse, FieldCreate, FieldResponse
from models.template_model import Template
from models.field_model import Field


router = APIRouter(
    prefix="/templates",
    tags=["Templates"],
)


@router.get("", response_model=list[TemplateResponse])
def list_templates(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """List all templates belonging to the authenticated user, including their fields."""
    templates = (
        db.query(Template)
        .filter(Template.user_id == current_user.id)
        .order_by(Template.name)
        .all()
    )
    return templates


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    body: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Create a new template for the authenticated user."""
    template = Template(
        name=body.name,
        description=body.description,
        user_id=current_user.id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Delete a template (and all its fields and jobs) by ID."""
    template = (
        db.query(Template)
        .filter(Template.id == template_id, Template.user_id == current_user.id)
        .first()
    )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template com ID {template_id} não encontrado ou sem permissão.",
        )
    db.delete(template)
    db.commit()


@router.post(
    "/{template_id}/fields",
    response_model=FieldResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_field(
    template_id: int,
    body: FieldCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Add a field to a template. Only one field should have is_key=True."""
    template = (
        db.query(Template)
        .filter(Template.id == template_id, Template.user_id == current_user.id)
        .first()
    )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template com ID {template_id} não encontrado ou sem permissão.",
        )

    # Enforce single key field
    if body.is_key:
        existing_key = (
            db.query(Field)
            .filter(Field.template_id == template_id, Field.is_key == True)
            .first()
        )
        if existing_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O template já possui um campo chave: '{existing_key.name}'. "
                       "Remova-o antes de adicionar outro campo chave.",
            )

    field = Field(
        name=body.name,
        description=body.description,
        is_key=body.is_key,
        template_id=template_id,
    )
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@router.delete(
    "/{template_id}/fields/{field_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_field(
    template_id: int,
    field_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Remove a field from a template."""
    # Verify template ownership
    template = (
        db.query(Template)
        .filter(Template.id == template_id, Template.user_id == current_user.id)
        .first()
    )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template com ID {template_id} não encontrado ou sem permissão.",
        )

    field = (
        db.query(Field)
        .filter(Field.id == field_id, Field.template_id == template_id)
        .first()
    )
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campo com ID {field_id} não encontrado neste template.",
        )

    db.delete(field)
    db.commit()