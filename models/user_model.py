from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)

    reports = relationship("Report", back_populates="user")
    documents = relationship("Document", back_populates="user")
    patterns = relationship("Pattern", back_populates="user")