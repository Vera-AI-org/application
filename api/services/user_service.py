from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models import user_model

def get_or_create_user(db: Session, firebase_user: dict):
    uid = firebase_user.get("uid")
    email = firebase_user.get("email")

    if not uid or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="UID and Email not found in Firebase token."
        )

    db_user = db.query(user_model.User).filter(user_model.User.uid == uid).first()

    if db_user:
        return db_user
    else:
        new_user = user_model.User(uid=uid, email=email)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
