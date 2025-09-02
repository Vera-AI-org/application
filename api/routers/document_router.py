from fastapi import APIRouter, UploadFile, File, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from api.services.document import document_service  
from core.database import get_db
from core.firebase_auth import get_current_user
from api.schemas.user_schema import UserResponse
from api.schemas.document_schema import DocumentSchema
from api.schemas.pattern_schema import PatternSchema, PatternDeleteResponse
from api.DTO.regex_generation_request import RegexGenerationRequest
from typing import List
from api.schemas.extraction_schema import ExtractionResponse


router = APIRouter(
    prefix="/document",
    tags=["Document"]
)

@router.post("/upload", response_model=DocumentSchema)
async def upload_pdfs(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    file: UploadFile = File(...)
):
    
    new_document = await document_service.handle_file_upload(
        db=db, 
        user_id=current_user.id, 
        file=file
    )

    return new_document

@router.post("/generate-pattern", response_model=PatternSchema)
async def generate_pattern(
    request: RegexGenerationRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    document_id = request.documentId 
    
    pattern_data = request.selections
    is_section = request.isSection

    new_pattern = await document_service.handle_generate_regex(
        db=db, 
        user_id=current_user.id, 
        pattern_data=pattern_data,
        document_id= document_id,
        is_section=is_section
    )

    return new_pattern

@router.post("/apply-regex/{template_id}", status_code=status.HTTP_202_ACCEPTED)
async def apply_regex(
    template_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    background_tasks.add_task(
        document_service.handle_apply_regex_background,
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        template_id=template_id,
        file=file,
    )
    return {"message": "Received."}


@router.delete(
    "/delete-pattern/{pattern_id}", 
    response_model=PatternDeleteResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Pattern not found or permission denied"}}
)
async def delete_pattern(
    pattern_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    result_message = await document_service.handle_delete_regex(
        db=db, 
        user_id=current_user.id, 
        pattern_id=pattern_id
    )

    return result_message
