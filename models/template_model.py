from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, func, Table
from sqlalchemy.orm import relationship
from core.database import Base

template_pattern_association = Table('template_pattern_association', Base.metadata,
    Column('template_id', Integer, ForeignKey('template.id', ondelete="CASCADE"), primary_key=True),
    Column('pattern_id', Integer, ForeignKey('pattern.id', ondelete="CASCADE"), primary_key=True)
)

class Template(Base):
    __tablename__ = "template"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    name = Column(String, nullable=True)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    patterns = relationship(
        "Pattern",
        secondary=template_pattern_association,
        back_populates="templates"
    )
    
    user = relationship("User", back_populates="templates")
    patterns = relationship("Pattern", back_populates="template", cascade="all, delete-orphan")
