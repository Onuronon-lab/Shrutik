from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    """Schema for public user registration - always creates CONTRIBUTOR role."""
    password: str
    
    model_config = {"extra": "forbid"}  # Pydantic v2 syntax


class UserCreateAdmin(UserBase):
    """Schema for admin-created users - allows role specification."""
    password: str
    role: UserRole = UserRole.CONTRIBUTOR
    
    model_config = {"extra": "forbid"}  


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    
    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[UserRole] = None