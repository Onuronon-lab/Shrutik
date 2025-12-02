import re
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from app.models.user import UserRole


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    """Schema for public user registration - always creates CONTRIBUTOR role."""

    password: str

    @field_validator("password")
    def password_strength(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[\W_]", value):
            raise ValueError("Password must contain at least one special character")
        return value

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
    role: UserRole

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[UserRole] = None
