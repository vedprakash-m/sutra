#!/usr/bin/env python3
"""
Comprehensive script to fix authentication issues across all test files.
Converts func.HttpRequest calls to use create_auth_request helpers.
"""

import re
import os
import glob

def fix_test_file_auth(file_path):
    """Fix authentication issues in a single test file."""
    print(f"Processing {file_path}...")

    with open(file_path, 'r') as f:
        content = f.read()

    original_content = content

    # Pattern 1: Simple func.HttpRequest with method, url, body, headers, route_params
    pattern1 = r'req = func\.HttpRequest\(\s*method="([^"]*)",\s*url="([^"]*)",\s*body=([^,]*),\s*headers=([^,]*),\s*route_params=(\{[^}]*\}),?\s*\)'

    def replace_pattern1(match):
        method = match.group(1)
        url = match.group(2)
        body = match.group(3)
        headers = match.group(4)
        route_params = match.group(5)

        # Skip if body contains json.dumps - handle manually
        if 'json.dumps(' in body:
            return match.group(0)  # Return unchanged

        return f'''req = self.create_auth_request(
            method="{method}",
            url="{url}",
            route_params={route_params},
            user_id="test-user-123",
            role="user"
        )'''

    # Apply pattern 1
    content = re.sub(pattern1, replace_pattern1, content, flags=re.MULTILINE | re.DOTALL)

    # Pattern 2: func.HttpRequest with just method, url, body (empty), headers (empty), route_params
    pattern2 = r'req = func\.HttpRequest\(\s*method="([^"]*)",\s*url="([^"]*)",\s*body=b"[^"]*",\s*headers=\{\},\s*route_params=(\{[^}]*\}),?\s*\)'

    def replace_pattern2(match):
        method = match.group(1)
        url = match.group(2)
        route_params = match.group(3)

        return f'''req = self.create_auth_request(
            method="{method}",
            url="{url}",
            route_params={route_params},
            user_id="test-user-123",
            role="user"
        )'''

    # Apply pattern 2
    content = re.sub(pattern2, replace_pattern2, content, flags=re.MULTILINE | re.DOTALL)

    # Pattern 3: func.HttpRequest with params
    pattern3 = r'req = func\.HttpRequest\(\s*method="([^"]*)",\s*url="([^"]*)",\s*body=b"[^"]*",\s*headers=\{\},\s*route_params=(\{[^}]*\}),\s*params=(\{[^}]*\}),?\s*\)'

    def replace_pattern3(match):
        method = match.group(1)
        url = match.group(2)
        route_params = match.group(3)
        params = match.group(4)

        return f'''req = self.create_auth_request(
            method="{method}",
            url="{url}",
            route_params={route_params},
            params={params},
            user_id="test-user-123",
            role="user"
        )'''

    # Apply pattern 3
    content = re.sub(pattern3, replace_pattern3, content, flags=re.MULTILINE | re.DOTALL)

    # Check if changes were made
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"  ✅ Fixed authentication issues in {file_path}")
        return True
    else:
        print(f"  ⏭️  No changes needed in {file_path}")
        return False

def main():
    """Fix authentication issues in all API test files."""

    # List of critical API test files to fix
    test_files = [
        '/Users/vedprakashmishra/sutra/api/collections_api/collections_test.py',
        '/Users/vedprakashmishra/sutra/api/playbooks_api/playbooks_test.py',
        '/Users/vedprakashmishra/sutra/api/integrations_api/integrations_test.py',
        '/Users/vedprakashmishra/sutra/api/llm_execute_api/llm_execute_test.py',
    ]

    fixed_count = 0

    for file_path in test_files:
        if os.path.exists(file_path):
            if fix_test_file_auth(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")

    print(f"\n✅ Fixed authentication issues in {fixed_count} test files")
    print("Note: Some complex patterns may need manual fixing")

if __name__ == '__main__':
    main()
