#!/usr/bin/env python3
"""
Script to automatically update API test files to use unified authentication system.
"""

import os
import re
import glob


def update_test_file(file_path):
    """Update a single test file to use unified auth."""
    with open(file_path, "r") as f:
        content = f.read()

    print(f"Updating {file_path}...")

    # Track changes
    original_content = content

    # 1. Update imports - remove base64, add create_auth_request from conftest
    content = re.sub(r"import base64\n", "", content)

    # Add create_auth_request import if not present
    if (
        "from ..conftest import create_auth_request" not in content
        and "create_auth_request" not in content
    ):
        # Find the import section and add it
        import_match = re.search(r"(import azure\.functions as func.*?\n)", content)
        if import_match:
            content = content.replace(
                import_match.group(1),
                import_match.group(1) + "from ..conftest import create_auth_request\n",
            )

    # 2. Remove create_auth_request method definitions from classes
    content = re.sub(
        r"    def create_auth_request\(self.*?\n        \)",
        "",
        content,
        flags=re.DOTALL,
    )

    # 3. Update test method signatures to use new auth fixtures
    # Replace mock_auth_success, mock_admin_auth, etc. with auth_test_user, auth_admin_user
    content = re.sub(r"mock_auth_success", "auth_test_user", content)
    content = re.sub(r"mock_admin_auth", "auth_admin_user", content)
    content = re.sub(r"mock_user_auth", "auth_test_user", content)
    content = re.sub(r"mock_non_admin_auth", "auth_test_user", content)
    content = re.sub(r"mock_no_auth", "auth_no_user", content)

    # 4. Update create_auth_request calls to remove old parameters
    content = re.sub(
        r'self\.create_auth_request\(\s*method="([^"]*)"[^)]*\)',
        r'create_auth_request(method="\1")',
        content,
    )
    content = re.sub(
        r"self\.create_auth_request\(\s*\)", r"create_auth_request()", content
    )

    # 5. Update any remaining create_auth_request calls with complex parameters
    # Match multi-line create_auth_request calls and simplify them
    def simplify_create_auth_request(match):
        method_match = re.search(r'method="([^"]*)"', match.group(0))
        body_match = re.search(r"body=([^,\)]+)", match.group(0))
        url_match = re.search(r'url="([^"]*)"', match.group(0))

        params = []
        if method_match:
            params.append(f'method="{method_match.group(1)}"')
        if body_match:
            params.append(f"body={body_match.group(1)}")
        if url_match:
            params.append(f'url="{url_match.group(1)}"')

        return f'create_auth_request({", ".join(params)})'

    content = re.sub(
        r"self\.create_auth_request\([^)]*\n[^)]*\n[^)]*\)",
        simplify_create_auth_request,
        content,
        flags=re.DOTALL,
    )

    # Write back if changed
    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"  ✅ Updated {file_path}")
        return True
    else:
        print(f"  ⏭️ No changes needed for {file_path}")
        return False


def main():
    """Update all API test files."""
    # Find all test files in API subdirectories
    test_files = []

    # Get all directories that contain APIs
    api_dirs = [d for d in os.listdir(".") if d.endswith("_api") and os.path.isdir(d)]

    for api_dir in api_dirs:
        test_pattern = os.path.join(api_dir, "*_test.py")
        test_files.extend(glob.glob(test_pattern))

    # Also check for test files in shared
    test_files.extend(glob.glob("shared/*_test.py"))

    print(f"Found {len(test_files)} test files to update:")
    for f in test_files:
        print(f"  - {f}")

    updated_count = 0
    for test_file in test_files:
        if update_test_file(test_file):
            updated_count += 1

    print(f"\n✅ Updated {updated_count} out of {len(test_files)} test files")


if __name__ == "__main__":
    main()
