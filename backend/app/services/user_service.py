"""
User management service for profile operations and collaboration features.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, and_
from fastapi import HTTPException, status

from ..models.user import User, UserAPIKey
from ..schemas.user import UserUpdate, UserSearch, APIKeyCreate, APIKeyUpdate, APIKeyResponse
from ..utils.encryption import encrypt_api_key, decrypt_api_key


class UserService:
    """Service class for user management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_profile(self, user_id: str) -> User:
        """
        Get user profile by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object
            
        Raises:
            HTTPException: If user not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    
    def update_user_profile(self, user: User, updates: UserUpdate) -> User:
        """
        Update user profile.
        
        Args:
            user: Current user object
            updates: Profile updates
            
        Returns:
            Updated user object
            
        Raises:
            HTTPException: If username/email already exists
        """
        # Check for username/email conflicts
        if updates.username and updates.username != user.username:
            existing_user = self.db.query(User).filter(
                and_(User.username == updates.username, User.id != user.id)
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        if updates.email and updates.email != user.email:
            existing_user = self.db.query(User).filter(
                and_(User.email == updates.email, User.id != user.id)
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Update fields
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update profile"
            )
    
    def search_users(self, query: str, limit: int = 20) -> List[UserSearch]:
        """
        Search users by username or full name for collaboration.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of user search results
        """
        if not query or len(query.strip()) < 2:
            return []
        
        search_term = f"%{query.strip()}%"
        users = self.db.query(User).filter(
            and_(
                User.is_active == True,
                or_(
                    User.username.ilike(search_term),
                    User.full_name.ilike(search_term)
                )
            )
        ).limit(limit).all()
        
        return [
            UserSearch(
                id=user.id,
                username=user.username,
                full_name=user.full_name,
                avatar_url=user.avatar_url
            )
            for user in users
        ]
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: Email to search for
            
        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(User.email == email).first()
    
    # API Key Management Methods
    
    def add_api_key(self, user: User, api_key_data: APIKeyCreate) -> APIKeyResponse:
        """
        Add or update API key for a provider.
        
        Args:
            user: User object
            api_key_data: API key data
            
        Returns:
            API key response object
            
        Raises:
            HTTPException: If encryption fails
        """
        try:
            # Encrypt the API key
            encrypted_key = encrypt_api_key(api_key_data.api_key)
            
            # Check if API key already exists for this provider
            existing_key = self.db.query(UserAPIKey).filter(
                and_(
                    UserAPIKey.user_id == user.id,
                    UserAPIKey.provider == api_key_data.provider
                )
            ).first()
            
            if existing_key:
                # Update existing key
                existing_key.api_key_encrypted = encrypted_key
                existing_key.is_active = True
                self.db.commit()
                self.db.refresh(existing_key)
                return APIKeyResponse.model_validate(existing_key)
            else:
                # Create new key
                db_api_key = UserAPIKey(
                    user_id=user.id,
                    provider=api_key_data.provider,
                    api_key_encrypted=encrypted_key,
                    is_active=True
                )
                self.db.add(db_api_key)
                self.db.commit()
                self.db.refresh(db_api_key)
                return APIKeyResponse.model_validate(db_api_key)
                
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save API key"
            )
    
    def get_user_api_keys(self, user: User) -> List[APIKeyResponse]:
        """
        Get all API keys for a user.
        
        Args:
            user: User object
            
        Returns:
            List of API key response objects
        """
        api_keys = self.db.query(UserAPIKey).filter(
            UserAPIKey.user_id == user.id
        ).all()
        
        return [APIKeyResponse.model_validate(key) for key in api_keys]
    
    def get_api_key(self, user: User, provider: str) -> Optional[str]:
        """
        Get decrypted API key for a provider.
        
        Args:
            user: User object
            provider: Provider name
            
        Returns:
            Decrypted API key or None if not found
        """
        api_key = self.db.query(UserAPIKey).filter(
            and_(
                UserAPIKey.user_id == user.id,
                UserAPIKey.provider == provider,
                UserAPIKey.is_active == True
            )
        ).first()
        
        if not api_key:
            return None
        
        try:
            return decrypt_api_key(api_key.api_key_encrypted)
        except Exception:
            return None
    
    def update_api_key(self, user: User, provider: str, api_key_data: APIKeyUpdate) -> APIKeyResponse:
        """
        Update API key for a provider.
        
        Args:
            user: User object
            provider: Provider name
            api_key_data: Updated API key data
            
        Returns:
            Updated API key response object
            
        Raises:
            HTTPException: If API key not found or update fails
        """
        api_key = self.db.query(UserAPIKey).filter(
            and_(
                UserAPIKey.user_id == user.id,
                UserAPIKey.provider == provider
            )
        ).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found for this provider"
            )
        
        try:
            # Encrypt new API key
            encrypted_key = encrypt_api_key(api_key_data.api_key)
            
            # Update fields
            api_key.api_key_encrypted = encrypted_key
            if api_key_data.is_active is not None:
                api_key.is_active = api_key_data.is_active
            
            self.db.commit()
            self.db.refresh(api_key)
            return APIKeyResponse.model_validate(api_key)
            
        except Exception:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update API key"
            )
    
    def delete_api_key(self, user: User, provider: str) -> bool:
        """
        Delete API key for a provider.
        
        Args:
            user: User object
            provider: Provider name
            
        Returns:
            True if deleted successfully
            
        Raises:
            HTTPException: If API key not found
        """
        api_key = self.db.query(UserAPIKey).filter(
            and_(
                UserAPIKey.user_id == user.id,
                UserAPIKey.provider == provider
            )
        ).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found for this provider"
            )
        
        try:
            self.db.delete(api_key)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete API key"
            )