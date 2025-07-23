from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models import user_model

class UserService:
    def __init__(self, db: Session):
        
        self.db = db

    def get_or_create(self, firebase_user: dict) -> user_model.User:
        
        firebase_uid = firebase_user.get("uid")
        email = firebase_user.get("email")

        if not firebase_uid or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="UID e Email não encontrados no token do Firebase."
            )

        db_user = self.db.query(user_model.User).filter(user_model.User.uid == firebase_uid).first()

        if db_user:
            return db_user
        
        new_user = user_model.User(uid=firebase_uid, email=email)
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        return new_user

def get_or_create_user(db: Session, firebase_user: dict) -> user_model.User:
    service = UserService(db)
    return service.get_or_create(firebase_user)