from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

class CreateTemplateRequest(BaseModel):
    document_id: int
    name: str | None
    pattern_ids: List[int] | None = None