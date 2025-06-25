#!/usr/bin/env python3
"""
Script to fix body encoding issues in playbooks tests.
Removes .encode() calls and json.dumps() calls from body parameters.
"""

import re

def fix_body_encoding():
    file_path = "api/playbooks_api/playbooks_test.py"

    with open(file_path, 'r') as f:
        content = f.read()

    # Fix json.dumps().encode() patterns
    content = re.sub(
        r'body=json\.dumps\(([^)]+)\)\.encode\(\)',
        r'body=\1',
        content
    )

    # Fix cases where body is just json.dumps()
    content = re.sub(
        r'body=json\.dumps\(([^)]+)\)',
        r'body=\1',
        content
    )

    # Fix b"" empty body cases
    content = re.sub(
        r'body=b""',
        r'body=None',
        content
    )

    with open(file_path, 'w') as f:
        f.write(content)

    print("Fixed body encoding issues")

if __name__ == "__main__":
    fix_body_encoding()
