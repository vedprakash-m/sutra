#!/usr/bin/env python3
"""
Script to fix database container method calls in playbooks tests.
Updates get_executions_container() to get_container("Executions")
"""

import re

def fix_container_calls():
    file_path = "api/playbooks_api/playbooks_test.py"

    with open(file_path, 'r') as f:
        content = f.read()

    # Replace get_executions_container() calls
    content = content.replace(
        '.get_executions_container()',
        '.get_container("Executions")'
    )

    # Replace get_playbooks_container() calls
    content = content.replace(
        '.get_playbooks_container()',
        '.get_container("Playbooks")'
    )

    with open(file_path, 'w') as f:
        f.write(content)

    print("Fixed database container method calls")

if __name__ == "__main__":
    fix_container_calls()
