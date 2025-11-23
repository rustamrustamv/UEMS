from pydantic import BaseModel, EmailStr, constr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr
    full_name: constr(min_length=2, max_length=255)
    role: str
    department: Optional[str] = None


class UserCreate(UserBase):
    password: constr(min_length=8)
    student_id: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[constr(min_length=2, max_length=255)] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: UUID
    student_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
