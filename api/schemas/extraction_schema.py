from pydantic import BaseModel
from typing import List, Dict, Any

class ExtractionResponse(BaseModel):
    extractions: List[Dict[str, str]]
