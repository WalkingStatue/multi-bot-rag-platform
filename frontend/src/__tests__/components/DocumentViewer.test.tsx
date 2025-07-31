/**
 * Tests for DocumentViewer component
 */


import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import DocumentViewer from '../../components/documents/DocumentViewer';
import * as documentService from '../../services/documentService';

// Mock the document service
vi.mock('../../services/documentService', () => ({
  fetchDocument: vi.fn(),
  searchDocuments: vi.fn(),
  formatFileSize: vi.fn((size) => `${size} bytes`),
  getFileTypeInfo: vi.fn(() => ({ name: 'PDF Document', extension: '.pdf' })),
}));

const mockDocument = {
  id: 'doc-1',
  filename: 'test-document.pdf',
  bot_id: 'bot-1',
  file_size: 1024,
  mime_type: 'application/pdf',
  chunk_count: 3,
  created_at: '2023-01-01T00:00:00Z',
  processing_status: 'processed' as const,
  chunks: [
    {
      id: 'chunk-1',
      chunk_index: 0,
      content_preview: 'This is the first chunk of the document...',
      content_length: 100,
      metadata: { page: 1 },
      created_at: '2023-01-01T00:00:00Z'
    },
    {
      id: 'chunk-2',
      chunk_index: 1,
      content_preview: 'This is the second chunk of the document...',
      content_length: 150,
      metadata: { page: 2 },
      created_at: '2023-01-01T00:00:00Z'
    },
    {
      id: 'chunk-3',
      chunk_index: 2,
      content_preview: 'This is the third chunk of the document...',
      content_length: 120,
      metadata: { page: 3 },
      created_at: '2023-01-01T00:00:00Z'
    }
  ]
};

const mockSearchResults = {
  query: 'test query',
  results: [
    {
      id: 'result-1',
      score: 0.95,
      text: 'This is a search result containing the test query...',
      metadata: { chunk_id: 'chunk-1' }
    }
  ],
  total_results: 1
};

describe('DocumentViewer', () => {
  const mockProps = {
    botId: 'bot-1',
    documentId: 'doc-1',
    onClose: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(documentService.fetchDocument).mockResolvedValue(mockDocument);
    vi.mocked(documentService.searchDocuments).mockResolvedValue(mockSearchResults);
  });

  it('renders loading state initially', () => {
    render(<DocumentViewer {...mockProps} />);
    
    // Should show loading animation
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders document viewer after loading', async () => {
    render(<DocumentViewer {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
      expect(screen.getByText('1024 bytes')).toBeInTheDocument();
      expect(screen.getByText('3 chunks')).toBeInTheDocument();
      expect(screen.getByText('PDF Document')).toBeInTheDocument();
    });
  });

  it('displays document chunks in sidebar', async () => {
    render(<DocumentViewer {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Document Chunks (3)')).toBeInTheDocument();
      expect(screen.getByText('Chunk 1')).toBeInTheDocument();
      expect(screen.getByText('Chunk 2')).toBeInTheDocument();
      expect(screen.getByText('Chunk 3')).toBeInTheDocument();
    });
  });

  it('selects first chunk by default', async () => {
    render(<DocumentViewer {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Chunk 1 of 3')).toBeInTheDocument();
      expect(screen.getByText('This is the first chunk of the document...')).toBeInTheDocument();
    });
  });

  it('navigates between chunks using navigation buttons', async () => {
    render(<DocumentViewer {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Chunk 1 of 3')).toBeInTheDocument();
    });

    // Navigate to next chunk
    const nextButton = screen.getByRole('button', { name: /next/i });
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText('Chunk 2 of 3')).toBeInTheDocument();
      expect(screen.getByText('This is the second chunk of the document...')).toBeInTheDocument();
    });

    // Navigate to previous chunk
    const prevButton = screen.getByRole('button', { name: /prev/i });
    fireEvent.click(prevButton);

    await waitFor(() => {
      expect(screen.getByText('Chunk 1 of 3')).toBeInTheDocument();
    });
  });

  it('selects chunk when clicked in sidebar', async () => {
    render(<DocumentViewer {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Chunk 1 of 3')).toBeInTheDocument();
    });

    // Click on chunk 3 in sidebar
    const chunk3Element = screen.getByText('This is the third chunk of the document...');
    fireEvent.click(chunk3Element.closest('div')!);

    await waitFor(() => {
      expect(screen.getByText('Chunk 3 of 3')).toBeInTheDocument();
      expect(screen.getByText('This is the third chunk of the document...')).toBeInTheDocument();
    });
  });

  it('performs search and displays results', async () => {
    render(<DocumentViewer {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search in document...')).toBeInTheDocument();
    });

    // Enter search query
    const searchInput = screen.getByPlaceholderText('Search in document...');
    fireEvent.change(searchInput, { target: { value: 'test query' } });

    // Click search button
    const searchButton = screen.getByRole('button', { name: /search/i });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(documentService.searchDocuments).toHaveBeenCalledWith(
        'bot-1',
        'test query',
        10,
        'doc-1'
      );
      expect(screen.getByText('Search Results (1)')).toBeInTheDocument();
      expect(screen.getByText('This is a search result containing the test query...')).toBeInTheDocument();
    });
  });

  it('performs search on Enter key press', async () => {
    render(<DocumentViewer {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search in document...')).toBeInTheDocument();
    });

    // Enter search query and press Enter
    const searchInput = screen.getByPlaceholderText('Search in document...');
    fireEvent.change(searchInput, { target: { value: 'test query' } });
    fireEvent.keyPress(searchInput, { key: 'Enter', code: 'Enter' });

    await waitFor(() => {
      expect(documentService.searchDocuments).toHaveBeenCalledWith(
        'bot-1',
        'test query',
        10,
        'doc-1'
      );
    });
  });

  it('displays chunk metadata when available', async () => {
    render(<DocumentViewer {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Chunk 1 of 3')).toBeInTheDocument();
    });

    // Should show metadata section
    expect(screen.getByText('Metadata')).toBeInTheDocument();
    expect(screen.getByText('"page": 1')).toBeInTheDocument();
  });

  it('closes viewer when close button is clicked', async () => {
    render(<DocumentViewer {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
    });

    // Click close button
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);

    expect(mockProps.onClose).toHaveBeenCalled();
  });

  it('handles document loading error', async () => {
    vi.mocked(documentService.fetchDocument).mockRejectedValue(new Error('Failed to load'));
    
    render(<DocumentViewer {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load document details.')).toBeInTheDocument();
    });
  });

  it('handles search error', async () => {
    vi.mocked(documentService.searchDocuments).mockRejectedValue(new Error('Search failed'));
    
    render(<DocumentViewer {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search in document...')).toBeInTheDocument();
    });

    // Perform search
    const searchInput = screen.getByPlaceholderText('Search in document...');
    fireEvent.change(searchInput, { target: { value: 'test query' } });
    
    const searchButton = screen.getByRole('button', { name: /search/i });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText('Search failed. Please try again.')).toBeInTheDocument();
    });
  });

  it('disables navigation buttons at boundaries', async () => {
    render(<DocumentViewer {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Chunk 1 of 3')).toBeInTheDocument();
    });

    // Previous button should be disabled on first chunk
    const prevButton = screen.getByRole('button', { name: /prev/i });
    expect(prevButton).toBeDisabled();

    // Navigate to last chunk
    const nextButton = screen.getByRole('button', { name: /next/i });
    fireEvent.click(nextButton); // Go to chunk 2
    fireEvent.click(nextButton); // Go to chunk 3

    await waitFor(() => {
      expect(screen.getByText('Chunk 3 of 3')).toBeInTheDocument();
    });

    // Next button should be disabled on last chunk
    expect(nextButton).toBeDisabled();
  });
});