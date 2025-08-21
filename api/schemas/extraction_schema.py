from pydantic import RootModel
from typing import List, Dict, Any

class ExtractionResponse(RootModel[List[Dict[str, Any]]]):
    pass