from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Dict, Any

class ReportSchema(BaseModel):
    id: int
    user_id: int
    analysis: str | None
    data: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)