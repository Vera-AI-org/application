from pydantic import BaseModel, EmailStr

class UserResponse(BaseModel):
    id: int
    uid: str
    email: EmailStr

    class Config:
        from_attributes = True