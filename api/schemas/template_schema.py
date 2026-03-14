from pydantic import BaseModel, ConfigDict


class FieldBase(BaseModel):
    name: str
    description: str
    is_key: bool = False


class FieldCreate(FieldBase):
    pass


class FieldResponse(FieldBase):
    id: int
    template_id: int

    model_config = ConfigDict(from_attributes=True)


class TemplateBase(BaseModel):
    name: str
    description: str | None = None


class TemplateCreate(TemplateBase):
    pass


class TemplateResponse(TemplateBase):
    id: int
    fields: list[FieldResponse] = []

    model_config = ConfigDict(from_attributes=True)