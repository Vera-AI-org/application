from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from api.services.document import document_service  
from core.database import get_db
from core.firebase_auth import get_current_user
from api.schemas.user_schema import UserResponse
from api.schemas.document_schema import DocumentSchema
from api.schemas.pattern_schema import PatternSchema
from api.schemas.regex_generation_request import RegexGenerationRequest
router = APIRouter(
    prefix="/document",
    tags=["Document"]
)

@router.post("/upload", response_model=DocumentSchema)
async def upload_pdfs(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    file: UploadFile = File(...),
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
    
    pattern_data = request.selections[0]

    print(pattern_data)
    new_pattern = await document_service.handle_generate_regex(
        db=db, 
        user_id=current_user.id, 
        pattern=pattern_data,
        document_id= document_id
    )

    return new_pattern

@router.delete(
    "/delete-pattern/{pattern_id}", 
    response_model=DeleteSuccessResponse,
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
