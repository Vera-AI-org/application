from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Dict, Any

class PatternSchema(BaseModel):
    id: int
    user_id: int
    document_id: int 
    name: str
    pattern: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PatternDeleteResponse(BaseModel):
    message: str