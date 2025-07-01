#!/usr/bin/env python3
"""
Fix cost_management_api tests to use create_auth_request consistently.
"""

import re


def fix_cost_management_tests():
    file_path = (
        "/Users/vedprakashmishra/sutra/api/cost_management_api/cost_management_test.py"
    )

    with open(file_path, "r") as f:
        content = f.read()

    # Replace func.HttpRequest with create_auth_request
    # Pattern: func.HttpRequest(method="GET", url="...", body=...)

    # Pattern 1: Simple GET requests
    content = re.sub(
        r'req = func\.HttpRequest\(\s*method="GET",\s*url="([^"]+)"\s*\)',
        r'req = create_auth_request(method="GET", url="\1")',
        content,
    )

    # Pattern 2: POST requests with body
    content = re.sub(
        r'req = func\.HttpRequest\(\s*method="POST",\s*url="([^"]+)",\s*body=([^)]+)\s*\)',
        r'req = create_auth_request(method="POST", url="\1", body=\2)',
        content,
    )

    # Pattern 3: PUT requests with body
    content = re.sub(
        r'req = func\.HttpRequest\(\s*method="PUT",\s*url="([^"]+)",\s*body=([^)]+)\s*\)',
        r'req = create_auth_request(method="PUT", url="\1", body=\2)',
        content,
    )

    # Pattern 4: Multi-line func.HttpRequest patterns
    # Look for the pattern where func.HttpRequest spans multiple lines
    multiline_pattern = r'req = func\.HttpRequest\(\s*method="([^"]+)",\s*url="([^"]+)"(?:,\s*body=([^)]+))?\s*\)'

    def replace_multiline(match):
        method = match.group(1)
        url = match.group(2)
        body = match.group(3)

        if body:
            return f'req = create_auth_request(method="{method}", url="{url}", body={body})'
        else:
            return f'req = create_auth_request(method="{method}", url="{url}")'

    content = re.sub(
        multiline_pattern, replace_multiline, content, flags=re.MULTILINE | re.DOTALL
    )

    # Also fix any remaining patterns with headers or other parameters
    # Look for remaining func.HttpRequest patterns and replace them
    remaining_patterns = re.findall(r"func\.HttpRequest\([^)]+\)", content)

    for pattern in remaining_patterns:
        # Parse the parameters from the HttpRequest call
        if "method=" in pattern and "url=" in pattern:
            # Extract method and url
            method_match = re.search(r'method="([^"]+)"', pattern)
            url_match = re.search(r'url="([^"]+)"', pattern)

            if method_match and url_match:
                method = method_match.group(1)
                url = url_match.group(1)

                # Check for body parameter
                body_match = re.search(r"body=([^,)]+)", pattern)

                if body_match:
                    body = body_match.group(1)
                    replacement = f'create_auth_request(method="{method}", url="{url}", body={body})'
                else:
                    replacement = f'create_auth_request(method="{method}", url="{url}")'

                content = content.replace(pattern, replacement)

    # Fix specific user ID references that might be hardcoded
    content = re.sub(r'"user-123"', '"test-user-123"', content)

    with open(file_path, "w") as f:
        f.write(content)

    print("Fixed cost_management_api tests to use create_auth_request")


if __name__ == "__main__":
    fix_cost_management_tests()
