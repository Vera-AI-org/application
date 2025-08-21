from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, func, BOOLEAN
from sqlalchemy.orm import relationship
from core.database import Base
from models.template_model import template_pattern_association


class Pattern(Base):
    __tablename__ = "pattern"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("document.id"), nullable=False)
    
    name = Column(String, nullable=True)
    pattern = Column(String, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    is_section = Column(BOOLEAN, nullable=False, default=False)

    user = relationship("User", back_populates="patterns")

    templates = relationship(
        "Template",
        secondary=template_pattern_association,
        back_populates="patterns"
    )