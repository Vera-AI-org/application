import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session
from .processing.report_processor import ReportDataProcessor
from models.report_model import Report
from .llm.llm_service import LLMService

BASE_TEMP_DIR = Path("files/temp")

class ReportService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    async def _save_files_to_unique_dir(self, files: dict[str, UploadFile], unique_dir: Path) -> dict:
        saved_paths = {}
        for name, file in files.items():
            if file and file.filename:
                file_path = unique_dir / file.filename
                with open(file_path, "wb") as buffer:
                    buffer.write(await file.read())
                saved_paths[name] = str(file_path)
        return saved_paths

    async def process(self, files: dict[str, UploadFile]) -> Report:
        BASE_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        request_temp_dir = BASE_TEMP_DIR / str(uuid.uuid4())
        request_temp_dir.mkdir()

        try:
            saved_file_paths = await self._save_files_to_unique_dir(files, request_temp_dir)
            
            llm_service = LLMService()
            processor = ReportDataProcessor(
                file_paths=saved_file_paths,
                output_dir=request_temp_dir,
                llm_service=llm_service
            )
            final_df, analysis_text = processor.run()
            
            new_report = Report(
                user_id=self.user_id,
                data=final_df.to_dict(orient='records'),
                analysis=analysis_text
            )
            
            self.db.add(new_report)
            self.db.commit()
            self.db.refresh(new_report)

            return new_report
        finally:
            shutil.rmtree(request_temp_dir)

async def handle_files_upload(db: Session, user_id: int, files: dict[str, UploadFile]):
    service = ReportService(db=db, user_id=user_id)
    return await service.process(files)