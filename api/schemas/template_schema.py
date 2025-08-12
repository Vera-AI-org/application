from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Dict, Any

class TemplateSchema(BaseModel):
    id: int
    user_id: int
    document_id: int
    name: str | None
    created_at: datetime
    updated_at: datetime | None 
    patterns: List[Dict[str, Any]] | None = None
    model_config = ConfigDict(from_attributes=True)