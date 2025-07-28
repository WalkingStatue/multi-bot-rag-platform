"""
Conversation and session management API endpoints.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.user import User
from ..schemas.conversation import (
    ConversationSessionCreate,
    ConversationSessionResponse,
    MessageCreate,
    MessageResponse,
    ChatRequest,
    ChatResponse
)
from ..services.conversation_service import ConversationService
from ..services.chat_service import ChatService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/sessions", response_model=ConversationSessionResponse)
async def create_session(
    session_data: ConversationSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation session."""
    try:
        conversation_service = ConversationService(db)
        session = conversation_service.create_session(current_user.id, session_data)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation session"
        )


@router.get("/sessions", response_model=List[ConversationSessionResponse])
async def list_sessions(
    bot_id: Optional[uuid.UUID] = Query(None, description="Filter by bot ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List conversation sessions for the current user."""
    conversation_service = ConversationService(db)
    sessions = conversation_service.list_user_sessions(
        current_user.id, bot_id, limit, offset
    )
    return sessions


@router.get("/sessions/{session_id}", response_model=ConversationSessionResponse)
async def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific conversation session."""
    conversation_service = ConversationService(db)
    session = conversation_service.get_session(session_id, current_user.id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied"
        )
    
    return session


@router.put("/sessions/{session_id}", response_model=ConversationSessionResponse)
async def update_session(
    session_id: uuid.UUID,
    title: Optional[str] = None,
    is_shared: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a conversation session."""
    try:
        conversation_service = ConversationService(db)
        session = conversation_service.update_session(
            session_id, current_user.id, title, is_shared
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation session."""
    try:
        conversation_service = ConversationService(db)
        success = conversation_service.delete_session(session_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        return {"message": "Session deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post("/messages", response_model=MessageResponse)
async def add_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a message to a conversation session."""
    try:
        conversation_service = ConversationService(db)
        message = conversation_service.add_message(current_user.id, message_data)
        return message
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages from a conversation session."""
    conversation_service = ConversationService(db)
    messages = conversation_service.get_session_messages(
        session_id, current_user.id, limit, offset
    )
    return messages


@router.get("/search")
async def search_conversations(
    q: str = Query(..., min_length=1, description="Search query"),
    bot_id: Optional[uuid.UUID] = Query(None, description="Filter by bot ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search conversations across user's accessible bots."""
    conversation_service = ConversationService(db)
    results = conversation_service.search_conversations(
        current_user.id, q, bot_id, limit, offset
    )
    return {
        "query": q,
        "results": results,
        "total": len(results)
    }


@router.get("/export")
async def export_conversations(
    bot_id: Optional[uuid.UUID] = Query(None, description="Filter by bot ID"),
    session_id: Optional[uuid.UUID] = Query(None, description="Export specific session"),
    format_type: str = Query("json", description="Export format"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export conversations for backup and analysis."""
    conversation_service = ConversationService(db)
    export_data = conversation_service.export_conversations(
        current_user.id, bot_id, session_id, format_type
    )
    return export_data


@router.get("/analytics")
async def get_conversation_analytics(
    bot_id: Optional[uuid.UUID] = Query(None, description="Filter by bot ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation analytics for user's accessible bots."""
    conversation_service = ConversationService(db)
    analytics = conversation_service.get_conversation_analytics(
        current_user.id, bot_id
    )
    return analytics


@router.post("/bots/{bot_id}/chat", response_model=ChatResponse)
async def chat_with_bot(
    bot_id: uuid.UUID,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to a bot and get a response through the RAG pipeline."""
    try:
        chat_service = ChatService(db)
        response = await chat_service.process_message(
            bot_id=bot_id,
            user_id=current_user.id,
            chat_request=chat_request
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat message: {str(e)}"
        )


@router.post("/bots/{bot_id}/sessions", response_model=ConversationSessionResponse)
async def create_bot_session(
    bot_id: uuid.UUID,
    title: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation session for a specific bot."""
    try:
        chat_service = ChatService(db)
        session = await chat_service.create_session(
            bot_id=bot_id,
            user_id=current_user.id,
            title=title
        )
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )