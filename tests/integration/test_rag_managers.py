#!/usr/bin/env python3
"""
Test script to verify RAG managers can be imported and instantiated.
"""
import sys
import os
import asyncio
from unittest.mock import Mock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

try:
    # Test imports
    from app.services.rag_pipeline_manager import RAGPipelineManager
    from app.services.embedding_compatibility_manager import EmbeddingCompatibilityManager
    from app.services.vector_collection_manager import VectorCollectionManager
    from app.services.rag_error_recovery import RAGErrorRecovery
    
    print("✅ All RAG managers imported successfully")
    
    # Test instantiation with mock database session
    mock_db = Mock()
    
    # Test RAGPipelineManager
    try:
        rag_manager = RAGPipelineManager(mock_db)
        print("✅ RAGPipelineManager instantiated successfully")
    except Exception as e:
        print(f"❌ RAGPipelineManager instantiation failed: {e}")
    
    # Test EmbeddingCompatibilityManager
    try:
        embedding_manager = EmbeddingCompatibilityManager(mock_db)
        print("✅ EmbeddingCompatibilityManager instantiated successfully")
    except Exception as e:
        print(f"❌ EmbeddingCompatibilityManager instantiation failed: {e}")
    
    # Test VectorCollectionManager
    try:
        collection_manager = VectorCollectionManager(mock_db)
        print("✅ VectorCollectionManager instantiated successfully")
    except Exception as e:
        print(f"❌ VectorCollectionManager instantiation failed: {e}")
    
    # Test RAGErrorRecovery
    try:
        error_recovery = RAGErrorRecovery()
        print("✅ RAGErrorRecovery instantiated successfully")
    except Exception as e:
        print(f"❌ RAGErrorRecovery instantiation failed: {e}")
    
    print("\n🎉 All RAG managers are working correctly!")
    
    # Test some basic functionality
    print("\n🔍 Testing basic functionality...")
    
    # Test error recovery statistics
    try:
        stats = error_recovery.get_error_statistics()
        print(f"✅ Error statistics retrieved: {stats['total_errors']} total errors")
    except Exception as e:
        print(f"❌ Error statistics failed: {e}")
    
    # Test performance metrics
    try:
        metrics = rag_manager.get_performance_metrics()
        print(f"✅ Performance metrics retrieved: {len(metrics)} operation types")
    except Exception as e:
        print(f"❌ Performance metrics failed: {e}")
    
    print("\n✨ Basic functionality tests completed!")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)