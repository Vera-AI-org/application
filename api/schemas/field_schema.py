from pydantic import BaseModel, ConfigDict

class FieldBase(BaseModel):
    label: str
    extraction_pattern: str
    field_type: str = "string"
    is_required: bool = True

class FieldCreate(FieldBase):
    pass

class Field(FieldBase):
    id: int
    template_id: int
    
    model_config = ConfigDict(from_attributes=True)