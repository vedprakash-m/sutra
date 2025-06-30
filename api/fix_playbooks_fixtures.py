#!/usr/bin/env python3
"""
Fix remaining playbooks API test patterns systematically.
"""

import re

def fix_playbooks_test_fixtures():
    """Fix playbooks tests to use create_auth_request instead of mock_auth_request."""
    
    test_file = "/Users/vedprakashmishra/sutra/api/playbooks_api/playbooks_test.py"
    
    with open(test_file, 'r') as f:
        content = f.read()
    
    # Fix 1: Remove mock_auth_request from function parameters
    content = re.sub(
        r'(async def test_\w+\(\s*self,\s*auth_test_user,\s*mock_cosmos_client),\s*mock_auth_request',
        r'\1',
        content
    )
    
    # Fix 2: Replace req = mock_auth_request with appropriate create_auth_request calls
    
    # For simple GET requests (like get_playbook tests)
    content = re.sub(
        r'req = mock_auth_request\s*\n\s*# Act\s*\n\s*response = await playbooks_main\(req\)',
        '''req = create_auth_request(method="GET", route_params={"id": playbook_id})
        
        # Act
        response = await playbooks_main(req)''',
        content,
        flags=re.MULTILINE
    )
    
    # For DELETE requests
    content = re.sub(
        r'(\s+)req = mock_auth_request(\s+# Act\s+response = await playbooks_main\(req\))',
        r'\1req = create_auth_request(method="DELETE", route_params={"id": playbook_id})\2',
        content
    )
    
    # For PUT requests with body data
    content = re.sub(
        r'(\s+)req = mock_auth_request(\s+# Act\s+response = await playbooks_main\(req\))',
        r'\1req = create_auth_request(method="PUT", route_params={"id": playbook_id}, body=update_data)\2',
        content
    )
    
    with open(test_file, 'w') as f:
        f.write(content)
    
    print("Fixed playbooks test patterns!")

if __name__ == "__main__":
    fix_playbooks_test_fixtures()
