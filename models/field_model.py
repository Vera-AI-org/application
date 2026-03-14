from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class Field(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)           # e.g., "CPF", "Nome", "Salário"
    description = Column(String, nullable=False)    # LLM prompt description
    is_key = Column(Boolean, default=False)         # is this the unique merge key?
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)

    template = relationship("Template", back_populates="fields")
