from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Dict, Any

class DocumentSchema(BaseModel):
    id: int
    user_id: int
    document_md: str 
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)