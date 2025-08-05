"""
Bot management API endpoints.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from ..core.database import get_db
from ..core.dependencies import get_current_active_user
from ..core.permissions import (
    get_bot_service, 
    get_permission_service,
    require_bot_view,
    require_bot_edit,
    require_owner_role
)
from ..models.user import User
from ..schemas.bot import (
    BotCreate, BotUpdate, BotResponse, BotTransferRequest,
    EmbeddingValidationRequest, EmbeddingValidationResponse,
    MigrationEstimateRequest, MigrationEstimateResponse,
    MigrationStartRequest, MigrationProgressResponse,
    MigrationStatusResponse, DimensionInfoResponse,
    ActiveMigrationsResponse, MigrationActionResponse
)
from ..services.bot_service import BotService
from ..services.permission_service import PermissionService
from ..services.embedding_compatibility_manager import EmbeddingCompatibilityManager

router = APIRouter(prefix="/bots", tags=["bots"])


@router.post("/", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_config: BotCreate,
    current_user: User = Depends(get_current_active_user),
    bot_service: BotService = Depends(get_bot_service)
):
    """
    Create a new bot.
    
    The user creating the bot automatically becomes the owner.
    """
    bot = bot_service.create_bot(current_user.id, bot_config)
    return BotResponse.model_validate(bot)


@router.get("/", response_model=List[Dict[str, Any]])
async def list_user_bots(
    current_user: User = Depends(get_current_active_user),
    bot_service: BotService = Depends(get_bot_service)
):
    """
    List all bots accessible to the current user.
    
    Returns bots with the user's role for each bot.
    """
    accessible_bots = bot_service.list_user_bots(current_user.id)
    
    # Convert to serializable format
    result = []
    for bot_info in accessible_bots:
        bot_data = BotResponse.model_validate(bot_info["bot"])
        result.append({
            "bot": bot_data.model_dump(),
            "role": bot_info["role"],
            "granted_at": bot_info["granted_at"].isoformat() if bot_info["granted_at"] else None
        })
    
    return result


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    bot_service: BotService = Depends(get_bot_service),
    _: bool = Depends(require_bot_view)
):
    """
    Get bot details.
    
    Requires viewer role or higher.
    """
    bot = bot_service.get_bot(bot_id, current_user.id)
    return BotResponse.model_validate(bot)


@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: uuid.UUID,
    updates: BotUpdate,
    current_user: User = Depends(get_current_active_user),
    bot_service: BotService = Depends(get_bot_service),
    _: bool = Depends(require_bot_edit)
):
    """
    Update bot configuration.
    
    Requires admin role or higher.
    """
    bot = bot_service.update_bot(bot_id, current_user.id, updates)
    return BotResponse.model_validate(bot)


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
    bot_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    bot_service: BotService = Depends(get_bot_service),
    _: bool = Depends(require_owner_role)
):
    """
    Delete a bot.
    
    Only the owner can delete a bot. This will cascade delete all
    associated data including conversations, documents, and permissions.
    """
    bot_service.delete_bot(bot_id, current_user.id)


@router.post("/{bot_id}/transfer", status_code=status.HTTP_200_OK)
async def transfer_ownership(
    bot_id: uuid.UUID,
    request: BotTransferRequest,
    current_user: User = Depends(get_current_active_user),
    bot_service: BotService = Depends(get_bot_service),
    _: bool = Depends(require_owner_role)
):
    """
    Transfer bot ownership to another user.
    
    Only the current owner can transfer ownership.
    """
    success = bot_service.transfer_ownership(bot_id, current_user.id, request.new_owner_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to transfer ownership"
        )
    
    return {"message": "Ownership transferred successfully"}


@router.get("/{bot_id}/analytics", response_model=Dict[str, Any])
async def get_bot_analytics(
    bot_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    bot_service: BotService = Depends(get_bot_service),
    _: bool = Depends(require_bot_view)
):
    """
    Get bot analytics and usage statistics.
    
    Requires viewer role or higher.
    """
    return bot_service.get_bot_analytics(bot_id, current_user.id)


@router.get("/models/available", response_model=Dict[str, List[str]])
async def get_available_models(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available models for all supported providers.
    
    Returns a dictionary mapping provider names to their available models.
    """
    from ..services.llm_service import LLMProviderService
    
    llm_service = LLMProviderService()
    try:
        return llm_service.get_all_available_models()
    finally:
        await llm_service.close()


@router.get("/models/{provider}", response_model=List[str])
async def get_provider_models(
    provider: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available models for a specific provider.
    
    Args:
        provider: Provider name (openai, anthropic, openrouter, gemini)
    """
    from ..services.llm_service import LLMProviderService
    
    llm_service = LLMProviderService()
    try:
        return llm_service.get_available_models(provider)
    finally:
        await llm_service.close()


@router.get("/providers", response_model=List[str])
async def get_supported_providers(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of supported LLM providers.
    """
    from ..services.llm_service import LLMProviderService
    
    llm_service = LLMProviderService()
    try:
        return llm_service.get_supported_providers()
    finally:
        await llm_service.close()


@router.get("/embeddings/available", response_model=Dict[str, List[str]])
async def get_available_embedding_models(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available embedding models for all supported providers.
    
    Returns a dictionary mapping provider names to their available embedding models.
    """
    from ..services.embedding_service import EmbeddingProviderService
    
    embedding_service = EmbeddingProviderService()
    try:
        return embedding_service.get_all_available_models()
    finally:
        await embedding_service.close()


@router.get("/embeddings/providers", response_model=List[str])
async def get_supported_embedding_providers(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of supported embedding providers.
    """
    from ..services.embedding_service import EmbeddingProviderService
    
    embedding_service = EmbeddingProviderService()
    try:
        return embedding_service.get_supported_providers()
    finally:
        await embedding_service.close()


@router.get("/embeddings/{provider}", response_model=List[str])
async def get_provider_embedding_models(
    provider: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available embedding models for a specific provider.
    
    Args:
        provider: Provider name (openai, gemini, anthropic)
    """
    from ..services.embedding_service import EmbeddingProviderService
    
    embedding_service = EmbeddingProviderService()
    try:
        return embedding_service.get_available_models(provider)
    finally:
        await embedding_service.close()

# Embedding Migration Endpoints

@router.post("/{bot_id}/embeddings/validate-change", response_model=EmbeddingValidationResponse)
async def validate_embedding_change(
    bot_id: uuid.UUID,
    request: EmbeddingValidationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    _: bool = Depends(require_bot_edit)
):
    """
    Validate embedding provider/model change for a bot.
    
    Requires admin role or higher.
    """
    compatibility_manager = EmbeddingCompatibilityManager(db)
    try:
        result = await compatibility_manager.validate_provider_change(
            bot_id, request.provider, request.model
        )
        
        return EmbeddingValidationResponse(
            compatible=result.compatible,
            issues=result.issues or [],
            recommendations=result.recommendations or [],
            migration_required=result.migration_required,
            current_config=result.current_config,
            target_config=result.target_config
        )
    finally:
        await compatibility_manager.close()


@router.post("/{bot_id}/embeddings/estimate-migration", response_model=MigrationEstimateResponse)
async def estimate_migration_time(
    bot_id: uuid.UUID,
    request: MigrationEstimateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    _: bool = Depends(require_bot_edit)
):
    """
    Estimate migration time for embedding provider change.
    
    Requires admin role or higher.
    """
    compatibility_manager = EmbeddingCompatibilityManager(db)
    try:
        result = await compatibility_manager.estimate_migration_time(bot_id, request.batch_size)
        return MigrationEstimateResponse(**result)
    finally:
        await compatibility_manager.close()


@router.post("/{bot_id}/embeddings/start-migration", response_model=Dict[str, Any])
async def start_embedding_migration(
    bot_id: uuid.UUID,
    request: MigrationStartRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    _: bool = Depends(require_bot_edit)
):
    """
    Start embedding migration for a bot.
    
    Requires admin role or higher.
    """
    compatibility_manager = EmbeddingCompatibilityManager(db)
    try:
        # Validate first
        validation_result = await compatibility_manager.validate_provider_change(
            bot_id, request.provider, request.model
        )
        if not validation_result.compatible:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Configuration not compatible for migration",
                    "issues": validation_result.issues,
                    "recommendations": validation_result.recommendations
                }
            )
        
        # Start migration
        migration_id, progress = await compatibility_manager.start_migration_with_progress(
            bot_id, request.provider, request.model, request.batch_size
        )
        
        return {
            "migration_id": migration_id,
            "message": "Migration started successfully",
            "progress": progress
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start migration: {str(e)}"
        )
    finally:
        await compatibility_manager.close()


@router.get("/{bot_id}/embeddings/migration-status", response_model=Dict[str, Any])
async def get_migration_status(
    bot_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    _: bool = Depends(require_bot_view)
):
    """
    Get current migration status for a bot.
    
    Requires viewer role or higher.
    
    Args:
        bot_id: Bot identifier
    """
    compatibility_manager = EmbeddingCompatibilityManager(db)
    try:
        status_info = await compatibility_manager.get_migration_status(bot_id)
        
        if not status_info:
            return {"status": "no_active_migration"}
        
        return status_info
        
    finally:
        await compatibility_manager.close()


@router.get("/embeddings/migration/{migration_id}/progress", response_model=Dict[str, Any])
async def get_migration_progress(
    migration_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed migration progress by migration ID.
    
    Args:
        migration_id: Migration identifier
    """
    compatibility_manager = EmbeddingCompatibilityManager(db)
    try:
        progress = await compatibility_manager.get_migration_progress_detailed(migration_id)
        
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Migration not found"
            )
        
        return progress
        
    finally:
        await compatibility_manager.close()


@router.post("/{bot_id}/embeddings/cancel-migration", response_model=Dict[str, Any])
async def cancel_migration(
    bot_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    _: bool = Depends(require_bot_edit)
):
    """
    Cancel active migration for a bot.
    
    Requires admin role or higher.
    
    Args:
        bot_id: Bot identifier
    """
    compatibility_manager = EmbeddingCompatibilityManager(db)
    try:
        success = await compatibility_manager.cancel_migration(bot_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active migration found for this bot"
            )
        
        return {"message": "Migration cancelled successfully"}
        
    finally:
        await compatibility_manager.close()


@router.post("/embeddings/migration/{migration_id}/rollback", response_model=Dict[str, Any])
async def rollback_migration(
    migration_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger rollback for a migration.
    
    Args:
        migration_id: Migration identifier
    """
    compatibility_manager = EmbeddingCompatibilityManager(db)
    try:
        success = await compatibility_manager.rollback_migration(migration_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rollback failed or migration not found"
            )
        
        return {"message": "Migration rolled back successfully"}
        
    finally:
        await compatibility_manager.close()


@router.get("/embeddings/migrations/active", response_model=Dict[str, Any])
async def get_all_active_migrations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all active migrations (admin only).
    
    This endpoint is useful for monitoring system-wide migration status.
    """
    # Check if user is admin (you might want to add a proper admin check)
    compatibility_manager = EmbeddingCompatibilityManager(db)
    try:
        migrations = await compatibility_manager.get_all_migration_statuses()
        
        return {
            "active_migrations": migrations,
            "total_count": len(migrations)
        }
        
    finally:
        await compatibility_manager.close()


@router.get("/{bot_id}/embeddings/dimension-info", response_model=Dict[str, Any])
async def get_embedding_dimension_info(
    bot_id: uuid.UUID,
    provider: str,
    model: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    _: bool = Depends(require_bot_view)
):
    """
    Get embedding dimension information for a provider/model combination.
    
    Requires viewer role or higher.
    
    Args:
        bot_id: Bot identifier
        provider: Embedding provider
        model: Embedding model
    """
    compatibility_manager = EmbeddingCompatibilityManager(db)
    try:
        dimension_info = await compatibility_manager.get_dimension_info(provider, model)
        
        return {
            "provider": dimension_info.provider,
            "model": dimension_info.model,
            "dimension": dimension_info.dimension,
            "compatible_providers": dimension_info.compatible_providers or [],
            "migration_required": dimension_info.migration_required
        }
        
    finally:
        await compatibility_manager.close()