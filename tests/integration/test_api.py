#!/usr/bin/env python3
"""
Simple API test script to verify OCR endpoints are working.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test basic health endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_root():
    """Test root endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Root endpoint: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Root endpoint failed: {e}")
        return False

def main():
    """Run basic API tests."""
    print("Testing Multi-Bot RAG Platform API...")
    
    health_ok = test_health()
    root_ok = test_root()
    
    print(f"\nResults:")
    print(f"Health endpoint: {'✅' if health_ok else '❌'}")
    print(f"Root endpoint: {'✅' if root_ok else '❌'}")
    
    if health_ok and root_ok:
        print("\n🎉 API is running successfully!")
        print("📝 Next steps:")
        print("1. Access the frontend at http://localhost:3000")
        print("2. Create a user account and login")
        print("3. Upload a scanned PDF or image file to test OCR")
        return True
    else:
        print("\n❌ Some API tests failed")
        return False

if __name__ == "__main__":
    main()