"""
Application configuration settings.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/multi_bot_rag"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Vector Store
    vector_store_type: str = "qdrant"  # or 'faiss'
    qdrant_url: str = "http://localhost:6333"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # File Storage
    upload_dir: str = "./uploads"
    max_file_size: int = 10485760  # 10MB
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()