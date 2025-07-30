#!/usr/bin/env python3
"""
Script to update testing progress and run specific service tests.

This script helps manage the testing progress by:
1. Running tests for specific services
2. Updating the progress tracking table
3. Generating test reports

Usage:
    python scripts/update_test_progress.py --service auth
    python scripts/update_test_progress.py --service user --test-type unit
    python scripts/update_test_progress.py --all
    python scripts/update_test_progress.py --report
"""
import argparse
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

# Service to test file mapping
SERVICE_TEST_MAPPING = {
    'auth': {
        'unit': ['tests/unit/services/test_auth_service.py'],
        'integration': ['tests/integration/test_auth_integration.py'],
        'api': ['tests/test_auth_api.py']
    },
    'user': {
        'unit': ['tests/unit/services/test_user_service.py'],
        'integration': ['tests/test_user_management_integration.py'],
        'api': ['tests/test_users_api.py']
    },
    'bot': {
        'unit': ['tests/unit/services/test_bot_service.py'],
        'integration': [],
        'api': ['tests/test_bots_api.py']
    },
    'permission': {
        'unit': ['tests/unit/services/test_permission_service.py'],
        'integration': [],
        'api': ['tests/test_permissions_api.py', 'tests/test_collaboration_api.py']
    },
    'conversation': {
        'unit': ['tests/unit/services/test_conversation_service.py'],
        'integration': ['tests/test_conversation_isolation.py'],
        'api': ['tests/test_conversation_api.py']
    },
    'chat': {
        'unit': ['tests/unit/services/test_chat_service.py'],
        'integration': ['tests/test_chat_endpoints_integration.py', 'tests/test_chat_rag_integration.py'],
        'api': ['tests/test_chat_api.py']
    },
    'document': {
        'unit': ['tests/unit/services/test_document_service.py'],
        'integration': [],
        'api': ['tests/test_documents_api.py']
    },
    'llm': {
        'unit': ['tests/unit/services/test_llm_service.py', 'tests/test_llm_service_enhanced.py'],
        'integration': ['tests/test_llm_integration.py'],
        'api': ['tests/test_providers.py']
    },
    'embedding': {
        'unit': ['tests/unit/services/test_embedding_service.py'],
        'integration': ['tests/test_embedding_integration.py'],
        'api': []
    },
    'vector': {
        'unit': ['tests/unit/services/test_vector_store.py'],
        'integration': [],
        'api': []
    },
    'analytics': {
        'unit': ['tests/unit/services/test_analytics_service.py'],
        'integration': [],
        'api': ['tests/test_analytics_api.py']
    },
    'websocket': {
        'unit': ['tests/unit/services/test_websocket_service.py'],
        'integration': ['tests/test_websocket_integration.py'],
        'api': ['tests/test_websocket_api.py']
    }
}


def run_command(command, cwd=None):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result
    except Exception as e:
        print(f"Error running command: {command}")
        print(f"Error: {e}")
        return None


def run_service_tests(service, test_type=None, verbose=False):
    """Run tests for a specific service."""
    if service not in SERVICE_TEST_MAPPING:
        print(f"❌ Unknown service: {service}")
        print(f"Available services: {', '.join(SERVICE_TEST_MAPPING.keys())}")
        return False
    
    service_tests = SERVICE_TEST_MAPPING[service]
    
    if test_type and test_type not in service_tests:
        print(f"❌ Unknown test type: {test_type}")
        print(f"Available test types for {service}: {', '.join(service_tests.keys())}")
        return False
    
    # Determine which tests to run
    if test_type:
        test_files = service_tests[test_type]
        test_description = f"{service} {test_type} tests"
    else:
        test_files = []
        for files in service_tests.values():
            test_files.extend(files)
        test_description = f"{service} all tests"
    
    if not test_files:
        print(f"⚠️ No test files found for {test_description}")
        return True
    
    print(f"🧪 Running {test_description}...")
    print(f"Test files: {', '.join(test_files)}")
    
    # Build pytest command
    pytest_args = ["pytest"]
    if verbose:
        pytest_args.append("-v")
    pytest_args.extend(test_files)
    
    # Run tests in Docker
    docker_command = f"docker-compose run --rm backend-test {' '.join(pytest_args)}"
    
    print(f"Command: {docker_command}")
    result = run_command(docker_command, cwd="../..")
    
    if result is None:
        print(f"❌ Failed to run {test_description}")
        return False
    
    print(f"\n📊 Test Results for {test_description}:")
    print("=" * 50)
    print(result.stdout)
    
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    success = result.returncode == 0
    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"\n{status} - {test_description}")
    
    return success


def run_all_tests():
    """Run all service tests."""
    print("🚀 Running all service tests...")
    
    results = {}
    total_services = len(SERVICE_TEST_MAPPING)
    passed_services = 0
    
    for service in SERVICE_TEST_MAPPING.keys():
        print(f"\n{'='*60}")
        print(f"Testing Service: {service.upper()}")
        print(f"{'='*60}")
        
        success = run_service_tests(service, verbose=True)
        results[service] = success
        
        if success:
            passed_services += 1
    
    # Print summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    
    for service, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{service:15} - {status}")
    
    print(f"\nOverall: {passed_services}/{total_services} services passed")
    
    return passed_services == total_services


def generate_test_report():
    """Generate a test report by running pytest with coverage."""
    print("📊 Generating comprehensive test report...")
    
    # Run tests with coverage
    command = "docker-compose run --rm backend-test pytest --cov=app --cov-report=html --cov-report=term tests/"
    
    result = run_command(command, cwd="../..")
    
    if result is None:
        print("❌ Failed to generate test report")
        return False
    
    print("Test Report:")
    print("=" * 50)
    print(result.stdout)
    
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    print("\n📁 HTML coverage report generated in htmlcov/ directory")
    return result.returncode == 0


def list_services():
    """List all available services."""
    print("Available services for testing:")
    print("=" * 40)
    
    for service, tests in SERVICE_TEST_MAPPING.items():
        print(f"\n{service}:")
        for test_type, files in tests.items():
            file_count = len(files)
            print(f"  {test_type}: {file_count} test file(s)")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Manage and run service tests for the multi-bot RAG platform"
    )
    
    parser.add_argument(
        "--service",
        help="Run tests for a specific service",
        choices=list(SERVICE_TEST_MAPPING.keys())
    )
    
    parser.add_argument(
        "--test-type",
        help="Type of tests to run (unit, integration, api)",
        choices=["unit", "integration", "api"]
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all service tests"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate comprehensive test report with coverage"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available services"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Run tests in verbose mode"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_services()
        return
    
    if args.report:
        success = generate_test_report()
        sys.exit(0 if success else 1)
    
    if args.all:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    
    if args.service:
        success = run_service_tests(args.service, args.test_type, args.verbose)
        sys.exit(0 if success else 1)
    
    # If no specific action, show help
    parser.print_help()


if __name__ == "__main__":
    main()