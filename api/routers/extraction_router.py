from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.schemas.extraction_schema import ExtractionRequest, ExtractionResultSchema
from api.services.extraction import extraction_service
from core.database import get_db
from core.firebase_auth import get_current_user
from api.schemas.user_schema import UserResponse

router = APIRouter(
    prefix="/extract",
    tags=["Extraction"]
)

@router.post("", response_model=ExtractionResultSchema)
async def create_extraction(
    request: ExtractionRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    return await extraction_service.extract_from_document(
        db=db,
        user_id=current_user.id,
        document_id=request.document_id,
        template_id=request.template_id
    )