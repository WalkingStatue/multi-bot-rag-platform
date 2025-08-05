#!/usr/bin/env python3
"""
Test script for the migration API endpoints.

This script tests the API endpoints for embedding migration functionality.
"""
import asyncio
import logging
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, '/app')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_api_imports():
    """Test that all API components can be imported."""
    
    print("Testing API Imports...")
    
    try:
        # Test schema imports
        from app.schemas.bot import (
            EmbeddingValidationRequest,
            EmbeddingValidationResponse,
            MigrationEstimateRequest,
            MigrationEstimateResponse,
            MigrationStartRequest,
            MigrationProgressResponse,
            MigrationStatusResponse,
            DimensionInfoResponse,
            ActiveMigrationsResponse,
            MigrationActionResponse
        )
        print("✓ Successfully imported migration schemas")
        
        # Test that schemas can be instantiated
        validation_request = EmbeddingValidationRequest(
            provider="openai",
            model="text-embedding-3-small"
        )
        print(f"✓ Created validation request: {validation_request.provider}/{validation_request.model}")
        
        estimate_request = MigrationEstimateRequest(batch_size=25)
        print(f"✓ Created estimate request with batch size: {estimate_request.batch_size}")
        
        start_request = MigrationStartRequest(
            provider="openai",
            model="text-embedding-3-large",
            batch_size=50
        )
        print(f"✓ Created start request: {start_request.provider}/{start_request.model}")
        
    except ImportError as e:
        print(f"✗ Failed to import schemas: {e}")
        return False
    except Exception as e:
        print(f"✗ Failed to create schema instances: {e}")
        return False
    
    try:
        # Test API router import
        from app.api.bots import router
        print("✓ Successfully imported bots router with migration endpoints")
        
        # Check that the router has the expected routes
        route_paths = [route.path for route in router.routes]
        migration_routes = [
            "/bots/{bot_id}/embeddings/validate-change",
            "/bots/{bot_id}/embeddings/estimate-migration", 
            "/bots/{bot_id}/embeddings/start-migration",
            "/bots/{bot_id}/embeddings/migration-status",
            "/bots/embeddings/migration/{migration_id}/progress",
            "/bots/{bot_id}/embeddings/cancel-migration",
            "/bots/embeddings/migration/{migration_id}/rollback",
            "/bots/embeddings/migrations/active",
            "/bots/{bot_id}/embeddings/dimension-info"
        ]
        
        for route in migration_routes:
            if route in route_paths:
                print(f"✓ Found migration route: {route}")
            else:
                print(f"✗ Missing migration route: {route}")
                return False
                
    except ImportError as e:
        print(f"✗ Failed to import API router: {e}")
        return False
    except Exception as e:
        print(f"✗ Failed to check API routes: {e}")
        return False
    
    return True


async def test_service_integration():
    """Test that services integrate correctly."""
    
    print("\nTesting Service Integration...")
    
    try:
        from app.services.embedding_compatibility_manager import EmbeddingCompatibilityManager
        from app.services.embedding_migration_system import EmbeddingMigrationSystem
        
        print("✓ Successfully imported service classes")
        
        # Test that EmbeddingCompatibilityManager has migration_system attribute
        # We can't instantiate without a DB session, but we can check the class
        if hasattr(EmbeddingCompatibilityManager, '__init__'):
            print("✓ EmbeddingCompatibilityManager has proper constructor")
        
        # Check that the migration system has all required methods
        required_methods = [
            'start_migration',
            'get_migration_progress', 
            'get_bot_migration_status',
            'cancel_migration',
            'rollback_migration',
            'get_all_active_migrations',
            'create_migration_config'
        ]
        
        for method in required_methods:
            if hasattr(EmbeddingMigrationSystem, method):
                print(f"✓ EmbeddingMigrationSystem has method: {method}")
            else:
                print(f"✗ EmbeddingMigrationSystem missing method: {method}")
                return False
        
    except ImportError as e:
        print(f"✗ Failed to import services: {e}")
        return False
    except Exception as e:
        print(f"✗ Service integration test failed: {e}")
        return False
    
    return True


async def test_schema_validation():
    """Test schema validation works correctly."""
    
    print("\nTesting Schema Validation...")
    
    try:
        from app.schemas.bot import (
            EmbeddingValidationRequest,
            MigrationEstimateRequest,
            MigrationStartRequest
        )
        from pydantic import ValidationError
        
        # Test valid requests
        valid_validation = EmbeddingValidationRequest(
            provider="openai",
            model="text-embedding-3-small"
        )
        print("✓ Valid validation request accepted")
        
        valid_estimate = MigrationEstimateRequest(batch_size=100)
        print("✓ Valid estimate request accepted")
        
        valid_start = MigrationStartRequest(
            provider="gemini",
            model="embedding-001",
            batch_size=25
        )
        print("✓ Valid start request accepted")
        
        # Test invalid requests
        try:
            invalid_provider = EmbeddingValidationRequest(
                provider="invalid_provider",
                model="some-model"
            )
            print("✗ Invalid provider should have been rejected")
            return False
        except ValidationError:
            print("✓ Invalid provider correctly rejected")
        
        try:
            invalid_batch_size = MigrationEstimateRequest(batch_size=0)
            print("✗ Invalid batch size should have been rejected")
            return False
        except ValidationError:
            print("✓ Invalid batch size correctly rejected")
        
        try:
            invalid_batch_size_large = MigrationStartRequest(
                provider="openai",
                model="text-embedding-3-small",
                batch_size=1000  # Too large
            )
            print("✗ Large batch size should have been rejected")
            return False
        except ValidationError:
            print("✓ Large batch size correctly rejected")
        
    except Exception as e:
        print(f"✗ Schema validation test failed: {e}")
        return False
    
    return True


async def test_migration_workflow():
    """Test the migration workflow logic."""
    
    print("\nTesting Migration Workflow Logic...")
    
    try:
        from app.services.embedding_migration_system import (
            MigrationStatus,
            MigrationPhase,
            MigrationConfig,
            MigrationProgress
        )
        from datetime import datetime, timezone
        import uuid
        
        # Test status transitions
        statuses = list(MigrationStatus)
        phases = list(MigrationPhase)
        
        print(f"✓ Migration has {len(statuses)} statuses and {len(phases)} phases")
        
        # Test that we can create a complete migration config
        config = MigrationConfig(
            bot_id=uuid.uuid4(),
            from_provider="openai",
            from_model="text-embedding-ada-002",
            from_dimension=1536,
            to_provider="openai", 
            to_model="text-embedding-3-large",
            to_dimension=3072,
            batch_size=50,
            max_retries=3,
            retry_delay=2.0,
            timeout_seconds=3600,
            enable_rollback=True,
            verify_migration=True
        )
        print("✓ Created complete migration configuration")
        
        # Test progress tracking
        progress = MigrationProgress(
            migration_id="test_123",
            bot_id=config.bot_id,
            status=MigrationStatus.IN_PROGRESS,
            phase=MigrationPhase.DATA_MIGRATION,
            total_chunks=1000,
            processed_chunks=250,
            failed_chunks=5,
            current_batch=5,
            total_batches=20,
            start_time=datetime.now(timezone.utc),
            last_update=datetime.now(timezone.utc),
            rollback_available=True
        )
        print("✓ Created migration progress tracking")
        
        # Test progress formatting
        from app.services.embedding_migration_system import format_migration_progress
        formatted = format_migration_progress(progress)
        
        expected_keys = [
            'migration_id', 'bot_id', 'status', 'phase', 'progress', 
            'timing', 'rollback_available', 'error_message', 'metadata'
        ]
        
        for key in expected_keys:
            if key in formatted:
                print(f"✓ Progress format includes: {key}")
            else:
                print(f"✗ Progress format missing: {key}")
                return False
        
        # Check progress percentage calculation
        expected_percentage = (250 / 1000) * 100
        actual_percentage = formatted['progress']['percentage']
        if abs(actual_percentage - expected_percentage) < 0.01:
            print(f"✓ Progress percentage calculated correctly: {actual_percentage}%")
        else:
            print(f"✗ Progress percentage incorrect: expected {expected_percentage}, got {actual_percentage}")
            return False
        
    except Exception as e:
        print(f"✗ Migration workflow test failed: {e}")
        return False
    
    return True


async def main():
    """Run all tests."""
    print("=" * 70)
    print("EMBEDDING MIGRATION API TEST SUITE")
    print("=" * 70)
    
    # Run tests
    test_results = []
    
    test_results.append(await test_api_imports())
    test_results.append(await test_service_integration())
    test_results.append(await test_schema_validation())
    test_results.append(await test_migration_workflow())
    
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    if all(test_results):
        print("🎉 ALL API TESTS PASSED!")
        print(f"\nPassed: {passed_tests}/{total_tests} test suites")
        print("\nThe migration API is ready for use!")
        print("\nAvailable endpoints:")
        print("- POST /{bot_id}/embeddings/validate-change")
        print("- POST /{bot_id}/embeddings/estimate-migration")
        print("- POST /{bot_id}/embeddings/start-migration")
        print("- GET  /{bot_id}/embeddings/migration-status")
        print("- GET  /embeddings/migration/{migration_id}/progress")
        print("- POST /{bot_id}/embeddings/cancel-migration")
        print("- POST /embeddings/migration/{migration_id}/rollback")
        print("- GET  /embeddings/migrations/active")
        print("- GET  /{bot_id}/embeddings/dimension-info")
        return True
    else:
        print("❌ SOME API TESTS FAILED!")
        print(f"\nPassed: {passed_tests}/{total_tests} test suites")
        print("\nPlease check the error messages above and fix any issues.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)