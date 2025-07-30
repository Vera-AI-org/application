from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from api.services.document import document_service  
from core.database import get_db
from core.firebase_auth import get_current_user
from api.schemas.user_schema import UserResponse
from api.schemas.document_schema import DocumentSchema
from api.schemas.pattern_schema import PatternSchema

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

@router.post("/generate-regex", response_model=PatternSchema)
async def generate_regex(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    pattern: dict = {},
    document_id: int = -1
):

    new_pattern = await document_service.handle_generate_regex(
        db=db, 
        user_id=current_user.id, 
        pattern=pattern,
        document_id= document_id
    )

    return new_pattern
