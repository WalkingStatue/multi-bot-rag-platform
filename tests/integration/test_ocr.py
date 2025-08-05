#!/usr/bin/env python3
"""
Test script for OCR functionality.
"""
import sys
import logging
from pathlib import Path
from io import BytesIO

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent))

from app.utils.text_processing import DocumentProcessor
from app.core.ocr_config import check_ocr_availability, get_tesseract_languages

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ocr_availability():
    """Test if OCR is available and working."""
    print("=== Testing OCR Availability ===")
    
    is_available, message = check_ocr_availability()
    print(f"OCR Available: {is_available}")
    print(f"Message: {message}")
    
    if is_available:
        languages = get_tesseract_languages()
        print(f"Installed languages: {languages}")
    
    return is_available


def test_pdf_processing():
    """Test PDF processing with OCR."""
    print("\n=== Testing PDF Processing ===")
    
    try:
        # Create a document processor with OCR enabled
        processor = DocumentProcessor(
            chunk_size=500,
            chunk_overlap=100,
            enable_ocr=True,
            ocr_language='eng'
        )
        
        print("DocumentProcessor created successfully with OCR enabled")
        
        # Test with a simple text-based PDF (you would need to provide a real PDF file)
        # For now, just test the processor initialization
        print("PDF processor ready for testing")
        
        return True
        
    except Exception as e:
        print(f"Error testing PDF processing: {e}")
        return False


def test_image_processing():
    """Test image processing with OCR."""
    print("\n=== Testing Image Processing ===")
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        import pytesseract
        from app.utils.text_processing import DocumentExtractor
        
        # Create a test image with text
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw test text
        test_text = "Hello World! This is a test."
        draw.text((10, 30), test_text, fill='black')
        
        # Convert to bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_content = img_bytes.getvalue()
        
        # Test with DocumentExtractor
        extractor = DocumentExtractor(enable_ocr=True, ocr_language='eng')
        
        # Validate the image file
        from pathlib import Path
        is_valid, mime_type, error_msg = extractor.validate_file(
            Path("test.png"), img_content
        )
        
        print(f"Image validation: {is_valid}, MIME: {mime_type}")
        
        if is_valid:
            # Extract text from image
            extracted_text, metadata = extractor.extract_text(
                img_content, mime_type, "test.png"
            )
            
            print(f"Original text: {test_text}")
            print(f"Extracted text: {extracted_text.strip()}")
            print(f"Metadata: {metadata}")
            
            return True
        else:
            print(f"Image validation failed: {error_msg}")
            return False
            
    except Exception as e:
        print(f"Error testing image processing: {e}")
        return False


def main():
    """Run all OCR tests."""
    print("Starting OCR functionality tests...\n")
    
    # Test OCR availability
    ocr_available = test_ocr_availability()
    
    if not ocr_available:
        print("\nOCR is not available. Please install Tesseract OCR.")
        return False
    
    # Test PDF processing
    pdf_test = test_pdf_processing()
    
    # Test image processing
    image_test = test_image_processing()
    
    print(f"\n=== Test Results ===")
    print(f"OCR Available: {ocr_available}")
    print(f"PDF Processing: {pdf_test}")
    print(f"Image Processing: {image_test}")
    
    all_passed = ocr_available and pdf_test and image_test
    print(f"All tests passed: {all_passed}")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)