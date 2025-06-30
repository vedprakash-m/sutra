#!/usr/bin/env python3
"""
Fix llm_execute_api tests to use create_auth_request consistently and fix auth issues.
"""

import re


def fix_llm_execute_tests():
    file_path = "/Users/vedprakashmishra/sutra/api/llm_execute_api/llm_execute_test.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix 1: Replace self.create_auth_request with create_auth_request
    content = re.sub(r'self\.create_auth_request', 'create_auth_request', content)
    
    # Fix 2: Replace func.HttpRequest with create_auth_request patterns
    # Simple GET requests
    content = re.sub(
        r'req = func\.HttpRequest\(\s*method="GET",\s*url="([^"]+)"\s*\)',
        r'req = create_auth_request(method="GET", url="\1")',
        content
    )
    
    # POST requests with body  
    content = re.sub(
        r'req = func\.HttpRequest\(\s*method="POST",\s*url="([^"]+)",\s*body=([^)]+)\s*\)',
        r'req = create_auth_request(method="POST", url="\1", body=\2)',
        content
    )
    
    # Fix 3: Handle multi-line func.HttpRequest patterns
    multiline_pattern = r'req = func\.HttpRequest\(\s*method="([^"]+)",\s*url="([^"]+)"(?:,\s*body=([^)]+))?\s*\)'
    
    def replace_multiline(match):
        method = match.group(1)
        url = match.group(2)
        body = match.group(3)
        
        if body:
            return f'req = create_auth_request(method="{method}", url="{url}", body={body})'
        else:
            return f'req = create_auth_request(method="{method}", url="{url}")'
    
    content = re.sub(multiline_pattern, replace_multiline, content, flags=re.MULTILINE | re.DOTALL)
    
    # Fix 4: Fix any remaining func.HttpRequest patterns manually
    # Look for specific patterns that might not be caught
    
    # Pattern for requests with headers
    content = re.sub(
        r'req = func\.HttpRequest\(\s*method="([^"]+)",\s*url="([^"]+)",\s*headers=([^,)]+)\s*\)',
        r'req = create_auth_request(method="\1", url="\2", headers=\3)',
        content
    )
    
    # Fix 5: Add auth_test_user parameter to test methods that need it
    # Look for test methods that use create_auth_request but don't have auth_test_user
    test_methods = re.findall(r'(async def test_\w+\([^)]*\):.*?)(?=async def|\Z)', content, re.DOTALL)
    
    for test_method in test_methods:
        if 'create_auth_request' in test_method and 'auth_test_user' not in test_method:
            # Extract the method signature
            signature_match = re.search(r'async def (test_\w+)\(([^)]*)\):', test_method)
            if signature_match:
                method_name = signature_match.group(1)
                current_params = signature_match.group(2)
                
                # Add auth_test_user parameter
                if current_params.strip():
                    new_params = current_params + ', auth_test_user'
                else:
                    new_params = 'self, auth_test_user'
                
                old_signature = f'async def {method_name}({current_params}):'
                new_signature = f'async def {method_name}({new_params}):'
                
                content = content.replace(old_signature, new_signature)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("Fixed llm_execute_api tests for unified auth")


if __name__ == "__main__":
    fix_llm_execute_tests()
