"""
Text processing utilities for document chunking and extraction.
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import PyPDF2
from io import BytesIO

# Try to import python-magic, fall back to mimetypes if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    import mimetypes
    MAGIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class TextChunk:
    """Represents a chunk of text with metadata."""
    
    def __init__(
        self,
        content: str,
        chunk_index: int,
        start_char: int,
        end_char: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.content = content
        self.chunk_index = chunk_index
        self.start_char = start_char
        self.end_char = end_char
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary representation."""
        return {
            "content": self.content,
            "chunk_index": self.chunk_index,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "metadata": self.metadata
        }


class DocumentExtractor:
    """Handles text extraction from various document formats with security checks."""
    
    ALLOWED_MIME_TYPES = {
        'application/pdf': 'pdf',
        'text/plain': 'txt',
        'text/x-python': 'txt',  # Python files as text
        'application/x-empty': 'txt'  # Empty files
    }
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    @classmethod
    def validate_file(cls, file_path: Path, file_content: bytes) -> Tuple[bool, str, str]:
        """
        Validate file type and size with security checks.
        
        Args:
            file_path: Path to the file
            file_content: File content as bytes
            
        Returns:
            Tuple of (is_valid, mime_type, error_message)
        """
        try:
            # Check file size
            if len(file_content) > cls.MAX_FILE_SIZE:
                return False, "", f"File size exceeds maximum allowed size of {cls.MAX_FILE_SIZE} bytes"
            
            # Check file extension
            file_extension = file_path.suffix.lower()
            if file_extension not in ['.pdf', '.txt', '.py', '.md']:
                return False, "", f"Unsupported file extension: {file_extension}"
            
            # Detect MIME type
            if MAGIC_AVAILABLE:
                try:
                    mime_type = magic.from_buffer(file_content, mime=True)
                except Exception as e:
                    logger.warning(f"python-magic failed, falling back to mimetypes: {e}")
                    mime_type, _ = mimetypes.guess_type(str(file_path))
                    mime_type = mime_type or "application/octet-stream"
            else:
                # Fallback to mimetypes module
                mime_type, _ = mimetypes.guess_type(str(file_path))
                if not mime_type:
                    # Basic detection based on file extension
                    if file_extension == '.pdf':
                        mime_type = 'application/pdf'
                    elif file_extension in ['.txt', '.py', '.md']:
                        mime_type = 'text/plain'
                    else:
                        mime_type = 'application/octet-stream'
            
            # Validate MIME type
            if mime_type not in cls.ALLOWED_MIME_TYPES:
                return False, mime_type, f"Unsupported MIME type: {mime_type}"
            
            return True, mime_type, ""
            
        except Exception as e:
            logger.error(f"Error validating file {file_path}: {e}")
            return False, "", f"File validation error: {str(e)}"
    
    @classmethod
    def extract_text(cls, file_content: bytes, mime_type: str, filename: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text from file content based on MIME type.
        
        Args:
            file_content: File content as bytes
            mime_type: MIME type of the file
            filename: Original filename
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        try:
            if mime_type == 'application/pdf':
                return cls._extract_pdf_text(file_content, filename)
            elif mime_type in ['text/plain', 'text/x-python', 'application/x-empty']:
                return cls._extract_text_file(file_content, filename)
            else:
                raise ValueError(f"Unsupported MIME type for extraction: {mime_type}")
                
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {e}")
            raise ValueError(f"Text extraction failed: {str(e)}")
    
    @classmethod
    def _extract_pdf_text(cls, file_content: bytes, filename: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from PDF file."""
        try:
            pdf_file = BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_parts = []
            page_metadata = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_parts.append(page_text)
                        page_metadata.append({
                            "page_number": page_num + 1,
                            "char_start": len("\n".join(text_parts[:-1])) + (1 if text_parts[:-1] else 0),
                            "char_end": len("\n".join(text_parts))
                        })
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num + 1} of {filename}: {e}")
                    continue
            
            full_text = "\n".join(text_parts)
            
            metadata = {
                "total_pages": len(pdf_reader.pages),
                "extracted_pages": len(page_metadata),
                "page_metadata": page_metadata,
                "extraction_method": "PyPDF2"
            }
            
            return full_text, metadata
            
        except Exception as e:
            logger.error(f"PDF extraction failed for {filename}: {e}")
            raise ValueError(f"PDF extraction failed: {str(e)}")
    
    @classmethod
    def _extract_text_file(cls, file_content: bytes, filename: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from plain text file."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    text = file_content.decode(encoding)
                    metadata = {
                        "encoding": encoding,
                        "line_count": len(text.splitlines()),
                        "char_count": len(text)
                    }
                    return text, metadata
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, use utf-8 with error handling
            text = file_content.decode('utf-8', errors='replace')
            metadata = {
                "encoding": "utf-8 (with errors replaced)",
                "line_count": len(text.splitlines()),
                "char_count": len(text)
            }
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"Text file extraction failed for {filename}: {e}")
            raise ValueError(f"Text file extraction failed: {str(e)}")


class TextChunker:
    """Handles intelligent text chunking with configurable parameters."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n\n",
        secondary_separators: Optional[List[str]] = None
    ):
        """
        Initialize text chunker.
        
        Args:
            chunk_size: Target size for each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            separator: Primary separator for splitting text
            secondary_separators: Additional separators to try if primary fails
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
        self.secondary_separators = secondary_separators or ["\n", ". ", "! ", "? ", " "]
        
        # Validate parameters
        if chunk_overlap >= chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")
        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if chunk_overlap < 0:
            raise ValueError("Chunk overlap must be non-negative")
    
    def chunk_text(
        self,
        text: str,
        document_metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """
        Split text into overlapping chunks with intelligent boundary detection.
        
        Args:
            text: Text to chunk
            document_metadata: Optional metadata to include in chunks
            
        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []
        
        # Clean and normalize text
        text = self._normalize_text(text)
        
        # Split text using hierarchical separators
        chunks = self._split_text_hierarchical(text)
        
        # Create TextChunk objects with metadata
        text_chunks = []
        current_pos = 0
        
        for i, chunk_content in enumerate(chunks):
            # Find the actual position of this chunk in the original text
            chunk_start = text.find(chunk_content, current_pos)
            if chunk_start == -1:
                chunk_start = current_pos
            
            chunk_end = chunk_start + len(chunk_content)
            
            # Create metadata for this chunk
            chunk_metadata = {
                "chunk_size": len(chunk_content),
                "word_count": len(chunk_content.split()),
                **(document_metadata or {})
            }
            
            text_chunk = TextChunk(
                content=chunk_content,
                chunk_index=i,
                start_char=chunk_start,
                end_char=chunk_end,
                metadata=chunk_metadata
            )
            
            text_chunks.append(text_chunk)
            current_pos = chunk_start + len(chunk_content) - self.chunk_overlap
        
        return text_chunks
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text by cleaning up whitespace and formatting."""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        text = re.sub(r'\n ', '\n', text)  # Remove spaces after newlines
        text = re.sub(r' \n', '\n', text)  # Remove spaces before newlines
        
        return text.strip()
    
    def _split_text_hierarchical(self, text: str) -> List[str]:
        """Split text using hierarchical separators for better chunk boundaries."""
        # Start with the primary separator
        chunks = self._split_with_overlap(text, self.separator)
        
        # If chunks are too large, try secondary separators
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= self.chunk_size:
                final_chunks.append(chunk)
            else:
                # Try secondary separators
                sub_chunks = self._split_large_chunk(chunk)
                final_chunks.extend(sub_chunks)
        
        return [chunk for chunk in final_chunks if chunk.strip()]
    
    def _split_with_overlap(self, text: str, separator: str) -> List[str]:
        """Split text with overlap using the specified separator."""
        if separator not in text:
            return [text]
        
        parts = text.split(separator)
        chunks = []
        current_chunk = ""
        
        for i, part in enumerate(parts):
            # Add separator back except for the first part
            if i > 0:
                part = separator + part
            
            # If adding this part would exceed chunk size, finalize current chunk
            if current_chunk and len(current_chunk + part) > self.chunk_size:
                chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + part
            else:
                current_chunk += part
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_large_chunk(self, chunk: str) -> List[str]:
        """Split a large chunk using secondary separators."""
        for separator in self.secondary_separators:
            if separator in chunk:
                sub_chunks = self._split_with_overlap(chunk, separator)
                
                # Check if splitting was effective
                if all(len(sub_chunk) <= self.chunk_size * 1.2 for sub_chunk in sub_chunks):
                    return sub_chunks
        
        # If no separator works, split by character count
        return self._split_by_character_count(chunk)
    
    def _split_by_character_count(self, text: str) -> List[str]:
        """Split text by character count as a last resort."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to find a good breaking point near the end
            if end < len(text):
                # Look for whitespace within the last 10% of the chunk
                search_start = max(start + int(self.chunk_size * 0.9), start + 1)
                space_pos = text.rfind(' ', search_start, end)
                
                if space_pos > start:
                    end = space_pos
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = max(end - self.chunk_overlap, start + 1)
        
        return chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of a chunk."""
        if len(text) <= self.chunk_overlap:
            return text
        
        overlap_start = len(text) - self.chunk_overlap
        
        # Try to find a good starting point for overlap (word boundary)
        space_pos = text.find(' ', overlap_start)
        if space_pos != -1 and space_pos < len(text) - self.chunk_overlap // 2:
            overlap_start = space_pos + 1
        
        return text[overlap_start:]


class DocumentProcessor:
    """High-level document processing pipeline."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        max_file_size: int = 50 * 1024 * 1024
    ):
        """
        Initialize document processor.
        
        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks in characters
            max_file_size: Maximum allowed file size in bytes
        """
        self.extractor = DocumentExtractor()
        self.chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.max_file_size = max_file_size
    
    def process_document(
        self,
        file_content: bytes,
        filename: str,
        document_id: str,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[TextChunk], Dict[str, Any]]:
        """
        Process a document through the complete pipeline.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            document_id: Unique document identifier
            additional_metadata: Additional metadata to include
            
        Returns:
            Tuple of (chunks, document_metadata)
        """
        file_path = Path(filename)
        
        # Step 1: Validate file
        is_valid, mime_type, error_msg = self.extractor.validate_file(file_path, file_content)
        if not is_valid:
            raise ValueError(f"File validation failed: {error_msg}")
        
        # Step 2: Extract text
        extracted_text, extraction_metadata = self.extractor.extract_text(
            file_content, mime_type, filename
        )
        
        if not extracted_text.strip():
            raise ValueError("No text content found in document")
        
        # Step 3: Create document metadata
        document_metadata = {
            "document_id": document_id,
            "filename": filename,
            "mime_type": mime_type,
            "file_size": len(file_content),
            "text_length": len(extracted_text),
            "extraction_metadata": extraction_metadata,
            **(additional_metadata or {})
        }
        
        # Step 4: Chunk text
        chunks = self.chunker.chunk_text(extracted_text, document_metadata)
        
        # Step 5: Add chunk-specific metadata
        for chunk in chunks:
            chunk.metadata.update({
                "total_chunks": len(chunks),
                "chunk_ratio": (chunk.chunk_index + 1) / len(chunks)
            })
        
        logger.info(f"Processed document {filename}: {len(chunks)} chunks created")
        
        return chunks, document_metadata
    
    def get_processing_stats(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """Get statistics about processed chunks."""
        if not chunks:
            return {"total_chunks": 0}
        
        chunk_sizes = [len(chunk.content) for chunk in chunks]
        word_counts = [len(chunk.content.split()) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "avg_word_count": sum(word_counts) / len(word_counts),
            "total_words": sum(word_counts),
            "total_characters": sum(chunk_sizes)
        }