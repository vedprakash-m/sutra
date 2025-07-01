#!/usr/bin/env python3
"""
Script to systematically fix admin test route parameters
"""

import re

# Read the current admin test file
with open("admin_api/admin_test.py", "r") as f:
    content = f.read()

# Define the route parameter mappings based on test names and expected endpoints
route_mappings = [
    # Users endpoints
    ("test_list_users", 'route_params={"resource": "users"}'),
    (
        "test_update_user_role",
        'route_params={"resource": "users", "action": "role", "user_id": target_user_id}',
    ),
    ("test.*users.*filter", 'route_params={"resource": "users"}'),
    ("test.*users.*masked", 'route_params={"resource": "users"}'),
    # System endpoints
    (
        "test_get_system_health",
        'route_params={"resource": "system", "action": "health"}',
    ),
    ("test_get_system_stats", 'route_params={"resource": "system", "action": "stats"}'),
    (
        "test_set_maintenance_mode",
        'route_params={"resource": "system", "action": "maintenance"}',
    ),
    # LLM endpoints
    ("test_get_llm_settings", 'route_params={"resource": "llm", "action": "settings"}'),
    (
        "test_update_llm_settings",
        'route_params={"resource": "llm", "action": "settings"}',
    ),
    # Usage endpoints
    ("test_get_usage_stats", 'route_params={"resource": "usage"}'),
    # Test data endpoints
    (
        "test_reset_test_data",
        'route_params={"resource": "system", "action": "reset-test-data"}',
    ),
    (
        "test_seed_test_data",
        'route_params={"resource": "system", "action": "seed-test-data"}',
    ),
]

# Pattern to find create_auth_request calls
pattern = r'(req = create_auth_request\(method="[^"]*")\)'


def determine_route_params(method_name, existing_match):
    """Determine the appropriate route parameters for a test method"""
    for test_pattern, route_params in route_mappings:
        if re.search(test_pattern, method_name):
            return route_params
    return "route_params={}"  # default fallback


# Split content into lines to process method by method
lines = content.split("\n")
current_method = None
modified_lines = []

for i, line in enumerate(lines):
    # Track current method name
    if "async def test_" in line:
        current_method = line.strip()

    # Check if this line contains create_auth_request
    if "req = create_auth_request(" in line and "route_params" not in line:
        if current_method:
            method_name = current_method
            route_params = determine_route_params(method_name, line)

            # Handle different patterns
            if line.strip().endswith(")"):
                # Simple case: req = create_auth_request(method="GET")
                modified_line = line.replace(")", f", {route_params})")
            else:
                # Multi-line case - add route_params before the closing )
                modified_line = line.replace(")", f", {route_params})")

            modified_lines.append(modified_line)
            print(f"Updated {method_name}: {modified_line.strip()}")
        else:
            modified_lines.append(line)
    else:
        modified_lines.append(line)

# Write back the modified content
modified_content = "\n".join(modified_lines)

# Special cases that need body parameter as well
body_fixes = [
    (
        r"(test_update_user_role.*?req = create_auth_request\([^)]*\))",
        lambda m: m.group(1).replace(")", ", body=new_role_data)")
        if "body=" not in m.group(1)
        else m.group(1),
    ),
    (
        r"(test_update_llm_settings.*?req = create_auth_request\([^)]*\))",
        lambda m: m.group(1).replace(")", ", body=new_settings)")
        if "body=" not in m.group(1)
        else m.group(1),
    ),
    (
        r"(test_set_maintenance_mode.*?req = create_auth_request\([^)]*\))",
        lambda m: m.group(1).replace(")", ", body=maintenance_data)")
        if "body=" not in m.group(1)
        else m.group(1),
    ),
]

for pattern, replacement in body_fixes:
    modified_content = re.sub(pattern, replacement, modified_content, flags=re.DOTALL)

with open("admin_api/admin_test.py", "w") as f:
    f.write(modified_content)

print("Admin tests have been updated with route parameters!")
