"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import auth, users, bots, permissions, documents, conversations, websocket, analytics, ocr, embedding_validation, embedding_models

app = FastAPI(
    title="Multi-Bot RAG Platform",
    description="A comprehensive multi-bot assistant platform with RAG capabilities",
    version="1.0.0",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(bots.router, prefix="/api")
app.include_router(permissions.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(websocket.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(ocr.router, prefix="/api")
app.include_router(embedding_validation.router)
app.include_router(embedding_models.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Multi-Bot RAG Platform API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}