"""
Pydantic Schemas for Phase 18: Authentication.
Never stores plaintext passwords or exposes password hashes in API responses.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """
    User registration payload.
    """
    email: EmailStr = Field(..., description="Unique email address for user login")
    password: str = Field(..., min_length=6, description="User password (min 6 characters)")
    full_name: Optional[str] = Field(None, max_length=255, description="Optional user full name")


class UserLoginRequest(BaseModel):
    """
    User login payload.
    """
    email: EmailStr = Field(..., description="User registered email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """
    User profile output schema.
    Strictly excludes password and password hash fields.
    """
    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """
    JWT Access Token and authenticated user profile.
    """
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
