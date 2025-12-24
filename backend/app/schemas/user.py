from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"
    is_active: bool = True


class AdminUserUpdate(BaseModel):
    password: str | None = None
    role: str | None = None
    is_active: bool | None = None

