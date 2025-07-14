from pydantic import BaseModel, EmailStr

class UserResponse(BaseModel):
    uid: str
    email: EmailStr

    class Config:
        from_attributes = True