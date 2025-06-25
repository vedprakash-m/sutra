#!/usr/bin/env python3
"""
Script to fix malformed route_params in playbooks tests.
"""

import re

def fix_route_params():
    """Fix malformed route_params in playbooks tests."""

    test_file = "/Users/vedprakashmishra/sutra/api/playbooks_api/playbooks_test.py"

    # Read the file
    with open(test_file, 'r') as f:
        content = f.read()

    # Fix malformed route_params patterns
    # Pattern 1: route_params={{"id": playbook_id},} if "{"id": playbook_id}," else {}
    content = re.sub(
        r'route_params=\{\{"id": playbook_id\},\} if "\{"id": playbook_id\}," else \{\}',
        'route_params={"id": playbook_id}',
        content
    )

    # Pattern 2: route_params={{"execution_id": execution_id},} if "{"execution_id": execution_id}," else {}
    content = re.sub(
        r'route_params=\{\{"execution_id": execution_id\},\} if "\{"execution_id": execution_id\}," else \{\}',
        'route_params={"execution_id": execution_id}',
        content
    )

    # Pattern 3: Any other malformed route_params with similar structure
    content = re.sub(
        r'route_params=\{\{([^}]+)\},\} if "[^"]+" else \{\}',
        r'route_params={\1}',
        content
    )

    # Pattern 4: route_params=None should be route_params={}
    content = re.sub(
        r'route_params=None',
        'route_params={}',
        content
    )

    # Pattern 5: body=None should be body=None (this is correct)
    # Pattern 6: body={} should be body=None for GET/DELETE requests with no body
    content = re.sub(
        r'method="(GET|DELETE)",\s*url=([^,]+),\s*body=\{\}',
        r'method="\1",\n                url=\2,\n                body=None',
        content
    )

    # Write the file back
    with open(test_file, 'w') as f:
        f.write(content)

    print("Fixed route_params formatting issues")

if __name__ == "__main__":
    fix_route_params()
