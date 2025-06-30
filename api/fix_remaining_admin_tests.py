#!/usr/bin/env python3
"""
Script to fix remaining admin tests that are missing route parameters.
"""

import re
import os

def fix_admin_tests():
    """Fix admin tests by adding missing route parameters."""
    
    admin_test_file = "/Users/vedprakashmishra/sutra/api/admin_api/admin_test.py"
    
    # Read the current content
    with open(admin_test_file, 'r') as f:
        content = f.read()
    
    # Define patterns and their fixes
    fixes = [
        # update_llm_settings - PUT /api/admin/llm/settings
        {
            'pattern': r'(async def test_update_llm_settings_success.*?req = create_auth_request\(method="PUT"\))',
            'replacement': lambda m: m.group(1).replace(
                'req = create_auth_request(method="PUT")',
                '''req = create_auth_request(
            method="PUT",
            route_params={"resource": "llm", "action": "settings"},
            body=updated_settings
        )'''
            )
        },
        # get_guest_settings - GET /api/admin/guest/settings
        {
            'pattern': r'(async def test_get_guest_settings_success.*?req = create_auth_request\(method="GET"\))',
            'replacement': lambda m: m.group(1).replace(
                'req = create_auth_request(method="GET")',
                '''req = create_auth_request(
            method="GET",
            route_params={"resource": "guest", "action": "settings"}
        )'''
            )
        },
        # update_guest_settings - PUT /api/admin/guest/settings
        {
            'pattern': r'(async def test_update_guest_settings_success.*?req = create_auth_request\(method="PUT"\))',
            'replacement': lambda m: m.group(1).replace(
                'req = create_auth_request(method="PUT")',
                '''req = create_auth_request(
            method="PUT",
            route_params={"resource": "guest", "action": "settings"},
            body=updated_settings
        )'''
            )
        },
        # delete_user - DELETE /api/admin/users/{user_id}
        {
            'pattern': r'(async def test_delete_user_success.*?req = create_auth_request\(method="DELETE"\))',
            'replacement': lambda m: m.group(1).replace(
                'req = create_auth_request(method="DELETE")',
                '''req = create_auth_request(
            method="DELETE",
            route_params={"resource": "users", "user_id": target_user_id}
        )'''
            )
        },
        # get_user_details - GET /api/admin/users/{user_id}
        {
            'pattern': r'(async def test_get_user_details_success.*?req = create_auth_request\(method="GET"\))',
            'replacement': lambda m: m.group(1).replace(
                'req = create_auth_request(method="GET")',
                '''req = create_auth_request(
            method="GET",
            route_params={"resource": "users", "user_id": target_user_id}
        )'''
            )
        },
        # reset_user_password - POST /api/admin/users/{user_id}/reset-password
        {
            'pattern': r'(async def test_reset_user_password_success.*?req = create_auth_request\(method="POST"\))',
            'replacement': lambda m: m.group(1).replace(
                'req = create_auth_request(method="POST")',
                '''req = create_auth_request(
            method="POST",
            route_params={"resource": "users", "user_id": target_user_id, "action": "reset-password"},
            body=reset_data
        )'''
            )
        },
        # audit_logs - GET /api/admin/audit/logs
        {
            'pattern': r'(async def test_get_audit_logs_success.*?req = create_auth_request\(method="GET"\))',
            'replacement': lambda m: m.group(1).replace(
                'req = create_auth_request(method="GET")',
                '''req = create_auth_request(
            method="GET",
            route_params={"resource": "audit", "action": "logs"}
        )'''
            )
        },
        # get_security_events - GET /api/admin/security/events
        {
            'pattern': r'(async def test_get_security_events_success.*?req = create_auth_request\(method="GET"\))',
            'replacement': lambda m: m.group(1).replace(
                'req = create_auth_request(method="GET")',
                '''req = create_auth_request(
            method="GET",
            route_params={"resource": "security", "action": "events"}
        )'''
            )
        },
        # system_backup - POST /api/admin/system/backup
        {
            'pattern': r'(async def test_create_system_backup_success.*?req = create_auth_request\(method="POST"\))',
            'replacement': lambda m: m.group(1).replace(
                'req = create_auth_request(method="POST")',
                '''req = create_auth_request(
            method="POST",
            route_params={"resource": "system", "action": "backup"},
            body=backup_request
        )'''
            )
        }
    ]
    
    # Apply fixes
    updated_content = content
    for fix in fixes:
        pattern = fix['pattern']
        replacement = fix['replacement']
        
        # Use re.DOTALL to match across lines
        matches = list(re.finditer(pattern, updated_content, re.DOTALL))
        if matches:
            for match in reversed(matches):  # Reverse to maintain positions
                new_text = replacement(match)
                updated_content = updated_content[:match.start()] + new_text + updated_content[match.end():]
            print(f"Applied fix for pattern: {pattern[:50]}...")
    
    # Write the updated content
    with open(admin_test_file, 'w') as f:
        f.write(updated_content)
    
    print(f"Updated {admin_test_file}")

if __name__ == "__main__":
    fix_admin_tests()
