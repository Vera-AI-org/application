from pydantic import BaseModel
from typing import List, Dict, Any

class RegexGenerationRequest(BaseModel):
    documentId: int
    selections: List[Dict[str, Any]]
    is_section: bool = False