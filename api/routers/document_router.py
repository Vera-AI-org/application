from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from api.services.document import document_service 
from core.database import get_db
from core.firebase_auth import get_current_user
from api.schemas.user_schema import UserResponse
from api.schemas.document_schema import DocumentSchema
from models import extraction_model
from api.schemas.extraction_schema import ExtractionResultSchema
from typing import List

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

@router.post("/upload", response_model=DocumentSchema)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    return await document_service.create_document(
        db=db, 
        user_id=current_user.id, 
        file=file
    )

@router.get("/document/{document_id}", response_model=List[ExtractionResultSchema])
def get_extractions_for_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    extractions = db.query(extraction_model.Extraction).filter(
        extraction_model.Extraction.document_id == document_id,
        extraction_model.Extraction.user_id == current_user.id
    ).order_by(extraction_model.Extraction.created_at.desc()).all()
    
    return extractions