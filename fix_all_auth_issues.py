#!/usr/bin/env python3
"""
Script to fix all remaining authentication issues in playbooks tests.
Converts all func.HttpRequest calls to use create_auth_request helper.
"""

import re
import json

def fix_playbooks_tests():
    """Fix all remaining authentication issues in playbooks tests."""

    test_file = "/Users/vedprakashmishra/sutra/api/playbooks_api/playbooks_test.py"

    # Read the file
    with open(test_file, 'r') as f:
        content = f.read()

    # Find all func.HttpRequest patterns that are not using create_auth_request
    # Look for direct func.HttpRequest calls
    direct_request_pattern = r'req = func\.HttpRequest\(\s*method="([^"]+)",\s*url=([^,]+),\s*body=([^,]*),\s*headers=([^,]*),\s*route_params=([^)]*)\s*\)'

    matches = list(re.finditer(direct_request_pattern, content, re.MULTILINE | re.DOTALL))

    print(f"Found {len(matches)} direct func.HttpRequest calls to fix")

    # Process matches in reverse order to maintain string positions
    for match in reversed(matches):
        method = match.group(1)
        url = match.group(2).strip()
        body = match.group(3).strip()
        headers = match.group(4).strip()
        route_params = match.group(5).strip()

        # Extract route params if present
        route_params_dict = {}
        if route_params and route_params != "{}":
            # Try to extract the route param
            if 'route_params={"id": playbook_id}' in route_params:
                route_params_dict = '"id": playbook_id'
            elif 'route_params={"execution_id": execution_id}' in route_params:
                route_params_dict = '"execution_id": execution_id'
            else:
                route_params_dict = route_params

        # Create the replacement using create_auth_request
        replacement = f"""req = self.create_auth_request(
                method="{method}",
                url={url},
                body={body if body and body != "None" and body != "{}" else "None"},
                route_params={{{route_params_dict}}} if "{route_params_dict}" else {{}},
                user_id="test-user-123",
                role="user"
            )"""

        # Replace in content
        content = content[:match.start()] + replacement + content[match.end():]

    # Also fix any remaining instances where route_params might have different patterns
    # Fix specific patterns for route params
    content = re.sub(
        r'route_params=\{"id": playbook_id\}',
        'route_params={"id": playbook_id}',
        content
    )

    content = re.sub(
        r'route_params=\{"execution_id": execution_id\}',
        'route_params={"execution_id": execution_id}',
        content
    )

    # Write the file back
    with open(test_file, 'w') as f:
        f.write(content)

    print("Fixed all direct func.HttpRequest calls in playbooks tests")

if __name__ == "__main__":
    fix_playbooks_tests()
