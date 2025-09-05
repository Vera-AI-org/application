from pydantic import BaseModel
from typing import List, Dict, Any

class CreatePatternRequest(BaseModel):
    templateId: int
    name: str
    description: str
    isSection: bool