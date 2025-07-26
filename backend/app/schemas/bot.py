"""
Bot-related Pydantic schemas for API validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class BotBase(BaseModel):
    """Base bot schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: str = Field(..., min_length=1)


class BotCreate(BotBase):
    """Schema for bot creation."""
    llm_provider: str = Field("openai", pattern="^(openai|anthropic|openrouter|gemini)$")
    llm_model: str = Field("gpt-3.5-turbo", max_length=100)
    embedding_provider: Optional[str] = Field("openai", pattern="^(openai|gemini|local)$")
    embedding_model: Optional[str] = Field("text-embedding-3-small", max_length=100)
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(1000, ge=1, le=8000)
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
    is_public: Optional[bool] = False
    allow_collaboration: Optional[bool] = True


class BotUpdate(BaseModel):
    """Schema for bot updates."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: Optional[str] = Field(None, min_length=1)
    llm_provider: Optional[str] = Field(None, pattern="^(openai|anthropic|openrouter|gemini)$")
    llm_model: Optional[str] = Field(None, max_length=100)
    embedding_provider: Optional[str] = Field(None, pattern="^(openai|gemini|local)$")
    embedding_model: Optional[str] = Field(None, max_length=100)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=8000)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    is_public: Optional[bool] = None
    allow_collaboration: Optional[bool] = None


class BotResponse(BotBase):
    """Schema for bot response."""
    id: uuid.UUID
    owner_id: uuid.UUID
    llm_provider: str
    llm_model: str
    embedding_provider: Optional[str]
    embedding_model: Optional[str]
    temperature: float
    max_tokens: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    is_public: bool
    allow_collaboration: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Bot Permission schemas
class BotPermissionBase(BaseModel):
    """Base bot permission schema."""
    role: str = Field(..., pattern="^(owner|admin|editor|viewer)$")


class BotPermissionCreate(BotPermissionBase):
    """Schema for bot permission creation."""
    user_id: uuid.UUID


class BotPermissionUpdate(BaseModel):
    """Schema for bot permission updates."""
    role: str = Field(..., pattern="^(owner|admin|editor|viewer)$")


class BotPermissionResponse(BotPermissionBase):
    """Schema for bot permission response."""
    id: uuid.UUID
    bot_id: uuid.UUID
    user_id: uuid.UUID
    granted_by: Optional[uuid.UUID]
    granted_at: datetime

    model_config = {"from_attributes": True}