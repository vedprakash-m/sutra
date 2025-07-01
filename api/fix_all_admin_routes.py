#!/usr/bin/env python3
"""
Comprehensive script to fix all remaining admin test route parameter issues.
"""

import re
import os


def fix_remaining_admin_tests():
    """Fix all remaining admin tests with missing route parameters."""

    admin_test_file = "/Users/vedprakashmishra/sutra/api/admin_api/admin_test.py"

    # Read the current content
    with open(admin_test_file, "r") as f:
        content = f.read()

    # Define specific fixes for each test based on exact test function names
    fixes = [
        # Database health failure test - GET /api/admin/system/health
        {
            "find": 'async def test_get_system_health_database_failure(.*?)req = create_auth_request(method="GET")',
            "replace": 'async def test_get_system_health_database_failure\\1req = create_auth_request(\n            method="GET",\n            route_params={"resource": "system", "action": "health"}\n        )',
        },
        # User not found test - PUT /api/admin/users/{user_id}/role
        {
            "find": 'async def test_update_user_role_user_not_found(.*?)req = create_auth_request(method="PUT")',
            "replace": 'async def test_update_user_role_user_not_found\\1req = create_auth_request(\n            method="PUT",\n            route_params={"resource": "users", "action": "role", "user_id": target_user_id},\n            body=role_data\n        )',
        },
        # Search filter test - GET /api/admin/users
        {
            "find": 'async def test_list_users_with_search_filter(.*?)req = create_auth_request(method="GET")',
            "replace": 'async def test_list_users_with_search_filter\\1req = create_auth_request(\n            method="GET",\n            route_params={"resource": "users"}\n        )',
        },
        # Invalid JSON test - PUT /api/admin/users/{user_id}/role
        {
            "find": 'async def test_update_user_role_invalid_json(.*?)req = create_auth_request(method="PUT")',
            "replace": 'async def test_update_user_role_invalid_json\\1req = create_auth_request(\n            method="PUT",\n            route_params={"resource": "users", "action": "role", "user_id": target_user_id}\n        )',
        },
        # Reset test data - POST /api/admin/dev/reset
        {
            "find": 'async def test_reset_test_data_success(.*?)req = create_auth_request(method="POST")',
            "replace": 'async def test_reset_test_data_success\\1req = create_auth_request(\n            method="POST",\n            route_params={"resource": "dev", "action": "reset"}\n        )',
        },
        # Seed test data - POST /api/admin/dev/seed
        {
            "find": 'async def test_seed_test_data_success(.*?)req = create_auth_request(method="POST")',
            "replace": 'async def test_seed_test_data_success\\1req = create_auth_request(\n            method="POST",\n            route_params={"resource": "dev", "action": "seed"}\n        )',
        },
        # List users with masked API keys - GET /api/admin/users
        {
            "find": 'async def test_list_users_with_masked_api_keys(.*?)req = create_auth_request(method="GET")',
            "replace": 'async def test_list_users_with_masked_api_keys\\1req = create_auth_request(\n            method="GET",\n            route_params={"resource": "users"}\n        )',
        },
        # Production environment blocked - POST /api/admin/dev/reset
        {
            "find": 'async def test_test_data_production_environment_blocked(.*?)req = create_auth_request(method="POST")',
            "replace": 'async def test_test_data_production_environment_blocked\\1req = create_auth_request(\n            method="POST",\n            route_params={"resource": "dev", "action": "reset"}\n        )',
        },
    ]

    # Apply fixes using regex substitution
    updated_content = content
    for fix in fixes:
        pattern = fix["find"]
        replacement = fix["replace"]

        # Use re.DOTALL to match across lines
        updated_content = re.sub(pattern, replacement, updated_content, flags=re.DOTALL)
        print(f"Applied fix for: {pattern[:50]}...")

    # Also fix the non-admin access test to use regular user headers
    non_admin_fix = """        # Create non-admin request
        req = create_auth_request(
            method="GET",
            route_params={"resource": "users"},
            headers={"x-test-user-id": "regular-user-123", "x-test-user-role": "user"}
        )"""

    updated_content = re.sub(
        r'(async def test_non_admin_access_forbidden.*?)req = create_auth_request\(method="GET"\)',
        r"\\1" + non_admin_fix,
        updated_content,
        flags=re.DOTALL,
    )
    print("Applied non-admin access fix")

    # Write the updated content
    with open(admin_test_file, "w") as f:
        f.write(updated_content)

    print(f"Updated {admin_test_file}")


if __name__ == "__main__":
    fix_remaining_admin_tests()
