from fastapi import APIRouter, Depends
from api.schemas import user_schema
from core.firebase_auth import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("", response_model= user_schema.UserResponse)
def login_or_create_user(
    current_user: user_schema.UserResponse = Depends(get_current_user)
):
    return current_user
