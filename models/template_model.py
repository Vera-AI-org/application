from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import relationship
from core.database import Base

class Template(Base):
    __tablename__ = "template"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("document.id"), nullable=False)

    name = Column(String, nullable=True)
    pattern = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    patterns = relationship("Pattern", back_populates="templates")
    user = relationship("User", back_populates="templates")
    document = relationship("Document", back_populates="templates")
