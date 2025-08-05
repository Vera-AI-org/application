from sqlalchemy import Column, Integer, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from core.database import Base

class Extraction(Base):
    __tablename__ = "extraction"

    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("document.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("template.id"), nullable=False)
    
    data = Column(JSON, nullable=False)
    
    errors = Column(JSON, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
   
    user = relationship("User")
    document = relationship("Document")
    template = relationship("Template")