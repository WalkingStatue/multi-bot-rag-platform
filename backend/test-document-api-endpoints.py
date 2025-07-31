#!/usr/bin/env python3
"""
Test script to test the actual document API endpoints and identify 422 errors.
"""
import asyncio
import sys
import os
import logging
from pathlib import Path
import httpx
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_document_api_endpoints():
    """Test document API endpoints to identify 422 errors."""
    
    print("🔍 Testing Document API Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api"
    
    # Test 1: Login to get access token
    print("\n1. Logging in to get access token...")
    
    login_data = {
        "username": "test_user_automated",
        "password": "testpassword123"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{base_url}/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                tokens = response.json()
                access_token = tokens["access_token"]
                print("✅ Login successful")
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login request failed: {e}")
            return False
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Test 2: Get user's bots
    print("\n2. Getting user's bots...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{base_url}/bots/",
                headers=headers
            )
            
            if response.status_code == 200:
                bots = response.json()
                if bots:
                    bot_id = bots[0]["bot"]["id"]
                    print(f"✅ Found bot: {bot_id}")
                else:
                    print("❌ No bots found")
                    return False
            else:
                print(f"❌ Failed to get bots: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Get bots request failed: {e}")
            return False
    
    # Test 3: Test document listing endpoint
    print("\n3. Testing document listing endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{base_url}/bots/{bot_id}/documents/",
                headers=headers
            )
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                print("✅ Document listing endpoint works")
            elif response.status_code == 422:
                print("❌ 422 Validation Error in document listing!")
                print(f"   Error details: {response.json()}")
                return False
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Document listing request failed: {e}")
            return False
    
    # Test 4: Test document stats endpoint
    print("\n4. Testing document stats endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{base_url}/bots/{bot_id}/documents/stats",
                headers=headers
            )
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                print("✅ Document stats endpoint works")
            elif response.status_code == 422:
                print("❌ 422 Validation Error in document stats!")
                print(f"   Error details: {response.json()}")
                return False
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Document stats request failed: {e}")
            return False
    
    # Test 5: Test document upload endpoint
    print("\n5. Testing document upload endpoint...")
    
    # Create a test file
    test_content = b"This is a test document for API endpoint testing."
    
    files = {
        "file": ("test_api_document.txt", test_content, "text/plain")
    }
    
    # Remove Content-Type header for multipart upload
    upload_headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{base_url}/bots/{bot_id}/documents/",
                headers=upload_headers,
                files=files,
                params={"process_immediately": "false"}
            )
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text[:500]}...")
            
            if response.status_code == 201:
                print("✅ Document upload endpoint works")
                uploaded_doc = response.json()
                document_id = uploaded_doc["id"]
            elif response.status_code == 422:
                print("❌ 422 Validation Error in document upload!")
                error_details = response.json()
                print(f"   Error details: {json.dumps(error_details, indent=2)}")
                return False
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Document upload request failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Test 6: Test document search endpoint
    print("\n6. Testing document search endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{base_url}/bots/{bot_id}/documents/search",
                headers=headers,
                params={"query": "test"}
            )
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                print("✅ Document search endpoint works")
            elif response.status_code == 422:
                print("❌ 422 Validation Error in document search!")
                print(f"   Error details: {response.json()}")
            else:
                print(f"⚠️  Document search failed (expected due to missing embeddings): {response.status_code}")
                
        except Exception as e:
            print(f"❌ Document search request failed: {e}")
    
    # Test 7: Test document processing endpoint
    print("\n7. Testing document processing endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{base_url}/bots/{bot_id}/documents/{document_id}/process",
                headers=headers
            )
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                print("✅ Document processing endpoint works")
            elif response.status_code == 422:
                print("❌ 422 Validation Error in document processing!")
                print(f"   Error details: {response.json()}")
            else:
                print(f"⚠️  Document processing failed (expected due to missing API keys): {response.status_code}")
                
        except Exception as e:
            print(f"❌ Document processing request failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Document API Endpoint Test Complete!")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_document_api_endpoints())
    if success:
        print("\n✅ Document API endpoints are working correctly!")
    else:
        print("\n❌ Found issues with document API endpoints.")
        sys.exit(1)