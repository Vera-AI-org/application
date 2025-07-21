from sqlalchemy import Column, String
from core.database import Base # Import Base from the new core directory

class User(Base):
    __tablename__ = "users"

    uid = Column(String, primary_key=True, index=True)  # Firebase UID
    email = Column(String, unique=True, index=True)