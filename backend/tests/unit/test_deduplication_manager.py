"""
Unit tests for deduplication manager service.
Tests requirements 10.3, 10.5 for task 11.2.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from app.services.deduplication_manager import (
    DeduplicationManager,
    DeduplicationPolicy,
    ConflictResolutionStrategy,
    ConflictResolutionCase,
    DeduplicationReport
)
from app.models.document import DocumentChunk, Document
from app.models.bot import Bot


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock()


@pytest.fixture
def mock_vector_service():
    """Mock vector service."""
    service = Mock()
    service.delete_document_chunks = AsyncMock()
    return service


@pytest.fixture
def mock_deduplication_service():
    """Mock deduplication service."""
    service = Mock()
    service.detect_chunk_similarities = AsyncMock()
    service.deduplicate_chunks = AsyncMock()
    service._merge_chunks = AsyncMock()
    service.get_deduplication_statistics = AsyncMock()
    return service


@pytest.fixture
def mock_audit_service():
    """Mock audit service."""
    service = Mock()
    service.record_deduplication_decision = AsyncMock()
    service.record_batch_deduplication = AsyncMock()
    service.get_deduplication_statistics = AsyncMock()
    return service


@pytest.fixture
def deduplication_manager(mock_db, mock_vector_service, mock_deduplication_service, mock_audit_service):
    """Create deduplication manager instance."""
    return DeduplicationManager(
        mock_db, 
        mock_vector_service, 
        mock_deduplication_service, 
        mock_audit_service
    )


@pytest.fixture
def sample_policy():
    """Create sample deduplication policy."""
    return DeduplicationPolicy(
        enabled=True,
        auto_deduplicate_on_upload=True,
        conflict_resolution_strategy=ConflictResolutionStrategy.CONSERVATIVE,
        similarity_threshold=0.95,
        batch_size=100,
        preserve_source_attribution=True,
        enable_cross_document_deduplication=True
    )


@pytest.fixture
def sample_chunks():
    """Create sample document chunks."""
    bot_id = uuid4()
    doc_id = uuid4()
    
    chunks = []
    for i in range(4):
        chunk = DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            bot_id=bot_id,
            chunk_index=i,
            content=f"Sample content {i}",
            embedding_id=f"embed_{i}",
            chunk_metadata={"page": 1, "section": f"section_{i}"},
            created_at=datetime.utcnow() - timedelta(minutes=i)
        )
        chunks.append(chunk)
    
    return chunks


class TestDeduplicationManager:
    """Test cases for deduplication manager."""
    
    @pytest.mark.asyncio
    async def test_configure_deduplication_policy(
        self, deduplication_manager, mock_db, sample_policy
    ):
        """Test deduplication policy configuration."""
        bot_id = uuid4()
        user_id = uuid4()
        
        # Mock bot query
        mock_bot = Mock()
        mock_bot.id = bot_id
        mock_bot.deduplication_config = {}
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_bot
        mock_db.query.return_value = mock_query
        mock_db.commit = Mock()
        
        result = await deduplication_manager.configure_deduplication_policy(
            bot_id, sample_policy, user_id
        )
        
        assert result['success'] is True
        assert 'policy' in result
        assert result['policy']['enabled'] is True
        assert result['policy']['similarity_threshold'] == 0.95
        
        # Should have committed changes
        mock_db.commit.assert_called_once()
    
    def test_validate_policy_valid(self, deduplication_manager, sample_policy):
        """Test policy validation with valid configuration."""
        result = deduplication_manager._validate_policy(sample_policy)
        
        assert result['valid'] is True
        assert result['error'] is None
    
    def test_validate_policy_invalid_threshold(self, deduplication_manager):
        """Test policy validation with invalid similarity threshold."""
        invalid_policy = DeduplicationPolicy(similarity_threshold=1.5)
        
        result = deduplication_manager._validate_policy(invalid_policy)
        
        assert result['valid'] is False
        assert 'threshold must be between' in result['error']
    
    def test_validate_policy_invalid_batch_size(self, deduplication_manager):
        """Test policy validation with invalid batch size."""
        invalid_policy = DeduplicationPolicy(batch_size=5000)
        
        result = deduplication_manager._validate_policy(invalid_policy)
        
        assert result['valid'] is False
        assert 'Batch size must be between' in result['error']
    
    def test_validate_policy_warnings(self, deduplication_manager):
        """Test policy validation with warning conditions."""
        warning_policy = DeduplicationPolicy(
            similarity_threshold=0.75,
            retention_days=15
        )
        
        result = deduplication_manager._validate_policy(warning_policy)
        
        assert result['valid'] is True
        assert len(result['warnings']) > 0
        assert any('Low similarity threshold' in warning for warning in result['warnings'])
    
    @pytest.mark.asyncio
    async def test_remove_old_document_chunks(
        self, deduplication_manager, mock_db, mock_vector_service, sample_chunks, sample_policy
    ):
        """Test removal of old document chunks during reprocessing."""
        bot_id = sample_chunks[0].bot_id
        document_id = sample_chunks[0].document_id
        
        # Mock database queries
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_chunks
        mock_query.delete.return_value = len(sample_chunks)
        mock_db.query.return_value = mock_query
        mock_db.commit = Mock()
        
        removed_count = await deduplication_manager._remove_old_document_chunks(
            bot_id, document_id, sample_policy
        )
        
        assert removed_count == len(sample_chunks)
        
        # Should have called vector service to delete embeddings
        mock_vector_service.delete_document_chunks.assert_called_once()
        
        # Should have committed database changes
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_detect_conflicts_ambiguous_similarity(
        self, deduplication_manager, mock_deduplication_service, sample_policy
    ):
        """Test conflict detection for ambiguous similarity."""
        bot_id = uuid4()
        chunk_ids = [uuid4(), uuid4()]
        
        # Mock similarity detection
        from app.services.chunk_deduplication_service import ChunkSimilarity
        mock_similarity = ChunkSimilarity(
            chunk1_id=chunk_ids[0],
            chunk2_id=chunk_ids[1],
            similarity_score=0.85,  # Below threshold but above 0.7
            similarity_type='medium',
            content_overlap=0.8,
            metadata_compatibility=True
        )
        
        mock_deduplication_service.detect_chunk_similarities.return_value = [mock_similarity]
        
        conflicts = await deduplication_manager._detect_conflicts(
            bot_id, chunk_ids, sample_policy
        )
        
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == 'ambiguous_similarity'
        assert conflicts[0].suggested_action == 'preserve_both'  # Conservative strategy
    
    @pytest.mark.asyncio
    async def test_detect_conflicts_metadata_conflict(
        self, deduplication_manager, mock_deduplication_service, mock_db, sample_policy
    ):
        """Test conflict detection for metadata conflicts."""
        bot_id = uuid4()
        chunk_ids = [uuid4(), uuid4()]
        
        # Mock similarity with metadata incompatibility
        from app.services.chunk_deduplication_service import ChunkSimilarity
        mock_similarity = ChunkSimilarity(
            chunk1_id=chunk_ids[0],
            chunk2_id=chunk_ids[1],
            similarity_score=0.96,  # High similarity
            similarity_type='high',
            content_overlap=0.9,
            metadata_compatibility=False  # Metadata conflict
        )
        
        mock_deduplication_service.detect_chunk_similarities.return_value = [mock_similarity]
        
        conflicts = await deduplication_manager._detect_conflicts(
            bot_id, chunk_ids, sample_policy
        )
        
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == 'metadata_conflict'
        assert conflicts[0].suggested_action == 'preserve_both'  # Conservative strategy
    
    def test_suggest_conflict_action_conservative(self, deduplication_manager):
        """Test conflict action suggestion with conservative strategy."""
        policy = DeduplicationPolicy(
            conflict_resolution_strategy=ConflictResolutionStrategy.CONSERVATIVE
        )
        
        # Test ambiguous similarity
        action = deduplication_manager._suggest_conflict_action(
            'ambiguous_similarity', None, policy
        )
        assert action == 'preserve_both'
        
        # Test metadata conflict
        action = deduplication_manager._suggest_conflict_action(
            'metadata_conflict', None, policy
        )
        assert action == 'preserve_both'
    
    def test_suggest_conflict_action_aggressive(self, deduplication_manager):
        """Test conflict action suggestion with aggressive strategy."""
        policy = DeduplicationPolicy(
            conflict_resolution_strategy=ConflictResolutionStrategy.AGGRESSIVE
        )
        
        action = deduplication_manager._suggest_conflict_action(
            'ambiguous_similarity', None, policy
        )
        assert action == 'merge_if_compatible'
    
    def test_suggest_conflict_action_oldest_wins(self, deduplication_manager):
        """Test conflict action suggestion with oldest wins strategy."""
        policy = DeduplicationPolicy(
            conflict_resolution_strategy=ConflictResolutionStrategy.OLDEST_WINS
        )
        
        action = deduplication_manager._suggest_conflict_action(
            'metadata_conflict', None, policy
        )
        assert action == 'keep_oldest'
    
    @pytest.mark.asyncio
    async def test_resolve_conflict_preserve_both(self, deduplication_manager, sample_policy):
        """Test conflict resolution with preserve both action."""
        conflict = ConflictResolutionCase(
            case_id=str(uuid4()),
            bot_id=uuid4(),
            chunk_ids=[uuid4(), uuid4()],
            similarity_scores=[0.85],
            conflict_type='ambiguous_similarity',
            suggested_action='preserve_both',
            confidence_score=0.5,
            created_at=datetime.utcnow()
        )
        
        result = await deduplication_manager._resolve_conflict(
            conflict, sample_policy, uuid4()
        )
        
        assert result['resolved'] is True
        assert result['action'] == 'preserved'
        assert result['chunks_affected'] == 0
        assert conflict.resolved is True
    
    @pytest.mark.asyncio
    async def test_resolve_conflict_keep_oldest(
        self, deduplication_manager, mock_db, mock_vector_service, sample_chunks
    ):
        """Test conflict resolution with keep oldest action."""
        policy = DeduplicationPolicy(
            conflict_resolution_strategy=ConflictResolutionStrategy.OLDEST_WINS
        )
        
        conflict = ConflictResolutionCase(
            case_id=str(uuid4()),
            bot_id=sample_chunks[0].bot_id,
            chunk_ids=[sample_chunks[0].id, sample_chunks[1].id],
            similarity_scores=[0.85],
            conflict_type='metadata_conflict',
            suggested_action='keep_oldest',
            confidence_score=0.3,
            created_at=datetime.utcnow()
        )
        
        # Mock database queries
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.in_.return_value = sample_chunks[:2]
        mock_db.query.return_value = mock_query
        mock_db.delete = Mock()
        mock_db.commit = Mock()
        
        result = await deduplication_manager._resolve_conflict(
            conflict, policy, uuid4()
        )
        
        assert result['resolved'] is True
        assert result['action'] == 'keep_oldest'
        assert result['chunks_affected'] == 1
        
        # Should have deleted the newer chunk
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_document_reprocessing_deduplication(
        self, deduplication_manager, mock_db, mock_deduplication_service, 
        mock_audit_service, sample_chunks
    ):
        """Test complete document reprocessing deduplication workflow."""
        bot_id = sample_chunks[0].bot_id
        document_id = sample_chunks[0].document_id
        user_id = uuid4()
        
        # Mock bot policy
        with patch.object(deduplication_manager, '_get_bot_policy') as mock_get_policy:
            mock_get_policy.return_value = DeduplicationPolicy()
            
            # Mock old chunk removal
            with patch.object(deduplication_manager, '_remove_old_document_chunks') as mock_remove:
                mock_remove.return_value = 2
                
                # Mock database queries for new chunks
                mock_query = Mock()
                mock_query.filter.return_value = mock_query
                mock_query.all.return_value = sample_chunks
                mock_db.query.return_value = mock_query
                
                # Mock conflict detection
                with patch.object(deduplication_manager, '_detect_conflicts') as mock_detect:
                    mock_detect.return_value = []
                    
                    # Mock deduplication result
                    from app.services.chunk_deduplication_service import DeduplicationResult
                    mock_result = DeduplicationResult(
                        success=True,
                        processed_chunks=4,
                        merged_chunks=1,
                        removed_chunks=0,
                        preserved_chunks=3,
                        decisions=[],
                        audit_trail=[]
                    )
                    mock_deduplication_service.deduplicate_chunks.return_value = mock_result
                    
                    report = await deduplication_manager.process_document_reprocessing_deduplication(
                        bot_id, document_id, user_id
                    )
                    
                    assert report.status == 'completed'
                    assert report.total_chunks_analyzed == len(sample_chunks)
                    assert report.chunks_removed == 2  # Old chunks removed
                    assert report.chunks_merged == 1
                    assert report.processing_time_seconds > 0
    
    @pytest.mark.asyncio
    async def test_manual_conflict_resolution_merge(
        self, deduplication_manager, mock_db, mock_deduplication_service, 
        mock_audit_service, sample_chunks
    ):
        """Test manual conflict resolution with merge action."""
        case_id = str(uuid4())
        user_id = uuid4()
        
        # Create active conflict
        conflict = ConflictResolutionCase(
            case_id=case_id,
            bot_id=sample_chunks[0].bot_id,
            chunk_ids=[sample_chunks[0].id, sample_chunks[1].id],
            similarity_scores=[0.85],
            conflict_type='ambiguous_similarity',
            suggested_action='manual_review',
            confidence_score=0.5,
            created_at=datetime.utcnow()
        )
        
        deduplication_manager.active_conflicts[case_id] = conflict
        
        # Mock database queries - return actual chunks, not mock
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.in_.return_value = sample_chunks[:2]  # Return actual chunks
        mock_db.query.return_value = mock_query
        
        # Mock merge operation
        from app.services.chunk_deduplication_service import DeduplicationDecision
        mock_decision = DeduplicationDecision(
            decision_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            action='merge',
            primary_chunk_id=sample_chunks[0].id,
            duplicate_chunk_ids=[sample_chunks[1].id],
            similarity_score=0.85,
            reason='Manual merge',
            preserved_metadata={},
            source_attribution=[]
        )
        mock_deduplication_service._merge_chunks.return_value = mock_decision
        
        result = await deduplication_manager.manual_conflict_resolution(
            case_id, 'merge', user_id
        )
        
        assert result['success'] is True
        assert result['action'] == 'merge'
        assert conflict.resolved is True
        assert conflict.resolved_by == user_id
        
        # Should have recorded in audit trail
        mock_audit_service.record_deduplication_decision.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_active_conflicts(
        self, deduplication_manager, mock_db, sample_chunks
    ):
        """Test getting active conflicts for a bot."""
        bot_id = sample_chunks[0].bot_id
        case_id = str(uuid4())
        
        # Create active conflict
        conflict = ConflictResolutionCase(
            case_id=case_id,
            bot_id=bot_id,
            chunk_ids=[sample_chunks[0].id, sample_chunks[1].id],
            similarity_scores=[0.85],
            conflict_type='ambiguous_similarity',
            suggested_action='preserve_both',
            confidence_score=0.5,
            created_at=datetime.utcnow()
        )
        
        deduplication_manager.active_conflicts[case_id] = conflict
        
        # Mock database queries - return actual chunks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.in_.return_value = sample_chunks[:2]  # Return actual chunks
        mock_db.query.return_value = mock_query
        
        conflicts = await deduplication_manager.get_active_conflicts(bot_id)
        
        assert len(conflicts) == 1
        assert conflicts[0]['case_id'] == case_id
        assert conflicts[0]['conflict_type'] == 'ambiguous_similarity'
        assert len(conflicts[0]['chunks']) == 2
        assert 'content_preview' in conflicts[0]['chunks'][0]
    
    @pytest.mark.asyncio
    async def test_get_deduplication_statistics_with_conflicts(
        self, deduplication_manager, mock_deduplication_service, mock_audit_service
    ):
        """Test getting comprehensive deduplication statistics."""
        bot_id = uuid4()
        
        # Mock basic statistics
        mock_deduplication_service.get_deduplication_statistics.return_value = {
            'total_chunks': 100,
            'potential_duplicate_chunks': 10
        }
        
        # Mock audit statistics
        mock_audit_service.get_deduplication_statistics.return_value = {
            'total_operations': 5,
            'operations_by_type': {'merge': 3, 'preserve': 2}
        }
        
        # Mock policy
        with patch.object(deduplication_manager, '_get_bot_policy') as mock_get_policy:
            mock_get_policy.return_value = DeduplicationPolicy()
            
            stats = await deduplication_manager.get_deduplication_statistics_with_conflicts(bot_id)
            
            assert 'total_chunks' in stats
            assert 'audit_statistics' in stats
            assert 'conflict_management' in stats
            assert 'policy_configuration' in stats
            assert 'performance_metrics' in stats
            
            assert stats['conflict_management']['active_conflicts'] == 0
            assert stats['policy_configuration']['enabled'] is True
    
    @pytest.mark.asyncio
    async def test_get_bot_policy_default(self, deduplication_manager, mock_db):
        """Test getting default policy when none is configured."""
        bot_id = uuid4()
        
        # Mock bot without policy
        mock_bot = Mock()
        mock_bot.id = bot_id
        mock_bot.deduplication_config = None
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_bot
        mock_db.query.return_value = mock_query
        
        policy = await deduplication_manager._get_bot_policy(bot_id)
        
        # Should return default policy
        assert isinstance(policy, DeduplicationPolicy)
        assert policy.enabled is True
        assert policy.conflict_resolution_strategy == ConflictResolutionStrategy.CONSERVATIVE
    
    @pytest.mark.asyncio
    async def test_get_bot_policy_configured(self, deduplication_manager, mock_db):
        """Test getting configured policy."""
        bot_id = uuid4()
        
        # Mock bot with configured policy
        mock_bot = Mock()
        mock_bot.id = bot_id
        mock_bot.deduplication_config = {
            'enabled': True,
            'similarity_threshold': 0.90,
            'conflict_resolution_strategy': 'aggressive',
            'auto_deduplicate_on_upload': True
        }
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_bot
        mock_db.query.return_value = mock_query
        
        policy = await deduplication_manager._get_bot_policy(bot_id)
        
        assert policy.similarity_threshold == 0.90
        assert policy.conflict_resolution_strategy == ConflictResolutionStrategy.AGGRESSIVE
        assert policy.auto_deduplicate_on_upload is True
    
    @pytest.mark.asyncio
    async def test_error_handling_in_operations(
        self, deduplication_manager, mock_db, mock_deduplication_service
    ):
        """Test error handling in deduplication operations."""
        bot_id = uuid4()
        document_id = uuid4()
        
        # Mock database error
        mock_db.query.side_effect = Exception("Database error")
        
        report = await deduplication_manager.process_document_reprocessing_deduplication(
            bot_id, document_id
        )
        
        assert report.status == 'failed'
        assert report.error_message is not None
        assert "Database error" in report.error_message
        assert report.processing_time_seconds > 0
    
    def test_conflict_resolution_strategies(self):
        """Test all conflict resolution strategies are properly defined."""
        strategies = list(ConflictResolutionStrategy)
        
        expected_strategies = [
            ConflictResolutionStrategy.CONSERVATIVE,
            ConflictResolutionStrategy.AGGRESSIVE,
            ConflictResolutionStrategy.MANUAL,
            ConflictResolutionStrategy.OLDEST_WINS,
            ConflictResolutionStrategy.NEWEST_WINS,
            ConflictResolutionStrategy.LONGEST_WINS
        ]
        
        assert len(strategies) == len(expected_strategies)
        for strategy in expected_strategies:
            assert strategy in strategies


if __name__ == "__main__":
    pytest.main([__file__])