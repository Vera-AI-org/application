from pydantic import BaseModel
from typing import List, Dict, Any

class RegexGenerationRequest(BaseModel):
    documentId: int
    key: str
    selections: List[str]
    isSection: bool = False