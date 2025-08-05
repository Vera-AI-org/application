from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any
from datetime import datetime

class ExtractionRequest(BaseModel):
    document_id: int
    template_id: int

class ExtractionResultSchema(BaseModel):
    id: int
    document_id: int
    template_id: int
    created_at: datetime
    data: List[Dict[str, Any]]
    errors: List[str] | None = []

    model_config = ConfigDict(from_attributes=True)