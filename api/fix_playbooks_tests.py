#!/usr/bin/env python3
"""
Fix all playbooks API tests to use correct HTTP methods and route parameters.
"""

import re


def fix_playbooks_tests():
    """Fix all playbooks tests systematically."""

    test_file = "/Users/vedprakashmishra/sutra/api/playbooks_api/playbooks_test.py"

    with open(test_file, "r") as f:
        content = f.read()

    # Define the test patterns and their fixes
    test_fixes = [
        # Run playbook tests - need POST to /{id}/run
        {
            "test_name": "test_run_playbook_success",
            "method": "POST",
            "route_params": '{"id": playbook_id}',
            "body": "execution_input",
            "url_pattern": "/run",
        },
        {
            "test_name": "test_run_playbook_missing_inputs",
            "method": "POST",
            "route_params": '{"id": playbook_id}',
            "body": "execution_input",
            "url_pattern": "/run",
        },
        # Update playbook tests - need PUT with /{id}
        {
            "test_name": "test_update_playbook_success",
            "method": "PUT",
            "route_params": '{"id": playbook_id}',
            "body": "update_data",
        },
        {
            "test_name": "test_update_playbook_not_found",
            "method": "PUT",
            "route_params": '{"id": playbook_id}',
            "body": "update_data",
        },
        {
            "test_name": "test_update_playbook_invalid_json",
            "method": "PUT",
            "route_params": '{"id": playbook_id}',
            "body": None,  # Will handle special case
            "invalid_json": True,
        },
        {
            "test_name": "test_update_playbook_validation_error",
            "method": "PUT",
            "route_params": '{"id": playbook_id}',
            "body": "update_data",
        },
        # Delete playbook tests - need DELETE with /{id}
        {
            "test_name": "test_delete_playbook_success",
            "method": "DELETE",
            "route_params": '{"id": playbook_id}',
        },
        {
            "test_name": "test_delete_playbook_not_found",
            "method": "DELETE",
            "route_params": '{"id": playbook_id}',
        },
        {
            "test_name": "test_delete_playbook_with_active_executions",
            "method": "DELETE",
            "route_params": '{"id": playbook_id}',
        },
        # Get playbook not found - need GET with /{id}
        {
            "test_name": "test_get_playbook_not_found",
            "method": "GET",
            "route_params": '{"id": playbook_id}',
        },
        # Execution status tests - need GET with execution route
        {
            "test_name": "test_get_execution_status_success",
            "method": "GET",
            "route_params": '{"execution_id": execution_id}',
            "url_pattern": "/executions",
        },
        {
            "test_name": "test_get_execution_status_not_found",
            "method": "GET",
            "route_params": '{"execution_id": execution_id}',
            "url_pattern": "/executions",
        },
        # Continue execution tests - need POST to /executions/{id}/continue
        {
            "test_name": "test_continue_execution_success",
            "method": "POST",
            "route_params": '{"execution_id": execution_id}',
            "body": "continue_data",
            "url_pattern": "/executions",
        },
        {
            "test_name": "test_continue_execution_invalid_status",
            "method": "POST",
            "route_params": '{"execution_id": execution_id}',
            "body": "{}",
            "url_pattern": "/executions",
        },
        {
            "test_name": "test_continue_execution_not_found",
            "method": "POST",
            "route_params": '{"execution_id": execution_id}',
            "body": "{}",
            "url_pattern": "/executions",
        },
        # Method not allowed test
        {
            "test_name": "test_method_not_allowed",
            "method": "PATCH",  # Unsupported method
            "route_params": None,
        },
    ]

    # Apply fixes systematically
    for fix in test_fixes:
        test_name = fix["test_name"]
        method = fix["method"]
        route_params = fix.get("route_params")
        body = fix.get("body")
        url_pattern = fix.get("url_pattern", "")

        print(f"Fixing {test_name}...")

        # Find and replace the create_auth_request call in each test
        if fix.get("invalid_json"):
            # Special case for invalid JSON test
            pattern = rf'(async def {test_name}.*?)(req = create_auth_request\(method="GET"\))'
            replacement = r'\1req = create_auth_request(method="PUT", route_params={"id": playbook_id}, body=\'{invalid_json\')'
        else:
            # Standard pattern
            pattern = rf'(async def {test_name}.*?)(req = create_auth_request\(method="GET"\))'

            # Build the replacement request
            request_parts = [f'method="{method}"']
            if route_params:
                request_parts.append(f"route_params={route_params}")
            if body:
                request_parts.append(f"body={body}")
            if url_pattern:
                request_parts.append(
                    f'url="http://localhost/api/playbooks{url_pattern}"'
                )

            request_call = f'req = create_auth_request({", ".join(request_parts)})'
            replacement = rf"\1{request_call}"

        content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Fix the method_not_allowed test missing mock_database_manager
    method_not_allowed_pattern = r'(async def test_method_not_allowed\(self, auth_test_user\):.*?)(with patch\("api\.playbooks_api\.get_database_manager", return_value=mock_database_manager\):)'
    method_not_allowed_replacement = r'\1# Create request with unsupported method\n        req = create_auth_request(method="PATCH")\n\n        # Act\n        response = await playbooks_main(req)\n\n        # Assert\n        assert response.status_code in [404, 405]  # Method not allowed or not found'

    content = re.sub(
        method_not_allowed_pattern,
        method_not_allowed_replacement,
        content,
        flags=re.DOTALL,
    )

    # Write the fixed content back
    with open(test_file, "w") as f:
        f.write(content)

    print("Fixed all playbooks tests!")


if __name__ == "__main__":
    fix_playbooks_tests()
