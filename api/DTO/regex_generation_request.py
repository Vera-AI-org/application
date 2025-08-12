from pydantic import BaseModel
from typing import List, Dict, Any

class RegexGenerationRequest(BaseModel):
    documentId: int
    key: str
    selections: List[Dict[str, str]]
    isSection: bool = False