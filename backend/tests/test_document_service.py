"""
Unit tests for document service.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil
from uuid import uuid4, UUID
from datetime import datetime

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.services.document_service import DocumentService
from app.models.document import Document, DocumentChunk
from app.models.bot import Bot
from app.models.user import User
from app.services.permission_service import PermissionService
from app.services.embedding_service import EmbeddingProviderService
from app.services.vector_store import VectorService


class MockUploadFile:
    """Mock UploadFile for testing."""
    
    def __init__(self, filename: str, content: bytes, content_type: str = "text/plain"):
        self.filename = filename
        self.content = content
        self.content_type = content_type
    
    async def read(self) -> bytes:
        return self.content


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def mock_permission_service():
    """Mock permission service."""
    service = Mock(spec=PermissionService)
    service.check_bot_permission = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service."""
    service = Mock(spec=EmbeddingProviderService)
    service.generate_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    return service


@pytest.fixture
def mock_vector_service():
    """Mock vector service."""
    service = Mock(spec=VectorService)
    service.store_document_chunks = AsyncMock(return_value=["chunk-1", "chunk-2"])
    service.delete_document_chunks = AsyncMock(return_value=True)
    service.search_relevant_chunks = AsyncMock(return_value=[])
    service.get_bot_collection_stats = AsyncMock(return_value={"vectors_count": 10})
    return service


@pytest.fixture
def temp_upload_dir():
    """Create temporary upload directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def document_service(mock_db, mock_permission_service, mock_embedding_service, mock_vector_service, temp_upload_dir):
    """Create document service with mocked dependencies."""
    service = DocumentService(
        db=mock_db,
        permission_service=mock_permission_service,
        embedding_service=mock_embedding_service,
        vector_service=mock_vector_service
    )
    service.upload_dir = temp_upload_dir
    return service


@pytest.fixture
def sample_bot():
    """Sample bot for testing."""
    return Bot(
        id=uuid4(),
        name="Test Bot",
        system_prompt="Test prompt",
        owner_id=uuid4(),
        embedding_provider="openai",
        embedding_model="text-embedding-3-small"
    )


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    return User(
        id=uuid4(),
        username="testuser",
        email="test@example.com"
    )


@pytest.fixture
def sample_document(sample_bot, sample_user):
    """Sample document for testing."""
    return Document(
        id=uuid4(),
        bot_id=sample_bot.id,
        uploaded_by=sample_user.id,
        filename="test.txt",
        file_path="/path/to/test.txt",
        file_size=100,
        mime_type="text/plain",
        chunk_count=0,
        created_at=datetime.utcnow()
    )


class TestDocumentService:
    """Test cases for DocumentService."""
    
    @pytest.mark.asyncio
    async def test_upload_document_success(self, document_service, sample_bot, sample_user, mock_db):
        """Test successful document upload."""
        # Setup
        file_content = b"This is a test document content."
        upload_file = MockUploadFile("test.txt", file_content)
        
        mock_db.query.return_value.filter.return_value.first.return_value = sample_bot
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Mock the process_document method to avoid actual processing
        with patch.object(document_service, 'process_document', new_callable=AsyncMock) as mock_process:
            # Execute
            result = await document_service.upload_document(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                file=upload_file,
                process_immediately=True
            )
            
            # Verify
            assert isinstance(result, Document)
            assert result.filename == "test.txt"
            assert result.bot_id == sample_bot.id
            assert result.uploaded_by == sample_user.id
            assert result.file_size == len(file_content)
            
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_process.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_document_permission_denied(self, document_service, sample_bot, sample_user, mock_permission_service):
        """Test document upload with insufficient permissions."""
        # Setup
        mock_permission_service.check_bot_permission.return_value = False
        upload_file = MockUploadFile("test.txt", b"content")
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await document_service.upload_document(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                file=upload_file
            )
        
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_upload_document_bot_not_found(self, document_service, sample_user, mock_db):
        """Test document upload when bot doesn't exist."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        upload_file = MockUploadFile("test.txt", b"content")
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await document_service.upload_document(
                bot_id=uuid4(),
                user_id=sample_user.id,
                file=upload_file
            )
        
        assert exc_info.value.status_code == 404
        assert "Bot not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_process_document_success(self, document_service, sample_document, sample_bot, sample_user, mock_db, temp_upload_dir):
        """Test successful document processing."""
        # Setup
        test_content = b"This is a test document for processing. It has multiple sentences."
        test_file = temp_upload_dir / "test.txt"
        test_file.write_bytes(test_content)
        
        sample_document.file_path = str(test_file)
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [sample_document, sample_bot]
        mock_db.add_all = Mock()
        mock_db.commit = Mock()
        
        # Execute
        result = await document_service.process_document(
            document_id=sample_document.id,
            user_id=sample_user.id
        )
        
        # Verify
        assert result["document_id"] == str(sample_document.id)
        assert result["filename"] == sample_document.filename
        assert result["chunks_created"] > 0
        assert result["embeddings_stored"] > 0
        assert "processing_stats" in result
        assert "document_metadata" in result
        
        mock_db.add_all.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_document_not_found(self, document_service, sample_user, mock_db):
        """Test processing non-existent document."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await document_service.process_document(
                document_id=uuid4(),
                user_id=sample_user.id
            )
        
        assert exc_info.value.status_code == 404
        assert "Document not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_process_document_file_not_found(self, document_service, sample_document, sample_user, mock_db):
        """Test processing document when file doesn't exist on disk."""
        # Setup
        sample_document.file_path = "/nonexistent/path.txt"
        mock_db.query.return_value.filter.return_value.first.return_value = sample_document
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await document_service.process_document(
                document_id=sample_document.id,
                user_id=sample_user.id
            )
        
        assert exc_info.value.status_code == 404
        assert "Document file not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_delete_document_success(self, document_service, sample_document, sample_user, mock_db, temp_upload_dir):
        """Test successful document deletion."""
        # Setup
        test_file = temp_upload_dir / "test.txt"
        test_file.write_text("test content")
        sample_document.file_path = str(test_file)
        
        mock_chunks = [
            Mock(embedding_id="chunk-1"),
            Mock(embedding_id="chunk-2")
        ]
        
        mock_db.query.return_value.filter.return_value.first.return_value = sample_document
        mock_db.query.return_value.filter.return_value.all.return_value = mock_chunks
        mock_db.delete = Mock()
        mock_db.commit = Mock()
        
        # Execute
        result = await document_service.delete_document(
            document_id=sample_document.id,
            user_id=sample_user.id
        )
        
        # Verify
        assert result is True
        assert not test_file.exists()  # File should be deleted
        mock_db.delete.assert_called_once_with(sample_document)
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_document_permission_denied(self, document_service, sample_document, sample_user, mock_permission_service, mock_db):
        """Test document deletion with insufficient permissions."""
        # Setup
        mock_permission_service.check_bot_permission.return_value = False
        mock_db.query.return_value.filter.return_value.first.return_value = sample_document
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await document_service.delete_document(
                document_id=sample_document.id,
                user_id=sample_user.id
            )
        
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_list_documents_success(self, document_service, sample_bot, sample_user, mock_db):
        """Test successful document listing."""
        # Setup
        mock_documents = [
            Mock(
                id=uuid4(),
                filename="doc1.txt",
                file_size=100,
                mime_type="text/plain",
                chunk_count=5,
                uploaded_by=sample_user.id,
                created_at=datetime.utcnow()
            ),
            Mock(
                id=uuid4(),
                filename="doc2.pdf",
                file_size=200,
                mime_type="application/pdf",
                chunk_count=10,
                uploaded_by=sample_user.id,
                created_at=datetime.utcnow()
            )
        ]
        
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = mock_documents
        
        # Execute
        result = await document_service.list_documents(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            skip=0,
            limit=10
        )
        
        # Verify
        assert len(result) == 2
        assert all("id" in doc for doc in result)
        assert all("filename" in doc for doc in result)
        assert all("processing_status" in doc for doc in result)
    
    @pytest.mark.asyncio
    async def test_get_document_info_success(self, document_service, sample_document, sample_user, mock_db):
        """Test successful document info retrieval."""
        # Setup
        mock_chunks = [
            Mock(
                id=uuid4(),
                chunk_index=0,
                content="This is chunk 0 content",
                chunk_metadata={"page": 1},
                created_at=datetime.utcnow()
            ),
            Mock(
                id=uuid4(),
                chunk_index=1,
                content="This is chunk 1 content",
                chunk_metadata={"page": 1},
                created_at=datetime.utcnow()
            )
        ]
        
        mock_db.query.return_value.filter.return_value.first.return_value = sample_document
        mock_db.query.return_value.filter.return_value.all.return_value = mock_chunks
        
        # Execute
        result = await document_service.get_document_info(
            document_id=sample_document.id,
            user_id=sample_user.id
        )
        
        # Verify
        assert result["id"] == str(sample_document.id)
        assert result["filename"] == sample_document.filename
        assert len(result["chunks"]) == 2
        assert all("content_preview" in chunk for chunk in result["chunks"])
    
    @pytest.mark.asyncio
    async def test_search_document_content_success(self, document_service, sample_bot, sample_user, mock_db, mock_vector_service):
        """Test successful document content search."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_bot
        
        mock_search_results = [
            {
                "id": "chunk-1",
                "score": 0.9,
                "text": "This is relevant content",
                "metadata": {"document_id": str(uuid4())}
            }
        ]
        mock_vector_service.search_relevant_chunks.return_value = mock_search_results
        
        mock_document = Mock(
            id=uuid4(),
            filename="test.txt",
            mime_type="text/plain"
        )
        mock_db.query.return_value.filter.return_value.first.side_effect = [sample_bot, mock_document]
        
        # Execute
        result = await document_service.search_document_content(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            query="test query",
            top_k=5
        )
        
        # Verify
        assert len(result) == 1
        assert result[0]["score"] == 0.9
        assert "document_info" in result[0]
    
    @pytest.mark.asyncio
    async def test_get_bot_document_stats_success(self, document_service, sample_bot, sample_user, mock_db):
        """Test successful document statistics retrieval."""
        # Setup
        mock_documents = [
            Mock(file_size=100, chunk_count=5, mime_type="text/plain"),
            Mock(file_size=200, chunk_count=10, mime_type="application/pdf"),
            Mock(file_size=150, chunk_count=7, mime_type="text/plain")
        ]
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_documents
        
        # Execute
        result = await document_service.get_bot_document_stats(
            bot_id=sample_bot.id,
            user_id=sample_user.id
        )
        
        # Verify
        assert result["total_documents"] == 3
        assert result["total_file_size"] == 450
        assert result["total_chunks"] == 22
        assert result["average_chunks_per_document"] == 22 / 3
        assert result["file_type_distribution"]["text/plain"] == 2
        assert result["file_type_distribution"]["application/pdf"] == 1
        assert "vector_store_stats" in result


class TestDocumentServiceIntegration:
    """Integration tests for document service."""
    
    @pytest.mark.asyncio
    async def test_upload_and_process_workflow(self, document_service, sample_bot, sample_user, mock_db, temp_upload_dir):
        """Test the complete upload and process workflow."""
        # Setup
        file_content = b"This is a comprehensive test document. It contains multiple sentences and should be processed into chunks."
        upload_file = MockUploadFile("integration_test.txt", file_content)
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [sample_bot, None, sample_bot]  # For upload, process queries
        mock_db.add = Mock()
        mock_db.add_all = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Execute upload
        document = await document_service.upload_document(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            file=upload_file,
            process_immediately=False  # Don't process immediately
        )
        
        # Verify upload
        assert document.filename == "integration_test.txt"
        assert document.chunk_count is None or document.chunk_count == 0  # Not processed yet
        
        # Setup for processing
        document.file_path = str(temp_upload_dir / f"{document.id}.txt")
        Path(document.file_path).write_bytes(file_content)
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [document, sample_bot]
        
        # Execute processing
        process_result = await document_service.process_document(
            document_id=document.id,
            user_id=sample_user.id
        )
        
        # Verify processing
        assert process_result["chunks_created"] > 0
        assert process_result["embeddings_stored"] > 0
        assert process_result["filename"] == "integration_test.txt"
    
    @pytest.mark.asyncio
    async def test_error_handling_and_cleanup(self, document_service, sample_bot, sample_user, mock_db, temp_upload_dir):
        """Test error handling and cleanup in document operations."""
        # Setup for upload failure
        upload_file = MockUploadFile("test.txt", b"content")
        mock_db.query.return_value.filter.return_value.first.return_value = sample_bot
        mock_db.add = Mock()
        mock_db.commit = Mock(side_effect=Exception("Database error"))
        mock_db.rollback = Mock()
        
        # Execute and verify error handling
        with pytest.raises(HTTPException):
            await document_service.upload_document(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                file=upload_file
            )
        
        # Verify rollback was called
        mock_db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_permission_checks_across_operations(self, document_service, sample_bot, sample_user, sample_document, mock_permission_service, mock_db):
        """Test that permission checks are enforced across all operations."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_document
        
        operations = [
            ("upload_document", {"bot_id": sample_bot.id, "user_id": sample_user.id, "file": MockUploadFile("test.txt", b"content")}, "editor"),
            ("process_document", {"document_id": sample_document.id, "user_id": sample_user.id}, "editor"),
            ("delete_document", {"document_id": sample_document.id, "user_id": sample_user.id}, "admin"),
            ("list_documents", {"bot_id": sample_bot.id, "user_id": sample_user.id}, "viewer"),
            ("get_document_info", {"document_id": sample_document.id, "user_id": sample_user.id}, "viewer"),
            ("search_document_content", {"bot_id": sample_bot.id, "user_id": sample_user.id, "query": "test"}, "viewer"),
            ("get_bot_document_stats", {"bot_id": sample_bot.id, "user_id": sample_user.id}, "viewer")
        ]
        
        for operation_name, kwargs, required_role in operations:
            # Setup permission denial
            mock_permission_service.check_bot_permission.return_value = False
            
            # Execute and verify permission check
            with pytest.raises(HTTPException) as exc_info:
                operation = getattr(document_service, operation_name)
                await operation(**kwargs)
            
            assert exc_info.value.status_code == 403
            assert "Insufficient permissions" in str(exc_info.value.detail)
            
            # Verify the correct permission was checked
            mock_permission_service.check_bot_permission.assert_called_with(
                sample_user.id, 
                kwargs.get("bot_id", sample_document.bot_id), 
                required_role
            )