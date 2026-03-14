from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base


class ExtractionJob(Base):
    __tablename__ = "extraction_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="pending")  # pending | processing | done | failed
    # list of {filename: str, template_id: int} — one entry per uploaded file
    document_templates = Column(JSON, nullable=False, default=list)
    results = Column(JSON, nullable=True)        # {key_value: {field: value, ...}}
    error_message = Column(String, nullable=True)
    document_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="jobs")
