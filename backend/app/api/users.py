"""
User management API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import get_current_active_user, get_user_service
from ..schemas.user import (
    UserResponse, UserUpdate, UserSearch, PasswordChange,
    APIKeyCreate, APIKeyUpdate, APIKeyResponse
)
from ..services.user_service import UserService
from ..services.auth_service import AuthService
from ..models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user profile.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile data
    """
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    updates: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update current user profile.
    
    Args:
        updates: Profile updates
        current_user: Current authenticated user
        user_service: User service
        
    Returns:
        Updated user profile
    """
    updated_user = user_service.update_user_profile(current_user, updates)
    return UserResponse.model_validate(updated_user)


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change user password.
    
    Args:
        password_data: Password change data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    auth_service = AuthService(db)
    success = auth_service.change_password(
        current_user,
        password_data.current_password,
        password_data.new_password
    )
    if success:
        return {"message": "Password changed successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.get("/search", response_model=List[UserSearch])
async def search_users(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Search users for collaboration.
    
    Args:
        q: Search query
        limit: Maximum number of results
        current_user: Current authenticated user
        user_service: User service
        
    Returns:
        List of matching users
    """
    return user_service.search_users(q, limit)


# API Key Management Endpoints

@router.get("/api-keys", response_model=List[APIKeyResponse])
async def get_api_keys(
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get all API keys for current user.
    
    Args:
        current_user: Current authenticated user
        user_service: User service
        
    Returns:
        List of user's API keys (without actual key values)
    """
    return user_service.get_user_api_keys(current_user)


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def add_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Add or update API key for a provider.
    
    Args:
        api_key_data: API key data
        current_user: Current authenticated user
        user_service: User service
        
    Returns:
        Created/updated API key info
    """
    return user_service.add_api_key(current_user, api_key_data)


@router.put("/api-keys/{provider}", response_model=APIKeyResponse)
async def update_api_key(
    provider: str,
    api_key_data: APIKeyUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update API key for a specific provider.
    
    Args:
        provider: Provider name (openai, anthropic, openrouter, gemini)
        api_key_data: Updated API key data
        current_user: Current authenticated user
        user_service: User service
        
    Returns:
        Updated API key info
    """
    return user_service.update_api_key(current_user, provider, api_key_data)


@router.delete("/api-keys/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    provider: str,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Delete API key for a specific provider.
    
    Args:
        provider: Provider name (openai, anthropic, openrouter, gemini)
        current_user: Current authenticated user
        user_service: User service
    """
    user_service.delete_api_key(current_user, provider)
    return None