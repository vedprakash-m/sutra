#!/usr/bin/env python3
"""
Fix playbooks_api tests to use create_auth_request instead of mock_auth_request fixture.
"""

import re


def fix_playbooks_tests():
    file_path = "/Users/vedprakashmishra/sutra/api/playbooks_api/playbooks_test.py"

    with open(file_path, "r") as f:
        content = f.read()

    # Step 1: Remove mock_auth_request from test method signatures
    content = re.sub(r", mock_auth_request", "", content)

    # Step 2: Replace mock_cosmos_client with mock_database_manager
    content = re.sub(r"mock_cosmos_client", "mock_database_manager", content)

    # Step 3: Replace all req = mock_auth_request with appropriate create_auth_request calls
    # We need to analyze each test context to determine the right parameters

    # Pattern for POST requests (creating/updating playbooks)
    post_pattern = r"req = mock_auth_request"

    # For now, let's do a simpler replacement and then we can refine specific tests
    # Replace with basic GET request - we'll refine each test individually
    content = re.sub(
        r"req = mock_auth_request", 'req = create_auth_request(method="GET")', content
    )

    # Step 4: Add mock database manager patch pattern like we used in other APIs
    test_methods = re.findall(
        r"(async def test_\w+.*?)(?=\n    async def|\n\nclass|\Z)", content, re.DOTALL
    )

    for i, test_method in enumerate(test_methods):
        if "create_auth_request" in test_method and "with patch" not in test_method:
            # Add database manager patch
            lines = test_method.split("\n")
            method_line_idx = -1
            for j, line in enumerate(lines):
                if "async def test_" in line:
                    method_line_idx = j
                    break

            if method_line_idx >= 0:
                # Find the first req = create_auth_request line
                req_line_idx = -1
                for j, line in enumerate(lines):
                    if "req = create_auth_request" in line:
                        req_line_idx = j
                        break

                if req_line_idx >= 0:
                    # Insert the patch before the request creation
                    indent = len(lines[req_line_idx]) - len(
                        lines[req_line_idx].lstrip()
                    )
                    patch_lines = [
                        f"{' ' * indent}# Additional patch to ensure we catch the right import",
                        f"{' ' * indent}with patch(\"api.playbooks_api.get_database_manager\", return_value=mock_database_manager):",
                        f"{' ' * (indent + 4)}{lines[req_line_idx].strip()}",
                    ]

                    # Replace the original req line and add patch
                    lines[req_line_idx] = "\n".join(patch_lines)

                    # Need to indent the response call as well
                    for k in range(req_line_idx + 1, len(lines)):
                        if "response = await playbooks_main(req)" in lines[k]:
                            current_indent = len(lines[k]) - len(lines[k].lstrip())
                            lines[k] = f"{' ' * (current_indent + 4)}{lines[k].strip()}"
                            break

                    new_test_method = "\n".join(lines)
                    content = content.replace(test_method, new_test_method)

    with open(file_path, "w") as f:
        f.write(content)

    print("Fixed playbooks_api tests to use create_auth_request and unified patterns")


if __name__ == "__main__":
    fix_playbooks_tests()
