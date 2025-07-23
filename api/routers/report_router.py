from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from api.services.report import report_service 
from core.database import get_db
from core.firebase_auth import get_current_user
from api.schemas.user_schema import UserResponse
from api.schemas.report_schema import ReportSchema

router = APIRouter(
    prefix="/report",
    tags=["Report"]
)

@router.post("/upload", response_model=ReportSchema)
async def upload_pdfs(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    funcionarios: UploadFile = File(...),
    cartao_pontos: UploadFile = File(...),
    cesta: UploadFile = File(...),
    vt: UploadFile = File(...),
    funcionarios_substitutos: UploadFile = File(...)
):
    files_to_process = {
        "funcionarios": funcionarios,
        "cartao_pontos": cartao_pontos,
        "cesta": cesta,
        "vt": vt,
        "funcionarios_substitutos": funcionarios_substitutos,
    }
    
    new_report = await report_service.handle_files_upload(
        db=db, 
        user_id=current_user.id, 
        files=files_to_process
    )

    return new_report
