"""
Document-related Pydantic schemas for API validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class DocumentBase(BaseModel):
    """Base document schema."""
    filename: str = Field(..., max_length=255)


class DocumentUpload(BaseModel):
    """Schema for document upload."""
    bot_id: uuid.UUID


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    id: uuid.UUID
    bot_id: uuid.UUID
    uploaded_by: Optional[uuid.UUID]
    file_path: str
    file_size: Optional[int]
    mime_type: Optional[str]
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentChunkResponse(BaseModel):
    """Schema for document chunk response."""
    id: uuid.UUID
    document_id: uuid.UUID
    bot_id: uuid.UUID
    chunk_index: int
    content: str
    embedding_id: Optional[str]
    chunk_metadata: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}