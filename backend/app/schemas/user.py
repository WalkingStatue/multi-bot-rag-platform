"""
User-related Pydantic schemas for API validation.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for user updates."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: uuid.UUID
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token data."""
    username: Optional[str] = None


class RefreshToken(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class UserSearch(BaseModel):
    """Schema for user search results."""
    id: uuid.UUID
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


# API Key schemas
class APIKeyBase(BaseModel):
    """Base API key schema."""
    provider: str = Field(..., pattern="^(openai|anthropic|openrouter|gemini)$")


class APIKeyCreate(APIKeyBase):
    """Schema for API key creation."""
    api_key: str = Field(..., min_length=10)


class APIKeyUpdate(BaseModel):
    """Schema for API key updates."""
    api_key: str = Field(..., min_length=10)
    is_active: Optional[bool] = True


class APIKeyResponse(APIKeyBase):
    """Schema for API key response."""
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Note: We don't return the actual API key for security

    model_config = {"from_attributes": True}