import csv
import io
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from core.database import SessionLocal
from models.extraction_job_model import ExtractionJob
from models.template_model import Template
from models.field_model import Field
from api.services.llm.llm_service import LLMService


class ExtractionService:
    def create_job(
        self,
        db: Session,
        user_id: int,
        files_with_templates: list[tuple[str, bytes, int]],
    ) -> ExtractionJob:
        """
        Validate all template IDs belong to the user, create an ExtractionJob
        with status=pending and return it.
        files_with_templates: list of (filename, bytes, template_id) tuples
        """
        # Validate every template belongs to this user
        for filename, _, template_id in files_with_templates:
            template = (
                db.query(Template)
                .filter(Template.id == template_id, Template.user_id == user_id)
                .first()
            )
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Template com ID {template_id} não encontrado ou sem permissão.",
                )

        document_templates = [
            {"filename": filename, "template_id": template_id}
            for filename, _, template_id in files_with_templates
        ]

        job = ExtractionJob(
            user_id=user_id,
            status="pending",
            document_templates=document_templates,
            document_count=len(files_with_templates),
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    async def process_job(
        self,
        job_id: int,
        files_with_templates: list[tuple[str, bytes, int]],
    ) -> None:
        """
        Background task: for each (file, template_id) pair, extract fields using
        the template's LLM prompt, then merge all results by the key field value.
        Opens its own DB session so it's independent of the request session.
        """
        db: Session = SessionLocal()
        try:
            job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
            if not job:
                return

            job.status = "processing"
            db.commit()

            llm_service = LLMService()
            all_keyed_results: list[tuple[str, dict]] = []  # (key_value, extracted_dict)

            for filename, file_bytes, template_id in files_with_templates:
                fields = (
                    db.query(Field)
                    .filter(Field.template_id == template_id)
                    .all()
                )

                if not fields:
                    raise ValueError(
                        f"O template ID {template_id} (arquivo: {filename}) não possui campos definidos."
                    )

                key_field = next((f for f in fields if f.is_key), None)
                if not key_field:
                    raise ValueError(
                        f"O template ID {template_id} (arquivo: {filename}) não possui campo chave (is_key=True)."
                    )

                document_text = self._extract_pdf_text(file_bytes)
                extracted = llm_service.extract_fields(document_text, fields)

                key_value = extracted.get(key_field.name)
                key_str = str(key_value).strip() if key_value is not None else "__sem_chave__"
                all_keyed_results.append((key_str, extracted))

            merged = self._merge_results(all_keyed_results)

            job.results = merged
            job.status = "done"
            db.commit()

        except Exception as exc:
            try:
                job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
                if job:
                    job.status = "failed"
                    job.error_message = str(exc)
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

    def _extract_pdf_text(self, file_bytes: bytes) -> str:
        """Use pymupdf (fitz) to extract plain text from a PDF given its bytes."""
        import fitz  # pymupdf

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text

    def _merge_results(self, keyed_results: list[tuple[str, dict]]) -> dict:
        """
        Merge list of (key_value, extracted_dict) by key_value.
        When the same key appears multiple times (different templates/documents),
        non-null values from later extractions fill in missing fields.
        Returns {key_value: {field: value, ...}}
        """
        merged: dict = {}
        for key_str, extracted in keyed_results:
            if key_str not in merged:
                merged[key_str] = dict(extracted)
            else:
                for field_name, value in extracted.items():
                    if value is None:
                        continue
                    existing = merged[key_str].get(field_name)
                    if existing is None:
                        merged[key_str][field_name] = value
        return merged

    def generate_csv(self, job: ExtractionJob) -> str:
        """Generate CSV from job.results. Key values become the first column."""
        if not job.results:
            return ""

        rows = list(job.results.values())
        if not rows:
            return ""

        all_columns: list[str] = []
        for row in rows:
            for col in row.keys():
                if col not in all_columns:
                    all_columns.append(col)

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=all_columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in all_columns})

        return output.getvalue()
