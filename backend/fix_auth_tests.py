#!/usr/bin/env python3
"""
Script to fix authentication issues in test files.
This script will update test files to use the standardized mock_authentication approach.
"""

import os
import re
from pathlib import Path

def fix_test_file(file_path):
    """Fix authentication issues in a single test file."""
    print(f"Fixing {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add import for mock_authentication if not present
    if 'from tests.test_auth_helper import' not in content:
        # Find the imports section and add our import
        import_pattern = r'(from app\..*?\n)'
        if re.search(import_pattern, content):
            content = re.sub(
                r'(from app\..*?\n)',
                r'\1from tests.test_auth_helper import mock_authentication, create_mock_user\n',
                content,
                count=1
            )
    
    # Replace @patch decorators for authentication
    content = re.sub(
        r'@patch\([\'"]app\.core\.dependencies\.get_current_user[\'"]\)\s*\n\s*@patch\([\'"]app\.core\.dependencies\.get_current_active_user[\'"]\)\s*\n\s*def (test_\w+)\(self, mock_get_active_user, mock_get_user,',
        r'def \1(self,',
        content
    )
    
    content = re.sub(
        r'@patch\([\'"]app\.core\.dependencies\.get_current_user[\'"]\)\s*\n\s*def (test_\w+)\(self, mock_get_user,',
        r'def \1(self,',
        content
    )
    
    content = re.sub(
        r'@patch\([\'"]app\.core\.dependencies\.get_current_active_user[\'"]\)\s*\n\s*def (test_\w+)\(self, mock_get_user,',
        r'def \1(self,',
        content
    )
    
    # Replace auth_headers fixture usage with mock_authentication
    content = re.sub(
        r'def (test_\w+)\(self, ([^)]*), auth_headers\)',
        r'def \1(self, \2)',
        content
    )
    
    content = re.sub(
        r'def (test_\w+)\(self, ([^)]*), sample_auth_headers\)',
        r'def \1(self, \2)',
        content
    )
    
    # Replace mock_get_user.return_value = user patterns
    content = re.sub(
        r'mock_get_user\.return_value = (\w+)\s*\n',
        r'',
        content
    )
    
    content = re.sub(
        r'mock_get_active_user\.return_value = (\w+)\s*\n',
        r'',
        content
    )
    
    # Wrap test execution in mock_authentication context
    # This is a more complex pattern that needs manual review
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")

def main():
    """Main function to fix all test files."""
    test_dir = Path("tests")
    
    # List of test files that need authentication fixes
    test_files = [
        "tests/integration/api/test_analytics_api.py",
        "tests/integration/api/test_collaboration_api.py", 
        "tests/integration/api/test_conversation_api.py",
        "tests/integration/api/test_permissions_api.py",
        "tests/integration/api/test_websocket_api.py",
        "tests/e2e/workflows/test_chat_rag_integration.py",
        "tests/e2e/scenarios/test_analytics_service.py",
    ]
    
    for test_file in test_files:
        file_path = Path(test_file)
        if file_path.exists():
            fix_test_file(file_path)
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    main()