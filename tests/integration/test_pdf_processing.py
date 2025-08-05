#!/usr/bin/env python3
"""
Test script specifically for PDF processing with the new improvements.
"""
import sys
import logging
from pathlib import Path
from io import BytesIO

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent))

from app.utils.text_processing import DocumentProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_pdf():
    """Create a simple test PDF using reportlab."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add some text to the PDF
        p.drawString(100, 750, "Test PDF Document")
        p.drawString(100, 700, "This is a test PDF created for OCR testing.")
        p.drawString(100, 650, "It contains multiple lines of text.")
        p.drawString(100, 600, "The OCR system should be able to extract this text.")
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        logger.warning("reportlab not available, creating minimal PDF")
        # Create a minimal PDF structure
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
        return pdf_content


def test_pdf_processing():
    """Test PDF processing with the improved error handling."""
    print("=== Testing PDF Processing with Improved Error Handling ===")
    
    try:
        # Create a document processor
        processor = DocumentProcessor(
            chunk_size=500,
            chunk_overlap=100,
            enable_ocr=True,
            ocr_language='eng'
        )
        
        print("✅ DocumentProcessor created successfully")
        
        # Create test PDF content
        pdf_content = create_test_pdf()
        print(f"✅ Test PDF created ({len(pdf_content)} bytes)")
        
        # Process the PDF
        chunks, metadata = processor.process_document(
            file_content=pdf_content,
            filename="test_document.pdf",
            document_id="test_123",
            additional_metadata={"test": True}
        )
        
        print(f"✅ PDF processed successfully:")
        print(f"   - Chunks created: {len(chunks)}")
        print(f"   - Extraction method: {metadata.get('extraction_metadata', {}).get('extraction_method', 'Unknown')}")
        print(f"   - Total pages: {metadata.get('extraction_metadata', {}).get('total_pages', 'Unknown')}")
        
        # Print first chunk content (truncated)
        if chunks:
            first_chunk = chunks[0]
            content_preview = first_chunk.content[:200] + "..." if len(first_chunk.content) > 200 else first_chunk.content
            print(f"   - First chunk preview: {content_preview}")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF processing failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


def main():
    """Run PDF processing tests."""
    print("Testing improved PDF processing...\n")
    
    success = test_pdf_processing()
    
    print(f"\n=== Results ===")
    print(f"PDF Processing: {'✅' if success else '❌'}")
    
    if success:
        print("\n🎉 PDF processing is working correctly!")
        print("The 'document closed' error should be resolved.")
    else:
        print("\n❌ PDF processing still has issues.")
        print("Check the logs for more details.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)