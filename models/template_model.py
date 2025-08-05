from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from core.database import Base

class Template(Base):
    __tablename__ = "template"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    
    segmentation_strategy = Column(JSON, nullable=False)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    user = relationship("User", back_populates="templates")
    fields = relationship("Field", back_populates="template", cascade="all, delete-orphan")