"""
Tests for document reprocessing functionality.
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4, UUID

from sqlalchemy.orm import Session

from app.services.document_reprocessing_service import (
    DocumentReprocessingService,
    ReprocessingStatus,
    ReprocessingPhase,
    DocumentProcessingResult,
    BatchProcessingResult,
    ReprocessingReport
)
from app.services.data_integrity_service import (
    DataIntegrityService,
    IntegrityCheckType,
    IntegrityIssueLevel,
    IntegrityIssue,
    DataSnapshot,
    RollbackResult
)
from app.services.reprocessing_queue_manager import (
    ReprocessingQueueManager,
    OperationPriority,
    QueueStatus
)
from app.models.bot import Bot
from app.models.document import Document, DocumentChunk
from app.models.user import User


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def mock_bot():
    """Mock bot instance."""
    bot = Mock(spec=Bot)
    bot.id = uuid4()
    bot.owner_id = uuid4()
    bot.embedding_provider = "openai"
    bot.embedding_model = "text-embedding-ada-002"
    return bot


@pytest.fixture
def mock_user():
    """Mock user instance."""
    user = Mock(spec=User)
    user.id = uuid4()
    return user


@pytest.fixture
def mock_documents():
    """Mock document instances."""
    documents = []
    for i in range(3):
        doc = Mock(spec=Document)
        doc.id = uuid4()
        doc.filename = f"test_document_{i}.pdf"
        doc.file_path = f"/tmp/test_document_{i}.pdf"
        doc.chunk_count = 5
        documents.append(doc)
    return documents


@pytest.fixture
def mock_chunks():
    """Mock chunk instances."""
    chunks = []
    for i in range(15):  # 5 chunks per document
        chunk = Mock(spec=DocumentChunk)
        chunk.id = uuid4()
        chunk.chunk_index = i % 5
        chunk.content = f"Test chunk content {i}"
        chunk.embedding_id = f"embedding_{i}"
        chunks.append(chunk)
    return chunks


class TestDocumentReprocessingService:
    """Test cases for DocumentReprocessingService."""
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mocked dependencies."""
        with patch('app.services.document_reprocessing_service.EmbeddingProviderService'), \
             patch('app.services.document_reprocessing_service.VectorService'), \
             patch('app.services.document_reprocessing_service.VectorCollectionManager'), \
             patch('app.services.document_reprocessing_service.OptimizedChunkStorage'), \
             patch('app.services.document_reprocessing_service.UserService'), \
             patch('app.services.document_reprocessing_service.DocumentProcessor'):
            
            service = DocumentReprocessingService(mock_db)
            
            # Mock the processor
            service.processor = Mock()
            service.processor.process_document = Mock(return_value=([], {}))
            
            return service
    
    @pytest.mark.asyncio
    async def test_reprocess_bot_documents_success(self, service, mock_db, mock_bot, mock_user):
        """Test successful bot document reprocessing."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = mock_bot
        
        # Mock the execute method to return immediately
        with patch.object(service, '_execute_reprocessing_operation') as mock_execute:
            mock_execute.return_value = Mock()
            
            # Call the method
            operation_id = await service.reprocess_bot_documents(
                bot_id=mock_bot.id,
                user_id=mock_user.id,
                batch_size=5
            )
            
            # Verify operation was queued
            assert operation_id is not None
            assert operation_id.startswith(f"reprocess_{mock_bot.id}")
    
    @pytest.mark.asyncio
    async def test_reprocess_bot_documents_bot_not_found(self, service, mock_db, mock_user):
        """Test reprocessing with non-existent bot."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Call the method and expect exception
        with pytest.raises(Exception) as exc_info:
            await service.reprocess_bot_documents(
                bot_id=uuid4(),
                user_id=mock_user.id
            )
        
        assert "Bot not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_process_documents_in_batches(self, service, mock_db, mock_documents, mock_user):
        """Test batch processing of documents."""
        operation_id = "test_operation"
        bot_id = uuid4()
        
        # Setup progress tracking
        service.progress_tracking[operation_id] = Mock()
        service.progress_tracking[operation_id].total_batches = 0
        service.progress_tracking[operation_id].total_documents = 0
        
        # Mock document processing
        with patch.object(service, '_process_document_batch') as mock_process_batch:
            mock_batch_result = BatchProcessingResult(
                batch_id="test_batch_1",
                documents_processed=3,
                documents_successful=2,
                documents_failed=1,
                total_chunks_processed=10,
                total_chunks_stored=8,
                processing_time=30.0,
                errors=[{"error": "test error", "document_id": "doc1"}]
            )
            mock_process_batch.return_value = mock_batch_result
            
            # Call the method
            result = await service._process_documents_in_batches(
                operation_id=operation_id,
                bot_id=bot_id,
                user_id=mock_user.id,
                batch_size=5
            )
            
            # Verify results
            assert result["success"] is True
            assert result["total_documents"] == 3
            assert result["successful_documents"] == 2
            assert result["failed_documents"] == 1
    
    @pytest.mark.asyncio
    async def test_process_single_document_with_isolation(self, service, mock_db, mock_documents, mock_user):
        """Test processing single document with error isolation."""
        semaphore = asyncio.Semaphore(1)
        document = mock_documents[0]
        bot_id = uuid4()
        operation_id = "test_operation"
        
        # Mock file operations
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=b"test content")), \
             patch.object(service, '_process_document_content') as mock_process:
            
            # Mock document processing
            mock_chunk = Mock()
            mock_chunk.content = "test content"
            mock_chunk.chunk_index = 0
            mock_chunk.start_char = 0
            mock_chunk.end_char = 12
            mock_chunk.metadata = {}
            
            mock_process.return_value = ([mock_chunk], {})
            
            # Mock bot query
            mock_bot = Mock()
            mock_bot.embedding_provider = "openai"
            mock_bot.embedding_model = "text-embedding-ada-002"
            mock_bot.owner_id = mock_user.id
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_bot
            
            # Mock embedding service
            service.embedding_service.generate_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
            
            # Mock user service
            service.user_service.get_user_api_key = Mock(return_value="test_api_key")
            
            # Mock storage service
            mock_storage_result = Mock()
            mock_storage_result.success = True
            mock_storage_result.stored_chunks = 1
            service.optimized_storage.store_chunks_efficiently = AsyncMock(return_value=mock_storage_result)
            
            # Call the method
            result = await service._process_single_document_with_isolation(
                semaphore=semaphore,
                document=document,
                bot_id=bot_id,
                user_id=mock_user.id,
                operation_id=operation_id
            )
            
            # Verify results
            assert result.success is True
            assert result.document_id == document.id
            assert result.chunks_processed == 1
            assert result.chunks_stored == 1


def mock_open(read_data=b""):
    """Mock open function for file operations."""
    from unittest.mock import mock_open as _mock_open
    return _mock_open(read_data=read_data)


class TestDataIntegrityService:
    """Test cases for DataIntegrityService."""
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mocked dependencies."""
        with patch('app.services.data_integrity_service.VectorService'):
            return DataIntegrityService(mock_db)
    
    @pytest.mark.asyncio
    async def test_create_data_snapshot(self, service, mock_db, mock_bot):
        """Test creating data snapshot."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = mock_bot
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        
        # Mock vector service
        service.vector_service.get_bot_collection_stats = AsyncMock(return_value={'points_count': 10})
        
        # Mock file operations
        with patch('builtins.open', mock_open()), \
             patch('pathlib.Path.mkdir'), \
             patch.object(service, '_store_snapshot') as mock_store:
            
            mock_store.return_value = None
            
            # Call the method
            snapshot = await service.create_data_snapshot(mock_bot.id)
            
            # Verify snapshot
            assert snapshot.bot_id == mock_bot.id
            assert snapshot.document_count == 5
            assert snapshot.chunk_count == 5
            assert snapshot.vector_count == 10
    
    @pytest.mark.asyncio
    async def test_verify_data_integrity(self, service, mock_db, mock_bot):
        """Test data integrity verification."""
        # Mock integrity checks
        with patch.object(service, '_perform_integrity_check') as mock_check:
            mock_issue = IntegrityIssue(
                check_type=IntegrityCheckType.DOCUMENT_CHUNK_CONSISTENCY,
                level=IntegrityIssueLevel.WARNING,
                description="Test issue",
                affected_entities=[str(mock_bot.id)]
            )
            
            mock_result = Mock()
            mock_result.passed = False
            mock_result.issues = [mock_issue]
            mock_result.check_duration = 1.0
            
            mock_check.return_value = mock_result
            
            # Call the method
            results = await service.verify_data_integrity(
                bot_id=mock_bot.id,
                check_types=[IntegrityCheckType.DOCUMENT_CHUNK_CONSISTENCY]
            )
            
            # Verify results
            assert len(results) == 1
            assert IntegrityCheckType.DOCUMENT_CHUNK_CONSISTENCY.value in results
            assert not results[IntegrityCheckType.DOCUMENT_CHUNK_CONSISTENCY.value].passed
    
    @pytest.mark.asyncio
    async def test_execute_rollback_success(self, service, mock_db, mock_bot):
        """Test successful rollback execution."""
        snapshot_id = "test_snapshot"
        
        # Mock snapshot loading
        mock_snapshot = DataSnapshot(
            snapshot_id=snapshot_id,
            bot_id=mock_bot.id,
            created_at=time.time(),
            document_count=5,
            chunk_count=10,
            vector_count=10,
            collection_config={},
            document_checksums={},
            chunk_checksums={}
        )
        
        with patch.object(service, '_load_snapshot', return_value=mock_snapshot), \
             patch.object(service, 'create_rollback_plan') as mock_plan, \
             patch.object(service, '_execute_rollback_step') as mock_step, \
             patch.object(service, 'verify_data_integrity') as mock_verify:
            
            # Mock rollback plan
            mock_rollback_plan = Mock()
            mock_rollback_plan.rollback_steps = [
                {"step": 1, "action": "test_action", "description": "Test step"}
            ]
            mock_plan.return_value = mock_rollback_plan
            
            # Mock verification
            mock_verify.return_value = {}
            
            # Call the method
            result = await service.execute_rollback(
                snapshot_id=snapshot_id,
                bot_id=mock_bot.id
            )
            
            # Verify results
            assert result.success is True
            assert result.snapshot_id == snapshot_id
            assert result.bot_id == mock_bot.id
            assert result.steps_completed == 1


class TestReprocessingQueueManager:
    """Test cases for ReprocessingQueueManager."""
    
    @pytest.fixture
    def manager(self, mock_db):
        """Create queue manager instance with mocked dependencies."""
        with patch('app.services.reprocessing_queue_manager.DocumentReprocessingService'):
            manager = ReprocessingQueueManager(mock_db, max_concurrent_operations=2)
            
            # Stop background tasks for testing
            if manager.queue_processor_task:
                manager.queue_processor_task.cancel()
            if manager.resource_monitor_task:
                manager.resource_monitor_task.cancel()
            
            return manager
    
    @pytest.mark.asyncio
    async def test_queue_reprocessing_operation(self, manager, mock_bot, mock_user):
        """Test queuing a reprocessing operation."""
        # Call the method
        operation_id = await manager.queue_reprocessing_operation(
            bot_id=mock_bot.id,
            user_id=mock_user.id,
            batch_size=10,
            priority=OperationPriority.HIGH
        )
        
        # Verify operation was queued
        assert operation_id is not None
        assert operation_id in manager.operation_metadata
        
        # Check queue state
        assert len(manager.operation_queues[OperationPriority.HIGH]) == 1
        assert manager.statistics.total_operations == 1
        assert manager.statistics.queued_operations == 1
    
    @pytest.mark.asyncio
    async def test_queue_full_error(self, manager, mock_bot, mock_user):
        """Test error when queue is full."""
        # Fill the queue
        manager.max_queue_size = 1
        
        # Queue first operation
        await manager.queue_reprocessing_operation(
            bot_id=mock_bot.id,
            user_id=mock_user.id
        )
        
        # Try to queue second operation
        with pytest.raises(ValueError, match="queue is full"):
            await manager.queue_reprocessing_operation(
                bot_id=mock_bot.id,
                user_id=mock_user.id
            )
    
    def test_get_next_operation(self, manager, mock_bot, mock_user):
        """Test getting next operation from priority queues."""
        # Add operations with different priorities
        high_op = Mock()
        high_op.priority = OperationPriority.HIGH
        manager.operation_queues[OperationPriority.HIGH].append(high_op)
        
        normal_op = Mock()
        normal_op.priority = OperationPriority.NORMAL
        manager.operation_queues[OperationPriority.NORMAL].append(normal_op)
        
        # Get next operation (should be high priority)
        next_op = manager._get_next_operation()
        assert next_op == high_op
        
        # High priority queue should now be empty
        assert len(manager.operation_queues[OperationPriority.HIGH]) == 0
        
        # Get next operation (should be normal priority)
        next_op = manager._get_next_operation()
        assert next_op == normal_op
    
    def test_get_operation_status_queued(self, manager, mock_bot, mock_user):
        """Test getting status of queued operation."""
        # Create and queue operation
        from app.services.reprocessing_queue_manager import QueuedOperation
        
        operation = QueuedOperation(
            operation_id="test_op",
            bot_id=mock_bot.id,
            user_id=mock_user.id,
            priority=OperationPriority.NORMAL,
            batch_size=10,
            force_recreate_collection=False,
            enable_rollback=True,
            queued_at=time.time()
        )
        
        manager.operation_metadata["test_op"] = operation
        manager.operation_queues[OperationPriority.NORMAL].append(operation)
        
        # Get status
        status = manager.get_operation_status("test_op")
        
        # Verify status
        assert status is not None
        assert status["operation_id"] == "test_op"
        assert status["status"] == "queued"
        assert status["priority"] == "NORMAL"
    
    @pytest.mark.asyncio
    async def test_cancel_queued_operation(self, manager, mock_bot, mock_user):
        """Test cancelling a queued operation."""
        # Queue operation
        operation_id = await manager.queue_reprocessing_operation(
            bot_id=mock_bot.id,
            user_id=mock_user.id
        )
        
        # Cancel operation
        cancelled = await manager.cancel_operation(operation_id)
        
        # Verify cancellation
        assert cancelled is True
        assert manager.statistics.cancelled_operations == 1
        assert len(manager.operation_queues[OperationPriority.NORMAL]) == 0


@pytest.mark.asyncio
async def test_integration_reprocessing_flow():
    """Integration test for complete reprocessing flow."""
    # This test would require more setup and mocking
    # but demonstrates how the components work together
    
    mock_db = Mock(spec=Session)
    
    # Create services
    with patch('app.services.document_reprocessing_service.EmbeddingProviderService'), \
         patch('app.services.document_reprocessing_service.VectorService'), \
         patch('app.services.document_reprocessing_service.VectorCollectionManager'), \
         patch('app.services.document_reprocessing_service.OptimizedChunkStorage'), \
         patch('app.services.document_reprocessing_service.UserService'), \
         patch('app.services.document_reprocessing_service.DocumentProcessor'):
        
        reprocessing_service = DocumentReprocessingService(mock_db)
        queue_manager = ReprocessingQueueManager(mock_db, reprocessing_service=reprocessing_service)
        
        # Stop background tasks
        if queue_manager.queue_processor_task:
            queue_manager.queue_processor_task.cancel()
        if queue_manager.resource_monitor_task:
            queue_manager.resource_monitor_task.cancel()
        
        # Mock bot and user
        bot_id = uuid4()
        user_id = uuid4()
        
        # Queue operation
        operation_id = await queue_manager.queue_reprocessing_operation(
            bot_id=bot_id,
            user_id=user_id,
            batch_size=5
        )
        
        # Verify operation was queued
        assert operation_id is not None
        
        # Check status
        status = queue_manager.get_operation_status(operation_id)
        assert status["status"] == "queued"
        
        # Get queue statistics
        stats = queue_manager.get_queue_statistics()
        assert stats.queued_operations == 1
        assert stats.total_operations == 1