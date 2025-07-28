"""
Unit tests for text processing utilities.
"""
import pytest
from pathlib import Path
from io import BytesIO
import PyPDF2

from app.utils.text_processing import (
    DocumentExtractor,
    TextChunker,
    TextChunk,
    DocumentProcessor
)


class TestDocumentExtractor:
    """Test cases for DocumentExtractor."""
    
    def test_validate_file_valid_txt(self):
        """Test validation of valid text file."""
        content = b"This is a test text file."
        file_path = Path("test.txt")
        
        is_valid, mime_type, error = DocumentExtractor.validate_file(file_path, content)
        
        assert is_valid is True
        assert mime_type == "text/plain"
        assert error == ""
    
    def test_validate_file_invalid_extension(self):
        """Test validation of invalid file extension."""
        content = b"This is a test file."
        file_path = Path("test.exe")
        
        is_valid, mime_type, error = DocumentExtractor.validate_file(file_path, content)
        
        assert is_valid is False
        assert "Unsupported file extension" in error
    
    def test_validate_file_too_large(self):
        """Test validation of file that's too large."""
        # Create content larger than max size
        content = b"x" * (DocumentExtractor.MAX_FILE_SIZE + 1)
        file_path = Path("test.txt")
        
        is_valid, mime_type, error = DocumentExtractor.validate_file(file_path, content)
        
        assert is_valid is False
        assert "File size exceeds maximum" in error
    
    def test_extract_text_from_plain_text(self):
        """Test text extraction from plain text file."""
        content = b"This is a test text file.\nWith multiple lines."
        
        text, metadata = DocumentExtractor.extract_text(content, "text/plain", "test.txt")
        
        assert text == "This is a test text file.\nWith multiple lines."
        assert metadata["encoding"] == "utf-8"
        assert metadata["line_count"] == 2
        assert metadata["char_count"] == len(text)
    
    def test_extract_text_from_utf16(self):
        """Test text extraction from UTF-16 encoded file."""
        original_text = "This is a UTF-16 test file."
        content = original_text.encode('utf-16')
        
        text, metadata = DocumentExtractor.extract_text(content, "text/plain", "test.txt")
        
        assert text == original_text
        assert metadata["encoding"] == "utf-16"
    
    def test_extract_text_invalid_encoding(self):
        """Test text extraction with invalid encoding (should use replacement)."""
        # Create invalid UTF-8 bytes that can't be decoded by common encodings
        content = b'\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f'
        
        text, metadata = DocumentExtractor.extract_text(content, "text/plain", "test.txt")
        
        # Should successfully decode with some encoding (latin-1 can decode any byte sequence)
        assert len(text) > 0  # Should have some content
        assert "encoding" in metadata
    
    def test_extract_text_unsupported_mime_type(self):
        """Test text extraction with unsupported MIME type."""
        content = b"Some content"
        
        with pytest.raises(ValueError, match="Unsupported MIME type"):
            DocumentExtractor.extract_text(content, "application/unknown", "test.unknown")


class TestTextChunker:
    """Test cases for TextChunker."""
    
    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        text = "This is a test. " * 100  # Create text longer than default chunk size
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) > 1
        assert all(isinstance(chunk, TextChunk) for chunk in chunks)
        assert all(len(chunk.content) <= 120 for chunk in chunks)  # Allow some flexibility
    
    def test_chunk_text_with_overlap(self):
        """Test that chunks have proper overlap."""
        text = "Word1 Word2 Word3 Word4 Word5 Word6 Word7 Word8 Word9 Word10"
        chunker = TextChunker(chunk_size=30, chunk_overlap=10)
        
        chunks = chunker.chunk_text(text)
        
        if len(chunks) > 1:
            # Check that there's some overlap between consecutive chunks
            for i in range(len(chunks) - 1):
                current_chunk = chunks[i].content
                next_chunk = chunks[i + 1].content
                
                # Find common words (simple overlap check)
                current_words = set(current_chunk.split())
                next_words = set(next_chunk.split())
                overlap_words = current_words.intersection(next_words)
                
                # Should have some overlapping words
                assert len(overlap_words) > 0 or len(current_chunk) < chunker.chunk_size
    
    def test_chunk_text_empty(self):
        """Test chunking empty text."""
        chunker = TextChunker()
        
        chunks = chunker.chunk_text("")
        
        assert chunks == []
    
    def test_chunk_text_short(self):
        """Test chunking text shorter than chunk size."""
        text = "Short text."
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].chunk_index == 0
    
    def test_chunk_text_with_separators(self):
        """Test chunking with different separators."""
        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        chunker = TextChunker(chunk_size=20, chunk_overlap=5, separator="\n\n")
        
        chunks = chunker.chunk_text(text)
        
        # Should split on paragraph boundaries
        assert len(chunks) >= 2
        assert all("Paragraph" in chunk.content for chunk in chunks)
    
    def test_chunk_text_metadata(self):
        """Test that chunk metadata is properly set."""
        text = "This is a test text for metadata checking."
        doc_metadata = {"document_id": "test-123", "source": "test"}
        chunker = TextChunker()
        
        chunks = chunker.chunk_text(text, doc_metadata)
        
        assert len(chunks) == 1
        chunk = chunks[0]
        
        assert chunk.chunk_index == 0
        assert chunk.start_char >= 0
        assert chunk.end_char > chunk.start_char
        assert chunk.metadata["document_id"] == "test-123"
        assert chunk.metadata["source"] == "test"
        assert "chunk_size" in chunk.metadata
        assert "word_count" in chunk.metadata
    
    def test_chunk_text_invalid_parameters(self):
        """Test chunker with invalid parameters."""
        with pytest.raises(ValueError, match="Chunk overlap must be less than chunk size"):
            TextChunker(chunk_size=100, chunk_overlap=100)
        
        with pytest.raises(ValueError, match="Chunk overlap must be less than chunk size"):
            TextChunker(chunk_size=0, chunk_overlap=200)  # Default overlap is 200
        
        with pytest.raises(ValueError, match="Chunk overlap must be non-negative"):
            TextChunker(chunk_size=1000, chunk_overlap=-1)
    
    def test_normalize_text(self):
        """Test text normalization."""
        chunker = TextChunker()
        
        # Test multiple newlines
        text = "Line 1\n\n\n\nLine 2"
        normalized = chunker._normalize_text(text)
        assert normalized == "Line 1\n\nLine 2"
        
        # Test multiple spaces
        text = "Word1    Word2\t\tWord3"
        normalized = chunker._normalize_text(text)
        assert normalized == "Word1 Word2 Word3"
        
        # Test spaces around newlines
        text = "Line 1 \n Line 2"
        normalized = chunker._normalize_text(text)
        assert normalized == "Line 1\nLine 2"
    
    def test_split_large_chunk(self):
        """Test splitting of large chunks using secondary separators."""
        # Create a chunk with no primary separator but with secondary separators
        text = "Sentence 1. Sentence 2. Sentence 3. Sentence 4. Sentence 5."
        chunker = TextChunker(chunk_size=30, chunk_overlap=5, separator="\n\n")  # Won't find this separator
        
        chunks = chunker._split_large_chunk(text)
        
        # Should split on sentence boundaries (". ")
        assert len(chunks) > 1
        assert all(len(chunk) <= 36 for chunk in chunks)  # Allow some flexibility
    
    def test_character_count_splitting(self):
        """Test fallback to character count splitting."""
        # Create text with no good separators
        text = "a" * 200  # Long text with no separators
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        
        chunks = chunker._split_by_character_count(text)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 50 for chunk in chunks)
        
        # Check overlap
        for i in range(len(chunks) - 1):
            current_end = chunks[i][-10:]  # Last 10 chars
            next_start = chunks[i + 1][:10]  # First 10 chars
            # Should have some overlap
            assert len(set(current_end).intersection(set(next_start))) > 0


class TestTextChunk:
    """Test cases for TextChunk class."""
    
    def test_text_chunk_creation(self):
        """Test TextChunk creation and properties."""
        content = "This is a test chunk."
        metadata = {"test": "value"}
        
        chunk = TextChunk(
            content=content,
            chunk_index=0,
            start_char=10,
            end_char=30,
            metadata=metadata
        )
        
        assert chunk.content == content
        assert chunk.chunk_index == 0
        assert chunk.start_char == 10
        assert chunk.end_char == 30
        assert chunk.metadata == metadata
    
    def test_text_chunk_to_dict(self):
        """Test TextChunk to_dict method."""
        chunk = TextChunk(
            content="Test content",
            chunk_index=1,
            start_char=5,
            end_char=15,
            metadata={"key": "value"}
        )
        
        chunk_dict = chunk.to_dict()
        
        expected = {
            "content": "Test content",
            "chunk_index": 1,
            "start_char": 5,
            "end_char": 15,
            "metadata": {"key": "value"}
        }
        
        assert chunk_dict == expected
    
    def test_text_chunk_default_metadata(self):
        """Test TextChunk with default metadata."""
        chunk = TextChunk("Content", 0, 0, 7)
        
        assert chunk.metadata == {}


class TestDocumentProcessor:
    """Test cases for DocumentProcessor."""
    
    def test_process_document_text_file(self):
        """Test processing a text document."""
        content = b"This is a test document.\nWith multiple lines.\nFor testing purposes."
        processor = DocumentProcessor(chunk_size=30, chunk_overlap=10)
        
        chunks, doc_metadata = processor.process_document(
            file_content=content,
            filename="test.txt",
            document_id="doc-123",
            additional_metadata={"source": "test"}
        )
        
        assert len(chunks) >= 1
        assert all(isinstance(chunk, TextChunk) for chunk in chunks)
        
        # Check document metadata
        assert doc_metadata["document_id"] == "doc-123"
        assert doc_metadata["filename"] == "test.txt"
        assert doc_metadata["mime_type"] == "text/plain"
        assert doc_metadata["file_size"] == len(content)
        assert doc_metadata["source"] == "test"
        assert "extraction_metadata" in doc_metadata
        
        # Check chunk metadata
        for chunk in chunks:
            assert chunk.metadata["document_id"] == "doc-123"
            assert chunk.metadata["total_chunks"] == len(chunks)
            assert "chunk_ratio" in chunk.metadata
    
    def test_process_document_invalid_file(self):
        """Test processing invalid document."""
        content = b"Some content"
        processor = DocumentProcessor()
        
        with pytest.raises(ValueError, match="File validation failed"):
            processor.process_document(
                file_content=content,
                filename="test.exe",  # Invalid extension
                document_id="doc-123"
            )
    
    def test_process_document_empty_content(self):
        """Test processing document with no extractable text."""
        content = b""  # Empty content
        processor = DocumentProcessor()
        
        with pytest.raises(ValueError, match="No text content found"):
            processor.process_document(
                file_content=content,
                filename="test.txt",
                document_id="doc-123"
            )
    
    def test_get_processing_stats(self):
        """Test getting processing statistics."""
        processor = DocumentProcessor()
        
        # Create mock chunks
        chunks = [
            TextChunk("Short chunk", 0, 0, 11),
            TextChunk("This is a longer chunk with more words", 1, 12, 50),
            TextChunk("Medium length chunk", 2, 51, 70)
        ]
        
        stats = processor.get_processing_stats(chunks)
        
        assert stats["total_chunks"] == 3
        assert stats["min_chunk_size"] == 11
        assert stats["max_chunk_size"] == 38
        assert stats["avg_chunk_size"] > 0
        assert stats["total_words"] > 0
        assert stats["avg_word_count"] > 0
        assert stats["total_characters"] > 0
    
    def test_get_processing_stats_empty(self):
        """Test getting statistics for empty chunk list."""
        processor = DocumentProcessor()
        
        stats = processor.get_processing_stats([])
        
        assert stats == {"total_chunks": 0}
    
    def test_custom_chunk_parameters(self):
        """Test processor with custom chunking parameters."""
        content = b"Word " * 100  # Create long content
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=15)
        
        chunks, _ = processor.process_document(
            file_content=content,
            filename="test.txt",
            document_id="doc-123"
        )
        
        # Should create multiple chunks with the specified parameters
        assert len(chunks) > 1
        assert all(len(chunk.content) <= 65 for chunk in chunks)  # Allow some flexibility


class TestIntegration:
    """Integration tests for the complete text processing pipeline."""
    
    def test_full_pipeline_text_document(self):
        """Test the complete pipeline with a text document."""
        # Create a realistic text document
        content = b"""
        Introduction
        
        This is a comprehensive test document that contains multiple paragraphs
        and sections to test the complete document processing pipeline.
        
        Section 1: Overview
        
        This section provides an overview of the document processing system.
        It includes text extraction, chunking, and metadata management.
        
        Section 2: Implementation Details
        
        The implementation uses various techniques for optimal text processing:
        - Intelligent chunking with overlap
        - Multiple encoding support
        - Metadata preservation
        - Error handling and validation
        
        Conclusion
        
        This document demonstrates the capabilities of the text processing system
        and serves as a comprehensive test case for validation.
        """
        
        processor = DocumentProcessor(chunk_size=200, chunk_overlap=50)
        
        chunks, doc_metadata = processor.process_document(
            file_content=content,
            filename="comprehensive_test.txt",
            document_id="integration-test-123",
            additional_metadata={"test_type": "integration"}
        )
        
        # Validate results
        assert len(chunks) >= 2  # Should create multiple chunks
        assert doc_metadata["document_id"] == "integration-test-123"
        assert doc_metadata["test_type"] == "integration"
        
        # Validate chunks
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            assert len(chunk.content) > 0
            assert chunk.metadata["document_id"] == "integration-test-123"
            assert chunk.metadata["total_chunks"] == len(chunks)
            assert 0 < chunk.metadata["chunk_ratio"] <= 1
        
        # Validate overlap (if multiple chunks)
        if len(chunks) > 1:
            for i in range(len(chunks) - 1):
                current_words = set(chunks[i].content.split())
                next_words = set(chunks[i + 1].content.split())
                overlap = current_words.intersection(next_words)
                # Should have some overlap or be at natural boundaries
                assert len(overlap) > 0 or chunks[i].content.endswith(('.', '!', '?', '\n'))
        
        # Get and validate statistics
        stats = processor.get_processing_stats(chunks)
        assert stats["total_chunks"] == len(chunks)
        assert stats["total_characters"] > 0
        assert stats["total_words"] > 0
        assert stats["avg_chunk_size"] > 0
    
    def test_edge_cases(self):
        """Test various edge cases in document processing."""
        processor = DocumentProcessor()
        
        # Test with only whitespace
        with pytest.raises(ValueError):
            processor.process_document(b"   \n\n\t  ", "whitespace.txt", "test-1")
        
        # Test with very short content
        chunks, metadata = processor.process_document(
            b"Hi!", "short.txt", "test-2"
        )
        assert len(chunks) == 1
        assert chunks[0].content == "Hi!"
        
        # Test with special characters
        content = "Special chars: àáâãäåæçèéêë ñòóôõö ùúûüý ÿ"
        chunks, metadata = processor.process_document(
            content.encode('utf-8'), "special.txt", "test-3"
        )
        assert len(chunks) == 1
        assert "àáâãäåæçèéêë" in chunks[0].content