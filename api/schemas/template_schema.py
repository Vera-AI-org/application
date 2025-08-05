from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any
from .field_schema import Field, FieldCreate

class TemplateBase(BaseModel):
    name: str
    description: str | None = None
    segmentation_strategy: Dict[str, Any]

class UserSelection(BaseModel):
    label: str
    context: str

class TemplateGenerationRequest(BaseModel):
    document_id: int
    name: str
    selections: List[UserSelection]

class TemplateUpdate(TemplateBase):
    name: str | None = None
    description: str | None = None
    segmentation_strategy: Dict[str, Any] | None = None

class TemplateCreate(TemplateBase):
    name: str | None = None
    description: str | None = None
    segmentation_strategy: Dict[str, Any] | None = None
    fields: List[Field] = []

class Template(TemplateBase):
    id: int
    user_id: int
    fields: List[Field] = []

    model_config = ConfigDict(from_attributes=True)