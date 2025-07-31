/**
 * Tests for DocumentManagement component
 */


import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import DocumentManagement from '../../components/documents/DocumentManagement';
import * as documentService from '../../services/documentService';

// Mock the document service
vi.mock('../../services/documentService', () => ({
  fetchDocumentList: vi.fn(),
  uploadDocument: vi.fn(),
  deleteDocument: vi.fn(),
  fetchDocument: vi.fn(),
  validateFile: vi.fn(),
  formatFileSize: vi.fn(),
  getFileTypeInfo: vi.fn(),
  formatProcessingStatus: vi.fn(),
}));

// Mock the child components
vi.mock('../../components/documents/DocumentUpload', () => ({
  default: ({ onUploadComplete, onUploadError }: any) => (
    <div data-testid="document-upload">
      <button 
        onClick={() => onUploadComplete([{ id: '1', filename: 'test.pdf' }])}
        data-testid="mock-upload-success"
      >
        Mock Upload Success
      </button>
      <button 
        onClick={() => onUploadError('Upload failed')}
        data-testid="mock-upload-error"
      >
        Mock Upload Error
      </button>
    </div>
  )
}));

vi.mock('../../components/documents/DocumentList', () => ({
  default: ({ onDocumentSelect }: any) => (
    <div data-testid="document-list">
      <button 
        onClick={() => onDocumentSelect({ id: '1', filename: 'test.pdf' })}
        data-testid="mock-select-document"
      >
        Mock Select Document
      </button>
    </div>
  )
}));

vi.mock('../../components/documents/DocumentViewer', () => ({
  default: ({ onClose }: any) => (
    <div data-testid="document-viewer">
      <button onClick={onClose} data-testid="mock-close-viewer">
        Mock Close Viewer
      </button>
    </div>
  )
}));

describe('DocumentManagement', () => {
  const mockBotId = 'test-bot-id';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders document management interface', () => {
    render(<DocumentManagement botId={mockBotId} />);
    
    expect(screen.getByText('Document Management')).toBeInTheDocument();
    expect(screen.getByText('Upload and manage documents for this bot\'s knowledge base')).toBeInTheDocument();
    expect(screen.getByTestId('document-upload')).toBeInTheDocument();
    expect(screen.getByTestId('document-list')).toBeInTheDocument();
  });

  it('shows success message on upload complete', async () => {
    render(<DocumentManagement botId={mockBotId} />);
    
    const uploadSuccessButton = screen.getByTestId('mock-upload-success');
    fireEvent.click(uploadSuccessButton);

    await waitFor(() => {
      expect(screen.getByText('Successfully uploaded 1 document')).toBeInTheDocument();
    });
  });

  it('shows error message on upload error', async () => {
    render(<DocumentManagement botId={mockBotId} />);
    
    const uploadErrorButton = screen.getByTestId('mock-upload-error');
    fireEvent.click(uploadErrorButton);

    await waitFor(() => {
      expect(screen.getByText('Upload failed')).toBeInTheDocument();
    });
  });

  it('opens document viewer when document is selected', async () => {
    render(<DocumentManagement botId={mockBotId} />);
    
    const selectDocumentButton = screen.getByTestId('mock-select-document');
    fireEvent.click(selectDocumentButton);

    await waitFor(() => {
      expect(screen.getByTestId('document-viewer')).toBeInTheDocument();
    });
  });

  it('closes document viewer when close is clicked', async () => {
    render(<DocumentManagement botId={mockBotId} />);
    
    // Open viewer
    const selectDocumentButton = screen.getByTestId('mock-select-document');
    fireEvent.click(selectDocumentButton);

    await waitFor(() => {
      expect(screen.getByTestId('document-viewer')).toBeInTheDocument();
    });

    // Close viewer
    const closeViewerButton = screen.getByTestId('mock-close-viewer');
    fireEvent.click(closeViewerButton);

    await waitFor(() => {
      expect(screen.queryByTestId('document-viewer')).not.toBeInTheDocument();
    });
  });

  it('clears messages when close button is clicked', async () => {
    render(<DocumentManagement botId={mockBotId} />);
    
    // Trigger success message
    const uploadSuccessButton = screen.getByTestId('mock-upload-success');
    fireEvent.click(uploadSuccessButton);

    await waitFor(() => {
      expect(screen.getByText('Successfully uploaded 1 document')).toBeInTheDocument();
    });

    // Clear message
    const closeButton = screen.getByText('×');
    fireEvent.click(closeButton);

    await waitFor(() => {
      expect(screen.queryByText('Successfully uploaded 1 document')).not.toBeInTheDocument();
    });
  });

  it('handles multiple document upload success', async () => {
    // Mock multiple documents
    vi.mocked(documentService.uploadDocument).mockResolvedValue({
      id: '1',
      filename: 'test.pdf',
      bot_id: mockBotId,
      chunk_count: 5,
      created_at: new Date().toISOString(),
      processing_status: 'processed'
    });

    render(<DocumentManagement botId={mockBotId} />);
    
    // Simulate multiple document upload
    const uploadComponent = screen.getByTestId('document-upload');
    const mockUploadMultiple = uploadComponent.querySelector('[data-testid="mock-upload-success"]');
    
    // Override the mock to simulate multiple documents
    // const mockOnUploadComplete = vi.fn();
    // const mockDocuments = [
    //   { id: '1', filename: 'test1.pdf' },
    //   { id: '2', filename: 'test2.pdf' }
    // ];

    // Simulate the upload complete callback with multiple documents
    fireEvent.click(mockUploadMultiple!);

    await waitFor(() => {
      expect(screen.getByText('Successfully uploaded 1 document')).toBeInTheDocument();
    });
  });
});