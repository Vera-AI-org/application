from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.schemas import user_schema
from api.services.user import user_service
from core.database import get_db
from core.firebase_auth import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("", response_model=user_schema.UserResponse)
def login_or_create_user(
    db: Session = Depends(get_db),
    firebase_user: dict = Depends(get_current_user)
):
    return user_service.get_or_create_user(db=db, firebase_user=firebase_user)
