#!/usr/bin/env python3
"""
Script to fix playbooks API test authentication issues.
This script updates all func.HttpRequest calls to use authenticated requests.
"""

import re
import sys

def fix_playbooks_tests():
    file_path = "api/playbooks_api/playbooks_test.py"

    with open(file_path, 'r') as f:
        content = f.read()

    # Pattern to match func.HttpRequest calls
    pattern = r'req = func\.HttpRequest\(\s*method="([^"]+)",\s*url="([^"]+)",\s*body=([^,]+),\s*headers=\{[^}]*\},\s*route_params=([^,]+),?\s*\)'

    def replace_request(match):
        method = match.group(1)
        url = match.group(2)
        body = match.group(3)
        route_params = match.group(4)

        # Determine if body should be passed
        body_param = ""
        if body != "b\"\"" and "None" not in body:
            body_param = f",\n            body={body}"

        return f'''req = self.create_auth_request(
            method="{method}",
            url="{url}"{body_param},
            route_params={route_params},
            user_id="test-user-123",
            role="user"
        )'''

    # Apply the replacement
    new_content = re.sub(pattern, replace_request, content, flags=re.MULTILINE | re.DOTALL)

    # Handle simpler cases
    simple_pattern = r'req = func\.HttpRequest\(\s*method="([^"]+)",\s*url="([^"]+)",\s*body=([^,]+),\s*headers=\{[^}]*\}\s*\)'

    def replace_simple_request(match):
        method = match.group(1)
        url = match.group(2)
        body = match.group(3)

        body_param = ""
        if body != "b\"\"" and "None" not in body:
            body_param = f",\n            body={body}"

        return f'''req = self.create_auth_request(
            method="{method}",
            url="{url}"{body_param},
            user_id="test-user-123",
            role="user"
        )'''

    new_content = re.sub(simple_pattern, replace_simple_request, new_content)

    # Write back the file
    with open(file_path, 'w') as f:
        f.write(new_content)

    print("Fixed playbooks test authentication issues")

if __name__ == "__main__":
    fix_playbooks_tests()
