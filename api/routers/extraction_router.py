import io
import csv

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.firebase_auth import get_current_user
from api.schemas.user_schema import UserResponse
from api.schemas.extraction_schema import ExtractionJobResponse, ExtractionJobListItem
from api.services.extraction.extraction_service import ExtractionService
from models.extraction_job_model import ExtractionJob


router = APIRouter(
    prefix="/extractions",
    tags=["Extractions"],
)

_extraction_service = ExtractionService()


@router.post("", response_model=ExtractionJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_extraction(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    template_ids: List[int] = Form(...),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Start an extraction job.
    Accepts a multipart form with:
      - files: one or more PDF files
      - template_ids: one template_id per file (same order)
    Returns the job immediately (status=pending) and processes in the background.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum arquivo enviado.",
        )
    if len(files) != len(template_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A quantidade de arquivos deve ser igual à quantidade de template_ids.",
        )

    # Read all file bytes before the request closes
    files_with_templates: list[tuple[str, bytes, int]] = []
    for upload_file, tmpl_id in zip(files, template_ids):
        content = await upload_file.read()
        files_with_templates.append((upload_file.filename or "arquivo.pdf", content, tmpl_id))

    job = _extraction_service.create_job(
        db=db,
        user_id=current_user.id,
        files_with_templates=files_with_templates,
    )

    background_tasks.add_task(
        _extraction_service.process_job,
        job_id=job.id,
        files_with_templates=files_with_templates,
    )

    return job


@router.get("", response_model=list[ExtractionJobListItem])
def list_extractions(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """List all extraction jobs for the authenticated user."""
    from models.template_model import Template

    jobs = (
        db.query(ExtractionJob)
        .filter(ExtractionJob.user_id == current_user.id)
        .order_by(ExtractionJob.created_at.desc())
        .all()
    )

    result = []
    for job in jobs:
        template_ids_used = list({dt["template_id"] for dt in (job.document_templates or [])})
        templates = db.query(Template).filter(Template.id.in_(template_ids_used)).all()
        templates_names = ", ".join(t.name for t in templates) if templates else ""
        result.append(
            ExtractionJobListItem(
                id=job.id,
                templates_names=templates_names,
                status=job.status,
                document_count=job.document_count,
                created_at=job.created_at,
            )
        )
    return result


@router.get("/{job_id}", response_model=ExtractionJobResponse)
def get_extraction(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get details of a specific extraction job, including results if done."""
    job = (
        db.query(ExtractionJob)
        .filter(ExtractionJob.id == job_id, ExtractionJob.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job de extração com ID {job_id} não encontrado ou sem permissão.",
        )
    return job


@router.get("/{job_id}/csv")
def download_csv(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Download the results of a completed extraction job as a CSV file."""
    job = (
        db.query(ExtractionJob)
        .filter(ExtractionJob.id == job_id, ExtractionJob.user_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job de extração com ID {job_id} não encontrado ou sem permissão.",
        )
    if job.status != "done":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"O job ainda não foi concluído. Status atual: {job.status}.",
        )
    if not job.results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum resultado disponível para este job.",
        )

    csv_string = _extraction_service.generate_csv(job)

    return StreamingResponse(
        io.BytesIO(csv_string.encode("utf-8-sig")),  # utf-8-sig for Excel compatibility
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=extracao_{job_id}.csv"},
    )
