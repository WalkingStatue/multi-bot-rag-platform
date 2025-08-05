#!/usr/bin/env python3
"""
Test script for Collection Lifecycle Management and Monitoring (Task 4.2)

This script tests the new functionality added to VectorCollectionManager:
- Configuration change detection and migration triggers
- Retry logic with exponential backoff for collection operations
- Detailed error logging and diagnostic information
- Collection optimization and maintenance scheduling
"""

import asyncio
import sys
import os
import uuid
import time
from unittest.mock import Mock, AsyncMock, patch

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.vector_collection_manager import (
    VectorCollectionManager, 
    CollectionInfo, 
    CollectionResult,
    OptimizationResult,
    ConfigurationChange,
    MaintenanceTask,
    DiagnosticInfo,
    CollectionStatus,
    MaintenanceTaskType
)


class MockBot:
    """Mock bot for testing."""
    def __init__(self, bot_id, embedding_provider="openai", embedding_model="text-embedding-ada-002"):
        self.id = bot_id
        self.embedding_provider = embedding_provider
        self.embedding_model = embedding_model


class MockDB:
    """Mock database session for testing."""
    def __init__(self):
        self.bots = []
    
    def query(self, model):
        if model.__name__ == 'Bot':
            return MockQuery(self.bots)
        return MockQuery([])
    
    def add_bot(self, bot):
        self.bots.append(bot)


class MockQuery:
    """Mock query object."""
    def __init__(self, items):
        self.items = items
    
    def filter(self, *args):
        return self
    
    def first(self):
        return self.items[0] if self.items else None
    
    def all(self):
        return self.items


async def test_configuration_change_detection():
    """Test configuration change detection functionality."""
    print("Testing configuration change detection...")
    
    # Setup
    mock_db = MockDB()
    bot_id = uuid.uuid4()
    bot = MockBot(bot_id, "openai", "text-embedding-ada-002")
    mock_db.add_bot(bot)
    
    # Mock embedding service
    with patch('app.services.vector_collection_manager.EmbeddingProviderService') as mock_embedding_service:
        mock_embedding_service.return_value.get_embedding_dimension.return_value = 1536
        
        manager = VectorCollectionManager(mock_db)
        
        # First call - should store initial configuration
        change1 = await manager.detect_configuration_changes(bot_id)
        assert change1 is None, "First call should not detect changes"
        
        # Change the bot configuration
        bot.embedding_provider = "gemini"
        bot.embedding_model = "embedding-001"
        mock_embedding_service.return_value.get_embedding_dimension.return_value = 768
        
        # Second call - should detect changes
        change2 = await manager.detect_configuration_changes(bot_id)
        assert change2 is not None, "Should detect configuration change"
        assert change2.change_type in ["provider", "model", "dimension", "multiple"], f"Unexpected change type: {change2.change_type}"
        assert change2.migration_required, "Migration should be required for provider change"
        assert change2.priority == "high", "Provider change should be high priority"
        
        print("✓ Configuration change detection working correctly")


async def test_retry_logic():
    """Test retry logic with exponential backoff."""
    print("Testing retry logic with exponential backoff...")
    
    mock_db = MockDB()
    bot_id = uuid.uuid4()
    
    with patch('app.services.vector_collection_manager.VectorService') as mock_vector_service:
        manager = VectorCollectionManager(mock_db)
        
        # Mock operation that fails twice then succeeds
        call_count = 0
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Simulated failure {call_count}")
            return f"Success after {call_count} attempts"
        
        # Test successful retry
        start_time = time.time()
        result = await manager.perform_collection_operation_with_retry(
            "test_operation",
            failing_operation,
            bot_id
        )
        end_time = time.time()
        
        assert result == "Success after 3 attempts", f"Unexpected result: {result}"
        assert call_count == 3, f"Expected 3 calls, got {call_count}"
        
        # Should have taken some time due to exponential backoff
        assert end_time - start_time >= 2.0, "Should have waited for retry delays"
        
        print("✓ Retry logic with exponential backoff working correctly")


async def test_diagnostic_logging():
    """Test detailed diagnostic logging."""
    print("Testing diagnostic logging...")
    
    mock_db = MockDB()
    manager = VectorCollectionManager(mock_db)
    
    # Log some diagnostic information
    await manager._log_diagnostic_info(
        bot_id="test-bot-1",
        error_type="test_error",
        error_message="This is a test error",
        context={"operation": "test", "attempt": 1},
        remediation_steps=["Step 1", "Step 2"]
    )
    
    await manager._log_diagnostic_info(
        bot_id="test-bot-2",
        error_type="another_error",
        error_message="Another test error",
        context={"operation": "test2", "attempt": 2}
    )
    
    # Get diagnostic summary
    summary = manager.get_diagnostic_summary(hours=1)
    
    assert summary["total_diagnostic_entries"] == 2, f"Expected 2 entries, got {summary['total_diagnostic_entries']}"
    assert "test_error" in summary["error_types"], "Should contain test_error"
    assert "another_error" in summary["error_types"], "Should contain another_error"
    assert "test-bot-1" in summary["affected_bots"], "Should contain test-bot-1"
    assert "test-bot-2" in summary["affected_bots"], "Should contain test-bot-2"
    
    print("✓ Diagnostic logging working correctly")


async def test_maintenance_scheduling():
    """Test maintenance task scheduling."""
    print("Testing maintenance task scheduling...")
    
    mock_db = MockDB()
    
    # Add some test bots
    bot1 = MockBot(uuid.uuid4(), "openai", "text-embedding-ada-002")
    bot2 = MockBot(uuid.uuid4(), "gemini", "embedding-001")
    mock_db.add_bot(bot1)
    mock_db.add_bot(bot2)
    
    with patch('app.services.vector_collection_manager.VectorService') as mock_vector_service, \
         patch('app.services.vector_collection_manager.EmbeddingProviderService') as mock_embedding_service:
        
        # Mock vector service methods
        mock_vector_service.return_value.vector_store.collection_exists = AsyncMock(return_value=True)
        mock_vector_service.return_value.get_bot_collection_stats = AsyncMock(return_value={
            'points_count': 1500,  # Above optimization threshold
            'config': {'vector_size': 1536},
            'status': 'green'
        })
        
        manager = VectorCollectionManager(mock_db)
        
        # Force last maintenance check to be old
        manager._last_maintenance_check = time.time() - 7200  # 2 hours ago
        
        # Schedule maintenance tasks
        result = await manager.schedule_maintenance_tasks()
        
        assert result["tasks_scheduled"] > 0, "Should have scheduled some tasks"
        assert len(manager._maintenance_queue) > 0, "Maintenance queue should not be empty"
        
        # Check queue status
        queue_status = manager.get_maintenance_queue_status()
        assert queue_status["total_tasks"] > 0, "Should have tasks in queue"
        assert "optimization" in queue_status["tasks_by_type"], "Should have optimization tasks"
        
        print("✓ Maintenance scheduling working correctly")


async def test_maintenance_execution():
    """Test maintenance task execution."""
    print("Testing maintenance task execution...")
    
    mock_db = MockDB()
    bot_id = uuid.uuid4()
    bot = MockBot(bot_id, "openai", "text-embedding-ada-002")
    mock_db.add_bot(bot)
    
    with patch('app.services.vector_collection_manager.VectorService') as mock_vector_service, \
         patch('app.services.vector_collection_manager.EmbeddingProviderService') as mock_embedding_service:
        
        # Mock services
        mock_vector_service.return_value.vector_store.collection_exists = AsyncMock(return_value=True)
        mock_vector_service.return_value.get_bot_collection_stats = AsyncMock(return_value={
            'points_count': 100,
            'config': {'vector_size': 1536},
            'status': 'green'
        })
        mock_embedding_service.return_value.get_embedding_dimension.return_value = 1536
        
        manager = VectorCollectionManager(mock_db)
        
        # Add a test maintenance task
        test_task = MaintenanceTask(
            bot_id=str(bot_id),
            task_type=MaintenanceTaskType.HEALTH_CHECK.value,
            scheduled_at=time.time(),
            priority=1
        )
        manager._maintenance_queue.append(test_task)
        
        # Execute the task
        result = await manager.execute_next_maintenance_task()
        
        assert result is not None, "Should have executed a task"
        assert result["success"], f"Task should have succeeded: {result.get('error', 'No error')}"
        assert result["task_type"] == MaintenanceTaskType.HEALTH_CHECK.value, "Should have executed health check"
        
        print("✓ Maintenance task execution working correctly")


async def main():
    """Run all tests."""
    print("Starting Collection Lifecycle Management and Monitoring Tests (Task 4.2)")
    print("=" * 70)
    
    try:
        await test_configuration_change_detection()
        await test_retry_logic()
        await test_diagnostic_logging()
        await test_maintenance_scheduling()
        await test_maintenance_execution()
        
        print("=" * 70)
        print("✅ All tests passed! Task 4.2 implementation is working correctly.")
        print("\nImplemented features:")
        print("- Configuration change detection and migration triggers")
        print("- Retry logic with exponential backoff for collection operations")
        print("- Detailed error logging and diagnostic information")
        print("- Collection optimization and maintenance scheduling")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())