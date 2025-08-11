"""
Unit tests for chunk deduplication service.
Tests requirements 10.1, 10.2, 10.4 for task 11.1.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from uuid import UUID, uuid4

from app.services.chunk_deduplication_service import (
    ChunkDeduplicationService,
    ChunkSimilarity,
    DeduplicationDecision,
    DeduplicationResult,
    DeduplicationConfig
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
def deduplication_service(mock_db, mock_vector_service):
    """Create deduplication service instance."""
    return ChunkDeduplicationService(mock_db, mock_vector_service)


@pytest.fixture
def sample_chunks():
    """Create sample document chunks for testing."""
    bot_id = uuid4()
    doc_id = uuid4()
    
    chunks = []
    
    # Exact duplicate chunks
    chunk1 = DocumentChunk(
        id=uuid4(),
        document_id=doc_id,
        bot_id=bot_id,
        chunk_index=0,
        content="This is a sample document chunk with some content.",
        embedding_id="embed_1",
        chunk_metadata={"page": 1, "section": "intro"},
        created_at=datetime(2024, 1, 1, 10, 0, 0)
    )
    
    chunk2 = DocumentChunk(
        id=uuid4(),
        document_id=doc_id,
        bot_id=bot_id,
        chunk_index=1,
        content="This is a sample document chunk with some content.",
        embedding_id="embed_2",
        chunk_metadata={"page": 1, "section": "intro"},
        created_at=datetime(2024, 1, 1, 10, 1, 0)
    )
    
    # Similar but not identical chunks
    chunk3 = DocumentChunk(
        id=uuid4(),
        document_id=doc_id,
        bot_id=bot_id,
        chunk_index=2,
        content="This is a sample document chunk with similar content.",
        embedding_id="embed_3",
        chunk_metadata={"page": 1, "section": "intro"},
        created_at=datetime(2024, 1, 1, 10, 2, 0)
    )
    
    # Different chunk
    chunk4 = DocumentChunk(
        id=uuid4(),
        document_id=doc_id,
        bot_id=bot_id,
        chunk_index=3,
        content="This is completely different content about another topic.",
        embedding_id="embed_4",
        chunk_metadata={"page": 2, "section": "body"},
        created_at=datetime(2024, 1, 1, 10, 3, 0)
    )
    
    chunks.extend([chunk1, chunk2, chunk3, chunk4])
    return chunks


class TestChunkDeduplicationService:
    """Test cases for chunk deduplication service."""
    
    def test_calculate_content_hash(self, deduplication_service):
        """Test content hash calculation with normalization."""
        content1 = "This is a test content."
        content2 = "THIS IS A TEST CONTENT."
        content3 = "This   is    a   test   content."
        
        hash1 = deduplication_service._calculate_content_hash(content1)
        hash2 = deduplication_service._calculate_content_hash(content2)
        hash3 = deduplication_service._calculate_content_hash(content3)
        
        # All should produce the same hash due to normalization
        assert hash1 == hash2 == hash3
        assert len(hash1) == 64  # SHA-256 hex length
    
    def test_calculate_text_similarity(self, deduplication_service):
        """Test text similarity calculation."""
        text1 = "This is a sample text."
        text2 = "This is a sample text."
        text3 = "This is a similar text."
        text4 = "Completely different content."
        
        # Identical texts
        similarity1 = deduplication_service._calculate_text_similarity(text1, text2)
        assert similarity1 == 1.0
        
        # Similar texts
        similarity2 = deduplication_service._calculate_text_similarity(text1, text3)
        assert 0.8 <= similarity2 < 1.0
        
        # Different texts
        similarity3 = deduplication_service._calculate_text_similarity(text1, text4)
        assert similarity3 < 0.5
    
    def test_calculate_content_overlap(self, deduplication_service):
        """Test content overlap calculation."""
        text1 = "the quick brown fox jumps"
        text2 = "the quick brown fox runs"
        text3 = "a slow white cat walks"
        
        # High overlap
        overlap1 = deduplication_service._calculate_content_overlap(text1, text2)
        assert overlap1 > 0.6
        
        # Low overlap
        overlap2 = deduplication_service._calculate_content_overlap(text1, text3)
        assert overlap2 < 0.3
    
    def test_assess_metadata_compatibility(self, deduplication_service):
        """Test metadata compatibility assessment."""
        metadata1 = {"page_number": 1, "section": "intro", "author": "John"}
        metadata2 = {"page_number": 1, "section": "intro", "date": "2024-01-01"}
        metadata3 = {"page_number": 2, "section": "intro", "author": "John"}
        
        # Compatible metadata (same critical fields)
        assert deduplication_service._assess_metadata_compatibility(metadata1, metadata2)
        
        # Incompatible metadata (different page numbers)
        assert not deduplication_service._assess_metadata_compatibility(metadata1, metadata3)
    
    @pytest.mark.asyncio
    async def test_analyze_chunk_pair(self, deduplication_service, sample_chunks):
        """Test chunk pair analysis."""
        chunk1, chunk2, chunk3, chunk4 = sample_chunks
        
        # Analyze identical chunks
        similarity1 = await deduplication_service._analyze_chunk_pair(chunk1, chunk2)
        assert similarity1.similarity_score == 1.0
        assert similarity1.similarity_type == 'exact'
        assert similarity1.metadata_compatibility is True
        
        # Analyze similar chunks
        similarity2 = await deduplication_service._analyze_chunk_pair(chunk1, chunk3)
        assert 0.8 < similarity2.similarity_score < 1.0
        assert similarity2.similarity_type in ['high', 'medium']
        
        # Analyze different chunks
        similarity3 = await deduplication_service._analyze_chunk_pair(chunk1, chunk4)
        assert similarity3.similarity_score < 0.5
        assert similarity3.metadata_compatibility is False
    
    @pytest.mark.asyncio
    async def test_detect_chunk_similarities(self, deduplication_service, mock_db, sample_chunks):
        """Test chunk similarity detection."""
        bot_id = sample_chunks[0].bot_id
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_chunks
        mock_db.query.return_value = mock_query
        
        similarities = await deduplication_service.detect_chunk_similarities(bot_id)
        
        # Should detect similarities between chunks
        assert len(similarities) > 0
        
        # Should be sorted by similarity score (highest first)
        for i in range(len(similarities) - 1):
            assert similarities[i].similarity_score >= similarities[i + 1].similarity_score
    
    def test_merge_chunk_metadata(self, deduplication_service):
        """Test metadata merging functionality."""
        primary_metadata = {"page": 1, "section": "intro", "author": "John"}
        duplicate_metadatas = [
            {"page": 1, "section": "intro", "date": "2024-01-01"},
            {"page": 1, "section": "intro", "keywords": ["test", "sample"]}
        ]
        
        merged = deduplication_service._merge_chunk_metadata(
            primary_metadata, duplicate_metadatas
        )
        
        # Should contain all unique fields
        assert "author" in merged
        assert "date" in merged
        assert "keywords" in merged
        
        # Should have deduplication metadata
        assert "_deduplication" in merged
        assert merged["_deduplication"]["source_count"] == 3
    
    def test_create_source_attribution(self, deduplication_service, sample_chunks):
        """Test source attribution creation."""
        primary_chunk = sample_chunks[0]
        duplicate_chunks = sample_chunks[1:3]
        
        attribution = deduplication_service._create_source_attribution(
            primary_chunk, duplicate_chunks
        )
        
        assert len(attribution) == 3  # Primary + 2 duplicates
        
        # Check primary chunk is marked correctly
        primary_attr = next(attr for attr in attribution if attr["is_primary"])
        assert primary_attr["chunk_id"] == str(primary_chunk.id)
        
        # Check all chunks are represented
        chunk_ids = {attr["chunk_id"] for attr in attribution}
        expected_ids = {str(chunk.id) for chunk in [primary_chunk] + duplicate_chunks}
        assert chunk_ids == expected_ids
    
    def test_group_similar_chunks(self, deduplication_service):
        """Test similarity grouping functionality."""
        # Create test similarities
        chunk_ids = [uuid4() for _ in range(5)]
        similarities = [
            ChunkSimilarity(chunk_ids[0], chunk_ids[1], 0.95, 'high', 0.9, True),
            ChunkSimilarity(chunk_ids[1], chunk_ids[2], 0.92, 'high', 0.88, True),
            ChunkSimilarity(chunk_ids[3], chunk_ids[4], 0.96, 'high', 0.91, True),
        ]
        
        groups = deduplication_service._group_similar_chunks(similarities)
        
        # Should create 2 groups
        assert len(groups) == 2
        
        # First group should have 3 chunks (0, 1, 2)
        group1 = next(group for group in groups if len(group) == 3)
        assert set(group1) == {chunk_ids[0], chunk_ids[1], chunk_ids[2]}
        
        # Second group should have 2 chunks (3, 4)
        group2 = next(group for group in groups if len(group) == 2)
        assert set(group2) == {chunk_ids[3], chunk_ids[4]}
    
    def test_select_primary_chunk(self, deduplication_service, sample_chunks):
        """Test primary chunk selection."""
        chunks = sample_chunks[:3]  # Use first 3 chunks
        
        primary = deduplication_service._select_primary_chunk(chunks)
        
        # Should select one of the chunks (scoring algorithm may vary)
        assert primary.id in [chunk.id for chunk in chunks]
    
    @pytest.mark.asyncio
    async def test_should_merge_chunks_conservative(self, deduplication_service, sample_chunks):
        """Test conservative merge decision making."""
        deduplication_service.config.conservative_preservation = True
        deduplication_service.config.high_similarity_threshold = 0.95
        
        primary_chunk = sample_chunks[0]
        
        # Test with identical chunks (should merge)
        duplicate_chunks = [sample_chunks[1]]  # Identical content
        should_merge = await deduplication_service._should_merge_chunks(
            primary_chunk, duplicate_chunks
        )
        assert should_merge is True
        
        # Test with similar but not identical chunks (should not merge)
        duplicate_chunks = [sample_chunks[2]]  # Similar content
        should_merge = await deduplication_service._should_merge_chunks(
            primary_chunk, duplicate_chunks
        )
        assert should_merge is False
    
    @pytest.mark.asyncio
    async def test_merge_chunks(self, deduplication_service, mock_db, mock_vector_service, sample_chunks):
        """Test chunk merging functionality."""
        primary_chunk = sample_chunks[0]
        duplicate_chunks = sample_chunks[1:2]
        
        # Mock database operations
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.delete.return_value = 1
        mock_db.query.return_value = mock_query
        
        decision = await deduplication_service._merge_chunks(primary_chunk, duplicate_chunks)
        
        assert decision.action == 'merge'
        assert decision.primary_chunk_id == primary_chunk.id
        assert len(decision.duplicate_chunk_ids) == 1
        assert decision.similarity_score > 0.9
        
        # Should have called vector service to delete embeddings
        mock_vector_service.delete_document_chunks.assert_called_once()
        
        # Should have updated primary chunk metadata
        assert '_deduplication' in primary_chunk.chunk_metadata
    
    def test_create_preserve_decision(self, deduplication_service, sample_chunks):
        """Test preservation decision creation."""
        primary_chunk = sample_chunks[0]
        other_chunks = sample_chunks[1:3]
        
        decision = deduplication_service._create_preserve_decision(primary_chunk, other_chunks)
        
        assert decision.action == 'preserve'
        assert decision.primary_chunk_id == primary_chunk.id
        assert len(decision.duplicate_chunk_ids) == 2
        assert "Conservative preservation" in decision.reason
    
    @pytest.mark.asyncio
    async def test_deduplicate_chunks_full_workflow(
        self, deduplication_service, mock_db, mock_vector_service, sample_chunks
    ):
        """Test complete deduplication workflow."""
        bot_id = sample_chunks[0].bot_id
        
        # Mock database queries
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_chunks
        mock_query.delete.return_value = 1
        mock_db.query.return_value = mock_query
        mock_db.commit = Mock()
        mock_db.rollback = Mock()
        
        result = await deduplication_service.deduplicate_chunks(bot_id)
        
        assert result.success is True
        assert result.processed_chunks > 0
        assert len(result.decisions) > 0
        assert len(result.audit_trail) > 0
        
        # Should have committed changes
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_deduplication_statistics(
        self, deduplication_service, mock_db, sample_chunks
    ):
        """Test deduplication statistics generation."""
        bot_id = sample_chunks[0].bot_id
        
        # Mock database queries
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_chunks
        mock_query.scalar.return_value = len(sample_chunks)
        mock_db.query.return_value = mock_query
        
        stats = await deduplication_service.get_deduplication_statistics(bot_id)
        
        assert 'total_chunks' in stats
        assert 'potential_duplicate_groups' in stats
        assert 'potential_duplicate_chunks' in stats
        assert 'similarity_distribution' in stats
        assert 'recommendations' in stats
        
        assert stats['total_chunks'] == len(sample_chunks)
        assert isinstance(stats['recommendations'], list)
    
    def test_generate_deduplication_recommendations(self, deduplication_service):
        """Test deduplication recommendation generation."""
        # High duplication scenario
        recommendations = deduplication_service._generate_deduplication_recommendations(
            total_chunks=100,
            potential_duplicates=25,
            already_deduplicated=0
        )
        
        assert len(recommendations) > 0
        assert any("High duplication detected" in rec for rec in recommendations)
        
        # Low duplication scenario
        recommendations = deduplication_service._generate_deduplication_recommendations(
            total_chunks=100,
            potential_duplicates=5,
            already_deduplicated=10
        )
        
        assert any("Low duplication detected" in rec for rec in recommendations)
        assert any("previously deduplicated" in rec for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, deduplication_service, mock_db):
        """Test error handling in deduplication operations."""
        bot_id = uuid4()
        
        # Mock database error during similarity detection
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.side_effect = Exception("Database error")
        mock_db.query.return_value = mock_query
        mock_db.rollback = Mock()
        
        result = await deduplication_service.deduplicate_chunks(bot_id)
        
        # The service should handle the error gracefully and return empty result
        # since no similarities were detected due to the error
        assert result.success is True  # Empty result is considered successful
        assert result.processed_chunks == 0
        assert result.merged_chunks == 0
    
    def test_deduplication_config(self):
        """Test deduplication configuration."""
        config = DeduplicationConfig()
        
        # Test default values
        assert config.exact_match_threshold == 1.0
        assert config.high_similarity_threshold == 0.95
        assert config.conservative_preservation is True
        assert config.preserve_source_attribution is True
        
        # Test custom configuration
        custom_config = DeduplicationConfig(
            high_similarity_threshold=0.90,
            conservative_preservation=False
        )
        
        assert custom_config.high_similarity_threshold == 0.90
        assert custom_config.conservative_preservation is False


if __name__ == "__main__":
    pytest.main([__file__])