from pydantic import BaseModel, ConfigDict
from datetime import datetime

class DocumentSchema(BaseModel):
    id: int
    user_id: int
    file_name: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)