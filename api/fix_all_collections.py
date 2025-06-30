#!/usr/bin/env python3
"""
Systematically fix all collections API tests using the proven pattern:
1. Use mock_database_manager fixture
2. Add local patch for api.collections_api.get_database_manager 
3. Configure return values properly
4. Add correct route parameters
"""

import re

def fix_all_collections_tests():
    """Apply the proven pattern to all collections tests."""
    
    test_file = "/Users/vedprakashmishra/sutra/api/collections_api/collections_test.py"
    
    with open(test_file, 'r') as f:
        content = f.read()
    
    # Pattern 1: Replace mock_cosmos_client with mock_database_manager in test signatures
    content = re.sub(
        r'async def (test_\w+)\(self, auth_test_user, mock_cosmos_client\)',
        r'async def \1(self, auth_test_user, mock_database_manager)',
        content
    )
    
    # Pattern 2: Add the local patch pattern to all tests that don't have it
    # Look for tests that have create_auth_request but no local patch
    test_methods = re.findall(r'(async def test_\w+.*?(?=async def|\Z))', content, re.DOTALL)
    
    for test_method in test_methods:
        # Skip if it already has the local patch
        if 'patch("api.collections_api.get_database_manager"' in test_method:
            continue
            
        # Skip if it doesn't use create_auth_request (might be a utility test)
        if 'create_auth_request(' not in test_method:
            continue
            
        # Find the create_auth_request call and wrap it in the patch
        old_pattern = r'(\s+)(req = create_auth_request\([^)]+\)\s*)(.*?)(# Act\s+response = await collections_main\(req\))'
        
        def replacement(match):
            indent = match.group(1)
            req_creation = match.group(2)
            middle_content = match.group(3)
            act_comment = match.group(4)
            
            return f'''{indent}# Additional patch to ensure we catch the right import
{indent}with patch("api.collections_api.get_database_manager", return_value=mock_database_manager):
{indent}    {req_creation.strip()}
{indent}    {middle_content.strip()}
{indent}    {act_comment}'''
        
        new_test_method = re.sub(old_pattern, replacement, test_method, flags=re.DOTALL)
        if new_test_method != test_method:
            content = content.replace(test_method, new_test_method)
    
    # Pattern 3: Replace mock_cosmos_client.* calls with mock_database_manager.*
    # Common patterns to replace:
    replacements = [
        (r'mock_cosmos_client\.query_items\.return_value = ', 'mock_database_manager.query_items.return_value = '),
        (r'mock_cosmos_client\.create_item\.return_value = ', 'mock_database_manager.create_item.return_value = '),
        (r'mock_cosmos_client\.update_item\.return_value = ', 'mock_database_manager.update_item.return_value = '),
        (r'mock_cosmos_client\.replace_item\.return_value = ', 'mock_database_manager.replace_item.return_value = '),
        (r'mock_cosmos_client\.delete_item\.return_value = ', 'mock_database_manager.delete_item.return_value = '),
        (r'mock_cosmos_client\.create_item\.assert_called_once\(\)', 'mock_database_manager.create_item.assert_called_once()'),
        (r'mock_cosmos_client\.update_item\.assert_called_once\(\)', 'mock_database_manager.update_item.assert_called_once()'),
        (r'mock_cosmos_client\.delete_item\.assert_called_once\(\)', 'mock_database_manager.delete_item.assert_called_once()'),
    ]
    
    for old_pattern, new_pattern in replacements:
        content = re.sub(old_pattern, new_pattern, content)
    
    # Write the updated content
    with open(test_file, 'w') as f:
        f.write(content)
    
    print(f"Applied systematic fixes to {test_file}")

if __name__ == "__main__":
    fix_all_collections_tests()
