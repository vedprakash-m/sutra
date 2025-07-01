#!/usr/bin/env python3
"""
Batch fix remaining playbooks tests
"""

import re


def batch_fix_remaining_tests():
    """Apply systematic fixes to remaining playbook tests."""

    test_file = "/Users/vedprakashmishra/sutra/api/playbooks_api/playbooks_test.py"

    with open(test_file, "r") as f:
        content = f.read()

    # List of test patterns to fix
    fixes = [
        # DELETE tests - need DELETE method + route params
        {
            "pattern": r"(async def test_delete_playbook_not_found\(\s*self, auth_test_user, mock_cosmos_client),\s*mock_auth_request",
            "replacement": r"\1",
        },
        {
            "pattern": r"(async def test_delete_playbook_with_active_executions\(\s*self, auth_test_user, mock_cosmos_client),\s*mock_auth_request",
            "replacement": r"\1",
        },
        # UPDATE tests - need PUT method + route params + body
        {
            "pattern": r"(async def test_update_playbook_not_found\(\s*self, auth_test_user, mock_cosmos_client),\s*mock_auth_request",
            "replacement": r"\1",
        },
        {
            "pattern": r"(async def test_update_playbook_invalid_json\(\s*self, auth_test_user, mock_cosmos_client),\s*mock_auth_request",
            "replacement": r"\1",
        },
        {
            "pattern": r"(async def test_update_playbook_validation_error\(\s*self, auth_test_user, mock_cosmos_client),\s*mock_auth_request",
            "replacement": r"\1",
        },
        # EXECUTION tests - need execution_id route params
        {
            "pattern": r"(async def test_get_execution_status_success\(\s*self, auth_test_user, mock_cosmos_client),\s*mock_auth_request",
            "replacement": r"\1",
        },
        {
            "pattern": r"(async def test_get_execution_status_not_found\(\s*self, auth_test_user, mock_cosmos_client),\s*mock_auth_request",
            "replacement": r"\1",
        },
        {
            "pattern": r"(async def test_continue_execution_success\(\s*self, auth_test_user, mock_cosmos_client),\s*mock_auth_request",
            "replacement": r"\1",
        },
        {
            "pattern": r"(async def test_continue_execution_invalid_status\(\s*self, auth_test_user, mock_cosmos_client),\s*mock_auth_request",
            "replacement": r"\1",
        },
        {
            "pattern": r"(async def test_continue_execution_not_found\(\s*self, auth_test_user, mock_cosmos_client),\s*mock_auth_request",
            "replacement": r"\1",
        },
        # METHOD test
        {
            "pattern": r"(async def test_method_not_allowed\(\s*self, auth_test_user),\s*mock_auth_request",
            "replacement": r"\1",
        },
    ]

    # Apply function signature fixes
    for fix in fixes:
        content = re.sub(fix["pattern"], fix["replacement"], content)

    # Now fix the request creation patterns
    request_fixes = [
        # Delete operations
        {
            "test_pattern": r"(test_delete_playbook_not_found.*?)req = mock_auth_request",
            "replacement": r'\1req = create_auth_request(method="DELETE", route_params={"id": playbook_id})',
        },
        {
            "test_pattern": r"(test_delete_playbook_with_active_executions.*?)req = mock_auth_request",
            "replacement": r'\1req = create_auth_request(method="DELETE", route_params={"id": playbook_id})',
        },
        # Update operations
        {
            "test_pattern": r"(test_update_playbook_not_found.*?)req = mock_auth_request",
            "replacement": r'\1req = create_auth_request(method="PUT", route_params={"id": playbook_id}, body=update_data)',
        },
        {
            "test_pattern": r"(test_update_playbook_invalid_json.*?)req = mock_auth_request",
            "replacement": r'\1req = create_auth_request(method="PUT", route_params={"id": playbook_id})',
        },
        {
            "test_pattern": r"(test_update_playbook_validation_error.*?)req = mock_auth_request",
            "replacement": r'\1req = create_auth_request(method="PUT", route_params={"id": playbook_id}, body=update_data)',
        },
        # Execution status (GET)
        {
            "test_pattern": r"(test_get_execution_status_success.*?)req = mock_auth_request",
            "replacement": r'\1req = create_auth_request(method="GET", route_params={"execution_id": execution_id}, url="http://localhost/api/playbooks/executions/" + execution_id)',
        },
        {
            "test_pattern": r"(test_get_execution_status_not_found.*?)req = mock_auth_request",
            "replacement": r'\1req = create_auth_request(method="GET", route_params={"execution_id": execution_id}, url="http://localhost/api/playbooks/executions/" + execution_id)',
        },
        # Continue execution (POST)
        {
            "test_pattern": r"(test_continue_execution_success.*?)req = mock_auth_request",
            "replacement": r'\1req = create_auth_request(method="POST", route_params={"execution_id": execution_id}, body=continue_data, url="http://localhost/api/playbooks/executions/" + execution_id + "/continue")',
        },
        {
            "test_pattern": r"(test_continue_execution_invalid_status.*?)req = mock_auth_request",
            "replacement": r'\1req = create_auth_request(method="POST", route_params={"execution_id": execution_id}, body={}, url="http://localhost/api/playbooks/executions/" + execution_id + "/continue")',
        },
        {
            "test_pattern": r"(test_continue_execution_not_found.*?)req = mock_auth_request",
            "replacement": r'\1req = create_auth_request(method="POST", route_params={"execution_id": execution_id}, body={}, url="http://localhost/api/playbooks/executions/" + execution_id + "/continue")',
        },
        # Method not allowed
        {
            "test_pattern": r"(test_method_not_allowed.*?)req = mock_auth_request",
            "replacement": r'\1req = create_auth_request(method="PATCH")  # Unsupported method',
        },
    ]

    # Apply request fixes
    for fix in request_fixes:
        content = re.sub(
            fix["test_pattern"], fix["replacement"], content, flags=re.DOTALL
        )

    with open(test_file, "w") as f:
        f.write(content)

    print("Applied batch fixes to remaining playbook tests!")


if __name__ == "__main__":
    batch_fix_remaining_tests()
