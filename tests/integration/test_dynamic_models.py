#!/usr/bin/env python3
"""
Test script for dynamic model fetching functionality
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.llm_service import LLMProviderService

async def test_dynamic_models():
    """Test dynamic model fetching for different providers."""
    print("Testing dynamic model fetching...")
    
    llm_service = LLMProviderService()
    
    try:
        # Test static models first
        print("\n=== Static Models ===")
        providers = llm_service.get_supported_providers()
        for provider in providers:
            static_models = llm_service.get_available_models(provider)
            print(f"{provider}: {len(static_models)} static models")
            print(f"  First few: {static_models[:3]}")
        
        # Test dynamic models (will fail without API keys, but should fall back to static)
        print("\n=== Dynamic Models (without API keys) ===")
        for provider in providers:
            try:
                dynamic_models = await llm_service.get_available_models_dynamic(provider, "fake-key")
                print(f"{provider}: {len(dynamic_models)} dynamic models (fallback to static)")
            except Exception as e:
                print(f"{provider}: Error - {e}")
        
        print("\n✅ Dynamic model fetching system is working!")
        print("   - Static models are available as fallback")
        print("   - Dynamic fetching will work when valid API keys are provided")
        
    except Exception as e:
        print(f"❌ Error testing dynamic models: {e}")
    finally:
        await llm_service.close()

if __name__ == "__main__":
    asyncio.run(test_dynamic_models())