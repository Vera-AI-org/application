from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

class CreateTemplateRequest(BaseModel):
    user_id: int
    document_id: int
    name: str | None
    created_at: datetime
    updated_at: datetime | None 
    patterns: List[Dict[str, Any]] | None = None