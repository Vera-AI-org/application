from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ExtractionJobResponse(BaseModel):
    id: int
    status: str
    document_count: int
    created_at: datetime
    results: dict | None = None
    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ExtractionJobListItem(BaseModel):
    id: int
    templates_names: str
    status: str
    document_count: int
    created_at: datetime
