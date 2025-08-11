"""
Unit tests for the cache management service.
"""
import asyncio
import pytest
import pytest_asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from app.services.cache_management_service import (
    CacheManagementService,
    CacheWarmingTask,
    CacheMaintenanceReport
)


@pytest_asyncio.fixture
async def mock_redis():
    """Create a mock Redis client."""
    mock_client = AsyncMock()
    mock_client.ping.return_value = True
    mock_client.keys.return_value = []
    mock_client.hgetall.return_value = {}
    mock_client.hset.return_value = True
    mock_client.delete.return_value = True
    mock_client.exists.return_value = True
    mock_client.zadd.return_value = True
    mock_client.zrem.return_value = True
    mock_client.zrevrange.return_value = []
    mock_client.get.return_value = None
    mock_client.setex.return_value = True
    mock_client.expire.return_value = True
    mock_client.close.return_value = None
    return mock_client


@pytest_asyncio.fixture
async def mock_cache_service():
    """Create a mock cache service."""
    mock_service = AsyncMock()
    mock_service.clear_cache.return_value = None
    mock_service.get_cache_stats.return_value = MagicMock(
        total_requests=100,
        cache_hits=80,
        cache_misses=20,
        hit_rate=0.8,
        total_entries=50,
        memory_usage_mb=10.5,
        evictions=2
    )
    mock_service.cleanup_expired_entries.return_value = None
    mock_service.get_cached_embeddings_batch.return_value = ([], [0, 1, 2])
    return mock_service


@pytest_asyncio.fixture
async def mock_performance_monitor():
    """Create a mock performance monitor."""
    mock_monitor = AsyncMock()
    mock_monitor.analyze_hit_rate_trends.return_value = MagicMock(
        current_hit_rate=0.8,
        avg_hit_rate_24h=0.75,
        avg_hit_rate_7d=0.7,
        trend="improving",
        recommendations=["Cache performance is good"]
    )
    mock_monitor.get_provider_performance_breakdown.return_value = {
        "openai/text-embedding-ada-002": {
            "requests": 50,
            "hits": 40,
            "misses": 10,
            "hit_rate": 0.8,
            "performance_rating": "excellent"
        }
    }
    mock_monitor.cleanup_old_metrics.return_value = None
    return mock_monitor


@pytest_asyncio.fixture
async def cache_mgmt_service(mock_redis, mock_cache_service, mock_performance_monitor):
    """Create a cache management service with mocked dependencies."""
    service = CacheManagementService("redis://localhost:6379")
    
    with patch('redis.asyncio.from_url', return_value=mock_redis), \
         patch('app.services.cache_management_service.get_embedding_cache_service', return_value=mock_cache_service), \
         patch('app.services.cache_management_service.get_cache_performance_monitor', return_value=mock_performance_monitor):
        await service.initialize()
    
    service.cache_service = mock_cache_service
    service.performance_monitor = mock_performance_monitor
    
    return service


@pytest.mark.asyncio
class TestCacheManagementService:
    """Test cases for CacheManagementService."""
    
    async def test_initialization(self, mock_redis, mock_cache_service, mock_performance_monitor):
        """Test cache management service initialization."""
        service = CacheManagementService("redis://localhost:6379")
        
        with patch('redis.asyncio.from_url', return_value=mock_redis), \
             patch('app.services.cache_management_service.get_embedding_cache_service', return_value=mock_cache_service), \
             patch('app.services.cache_management_service.get_cache_performance_monitor', return_value=mock_performance_monitor):
            await service.initialize()
        
        assert service.redis_client is not None
        assert service.cache_service is not None
        assert service.performance_monitor is not None
        mock_redis.ping.assert_called_once()
    
    async def test_invalidate_cache_for_model_change(self, cache_mgmt_service):
        """Test cache invalidation for model changes."""
        provider = "openai"
        old_model = "text-embedding-ada-002"
        new_model = "text-embedding-3-small"
        bot_id = "bot123"
        
        await cache_mgmt_service.invalidate_cache_for_model_change(
            provider, old_model, new_model, bot_id
        )
        
        # Should clear cache for old model
        cache_mgmt_service.cache_service.clear_cache.assert_called_once_with(provider, old_model)
    
    async def test_invalidate_cache_for_provider_change(self, cache_mgmt_service):
        """Test cache invalidation for provider changes."""
        old_provider = "openai"
        new_provider = "gemini"
        bot_id = "bot123"
        
        await cache_mgmt_service.invalidate_cache_for_provider_change(
            old_provider, new_provider, bot_id
        )
        
        # Should clear cache for old provider
        cache_mgmt_service.cache_service.clear_cache.assert_called_once_with(old_provider)
    
    async def test_invalidate_cache_for_document_update(self, cache_mgmt_service):
        """Test cache invalidation for document updates."""
        document_id = "doc123"
        affected_texts = ["text1", "text2", "text3"]
        provider = "openai"
        model = "text-embedding-ada-002"
        
        # Mock Redis exists responses
        cache_mgmt_service.redis_client.exists.side_effect = [True, False, True]
        
        await cache_mgmt_service.invalidate_cache_for_document_update(
            document_id, affected_texts, provider, model
        )
        
        # Should check existence and delete existing entries
        assert cache_mgmt_service.redis_client.exists.call_count == 3
        assert cache_mgmt_service.redis_client.delete.call_count == 2  # Only existing entries
    
    async def test_schedule_cache_warming(self, cache_mgmt_service):
        """Test scheduling cache warming tasks."""
        texts = ["hello world", "test text", "another example"]
        provider = "openai"
        model = "text-embedding-ada-002"
        priority = 7
        
        task_id = await cache_mgmt_service.schedule_cache_warming(
            texts, provider, model, priority
        )
        
        assert task_id is not None
        assert task_id in cache_mgmt_service._warming_tasks
        
        task = cache_mgmt_service._warming_tasks[task_id]
        assert task.texts == texts
        assert task.provider == provider
        assert task.model == model
        assert task.priority == priority
        assert task.status == "pending"
        
        # Should add to warming queue
        cache_mgmt_service.redis_client.zadd.assert_called()
    
    async def test_get_warming_task_status(self, cache_mgmt_service):
        """Test getting warming task status."""
        # Create a test task
        task = CacheWarmingTask(
            task_id="test_task",
            texts=["test"],
            provider="openai",
            model="text-embedding-ada-002",
            priority=5,
            created_at=time.time(),
            status="running",
            progress=0.5
        )
        
        cache_mgmt_service._warming_tasks["test_task"] = task
        
        result = await cache_mgmt_service.get_warming_task_status("test_task")
        
        assert result is not None
        assert result.task_id == "test_task"
        assert result.status == "running"
        assert result.progress == 0.5
        
        # Test non-existent task
        result = await cache_mgmt_service.get_warming_task_status("nonexistent")
        assert result is None
    
    async def test_cancel_warming_task(self, cache_mgmt_service):
        """Test cancelling warming tasks."""
        # Create a pending task
        task = CacheWarmingTask(
            task_id="test_task",
            texts=["test"],
            provider="openai",
            model="text-embedding-ada-002",
            priority=5,
            created_at=time.time(),
            status="pending",
            progress=0.0
        )
        
        cache_mgmt_service._warming_tasks["test_task"] = task
        
        # Should be able to cancel pending task
        result = await cache_mgmt_service.cancel_warming_task("test_task")
        assert result is True
        assert task.status == "cancelled"
        
        # Should remove from queue
        cache_mgmt_service.redis_client.zrem.assert_called_with(
            cache_mgmt_service.warming_queue_key, "test_task"
        )
        
        # Test cancelling non-existent task
        result = await cache_mgmt_service.cancel_warming_task("nonexistent")
        assert result is False
        
        # Test cancelling running task
        task.status = "running"
        result = await cache_mgmt_service.cancel_warming_task("test_task")
        assert result is False
    
    async def test_run_cache_maintenance(self, cache_mgmt_service):
        """Test running cache maintenance."""
        # Force maintenance to bypass time check
        report = await cache_mgmt_service.run_cache_maintenance(force=True)
        
        assert isinstance(report, CacheMaintenanceReport)
        assert report.timestamp > 0
        assert report.maintenance_duration_seconds >= 0
        
        # Should call cleanup methods
        cache_mgmt_service.cache_service.cleanup_expired_entries.assert_called_once()
        cache_mgmt_service.performance_monitor.cleanup_old_metrics.assert_called_once()
    
    async def test_run_cache_maintenance_too_soon(self, cache_mgmt_service):
        """Test maintenance rejection when run too soon."""
        # Set last maintenance to recent time
        cache_mgmt_service._last_maintenance = time.time()
        
        with pytest.raises(ValueError, match="Maintenance not needed"):
            await cache_mgmt_service.run_cache_maintenance(force=False)
    
    async def test_run_cache_maintenance_already_running(self, cache_mgmt_service):
        """Test maintenance rejection when already running."""
        cache_mgmt_service._maintenance_running = True
        
        with pytest.raises(ValueError, match="Maintenance is already running"):
            await cache_mgmt_service.run_cache_maintenance(force=True)
    
    async def test_get_cache_statistics(self, cache_mgmt_service):
        """Test getting comprehensive cache statistics."""
        stats = await cache_mgmt_service.get_cache_statistics()
        
        assert "cache_performance" in stats
        assert "hit_rate_analysis" in stats
        assert "provider_breakdown" in stats
        assert "warming_statistics" in stats
        assert "maintenance" in stats
        
        # Check cache performance stats
        cache_perf = stats["cache_performance"]
        assert cache_perf["total_requests"] == 100
        assert cache_perf["cache_hits"] == 80
        assert cache_perf["hit_rate"] == 0.8
        
        # Check hit rate analysis
        hit_analysis = stats["hit_rate_analysis"]
        assert hit_analysis["current_hit_rate"] == 0.8
        assert hit_analysis["trend"] == "improving"
        
        # Check provider breakdown
        provider_breakdown = stats["provider_breakdown"]
        assert "openai/text-embedding-ada-002" in provider_breakdown
        
        # Check maintenance info
        maintenance = stats["maintenance"]
        assert "last_maintenance" in maintenance
        assert "maintenance_running" in maintenance
    
    async def test_warming_statistics(self, cache_mgmt_service):
        """Test warming task statistics calculation."""
        # Add various tasks
        tasks = [
            CacheWarmingTask("task1", ["text"], "openai", "model", 5, time.time(), "pending", 0.0),
            CacheWarmingTask("task2", ["text"], "openai", "model", 5, time.time(), "running", 0.5),
            CacheWarmingTask("task3", ["text"], "openai", "model", 5, time.time(), "completed", 1.0),
            CacheWarmingTask("task4", ["text"], "openai", "model", 5, time.time(), "failed", 0.0),
            CacheWarmingTask("task5", ["text"], "openai", "model", 5, time.time(), "cancelled", 0.0),
        ]
        
        for task in tasks:
            cache_mgmt_service._warming_tasks[task.task_id] = task
        
        stats = await cache_mgmt_service._get_warming_statistics()
        
        assert stats["total_tasks"] == 5
        assert stats["pending_tasks"] == 1
        assert stats["running_tasks"] == 1
        assert stats["completed_tasks"] == 1
        assert stats["failed_tasks"] == 1
        assert stats["cancelled_tasks"] == 1
    
    async def test_save_and_load_warming_tasks(self, cache_mgmt_service):
        """Test saving and loading warming tasks."""
        # Create a test task
        task = CacheWarmingTask(
            task_id="test_task",
            texts=["hello", "world"],
            provider="openai",
            model="text-embedding-ada-002",
            priority=5,
            created_at=time.time(),
            status="pending",
            progress=0.0
        )
        
        # Save task
        await cache_mgmt_service._save_warming_task(task)
        
        # Should call hset with task data
        cache_mgmt_service.redis_client.hset.assert_called()
        
        # Mock loading tasks
        cache_mgmt_service.redis_client.keys.return_value = ["cache_warming:task:test_task"]
        cache_mgmt_service.redis_client.hgetall.return_value = {
            'task_id': 'test_task',
            'texts': 'hello|world',
            'provider': 'openai',
            'model': 'text-embedding-ada-002',
            'priority': '5',
            'created_at': str(task.created_at),
            'status': 'pending',
            'progress': '0.0',
            'error_message': ''
        }
        
        # Load tasks
        await cache_mgmt_service._load_warming_tasks()
        
        # Should have loaded the task
        assert "test_task" in cache_mgmt_service._warming_tasks
        loaded_task = cache_mgmt_service._warming_tasks["test_task"]
        assert loaded_task.texts == ["hello", "world"]
        assert loaded_task.provider == "openai"
    
    async def test_cleanup_old_warming_tasks(self, cache_mgmt_service):
        """Test cleanup of old warming tasks."""
        # Create old completed task
        old_time = time.time() - (86400 * 8)  # 8 days ago
        old_task = CacheWarmingTask(
            task_id="old_task",
            texts=["text"],
            provider="openai",
            model="model",
            priority=5,
            created_at=old_time,
            status="completed",
            progress=1.0
        )
        
        # Create recent task
        recent_task = CacheWarmingTask(
            task_id="recent_task",
            texts=["text"],
            provider="openai",
            model="model",
            priority=5,
            created_at=time.time(),
            status="completed",
            progress=1.0
        )
        
        cache_mgmt_service._warming_tasks["old_task"] = old_task
        cache_mgmt_service._warming_tasks["recent_task"] = recent_task
        
        await cache_mgmt_service._cleanup_old_warming_tasks()
        
        # Should remove old task but keep recent one
        assert "old_task" not in cache_mgmt_service._warming_tasks
        assert "recent_task" in cache_mgmt_service._warming_tasks
        
        # Should delete old task from Redis
        cache_mgmt_service.redis_client.delete.assert_called_with("cache_warming:task:old_task")
    
    async def test_close(self, cache_mgmt_service):
        """Test cache management service cleanup."""
        await cache_mgmt_service.close()
        cache_mgmt_service.redis_client.close.assert_called_once()


@pytest.mark.asyncio
class TestCacheWarmingTask:
    """Test cases for CacheWarmingTask."""
    
    def test_cache_warming_task_creation(self):
        """Test cache warming task creation."""
        task = CacheWarmingTask(
            task_id="test_task",
            texts=["hello", "world"],
            provider="openai",
            model="text-embedding-ada-002",
            priority=7,
            created_at=time.time(),
            status="pending",
            progress=0.0
        )
        
        assert task.task_id == "test_task"
        assert task.texts == ["hello", "world"]
        assert task.provider == "openai"
        assert task.model == "text-embedding-ada-002"
        assert task.priority == 7
        assert task.status == "pending"
        assert task.progress == 0.0
        assert task.error_message is None


@pytest.mark.asyncio
class TestCacheMaintenanceReport:
    """Test cases for CacheMaintenanceReport."""
    
    def test_maintenance_report_creation(self):
        """Test maintenance report creation."""
        report = CacheMaintenanceReport(
            timestamp=time.time(),
            expired_entries_cleaned=10,
            invalid_entries_cleaned=5,
            memory_freed_mb=2.5,
            maintenance_duration_seconds=30.0,
            errors=["Error 1", "Error 2"]
        )
        
        assert report.expired_entries_cleaned == 10
        assert report.invalid_entries_cleaned == 5
        assert report.memory_freed_mb == 2.5
        assert report.maintenance_duration_seconds == 30.0
        assert len(report.errors) == 2