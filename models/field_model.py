from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, func, DateTime
from sqlalchemy.orm import relationship
from core.database import Base

class Field(Base):
    __tablename__ = "field"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("template.id"), nullable=False)
    
    label = Column(String, nullable=False)
    
    extraction_pattern = Column(String, nullable=False)
    
    field_type = Column(String, default="string") 
    
    is_required = Column(Boolean, default=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    template = relationship("Template", back_populates="fields")