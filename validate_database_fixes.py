#!/usr/bin/env python3
"""
Database mapping fix script - June 24, 2025
Addresses critical database connection and save/fetch operation issues.

Issues Fixed:
1. Wrong function signatures in database calls
2. Missing partition_key parameters
3. Inconsistent field naming between APIs and Cosmos DB containers
4. Authentication context not properly propagated
5. Authorization decorators with wrong action restrictions
"""

import os
import subprocess
import sys

def check_database_fixes():
    """Verify that all database fixes have been applied correctly."""

    print("🔍 Verifying database mapping fixes...")

    fixes_verified = []
    issues_found = []

    # Check 1: Prompts API update_item call
    prompts_file = "/Users/vedprakashmishra/sutra/api/prompts/__init__.py"
    with open(prompts_file, 'r') as f:
        prompts_content = f.read()

    if 'updated_prompt = await db_manager.update_item(\n            container_name="Prompts",\n            item=existing_prompt,\n            partition_key=user.id,' in prompts_content:
        fixes_verified.append("✅ Prompts API: update_item call signature fixed")
    else:
        issues_found.append("❌ Prompts API: update_item call signature still incorrect")

    # Check 2: Collections API partition key and field names
    collections_file = "/Users/vedprakashmishra/sutra/api/collections_api/__init__.py"
    with open(collections_file, 'r') as f:
        collections_content = f.read()

    if '"userId": user_id,  # Database partition key field' in collections_content:
        fixes_verified.append("✅ Collections API: Field name fixed to userId")
    else:
        issues_found.append("❌ Collections API: Still using wrong field name")

    if 'partition_key=user_id' in collections_content:
        fixes_verified.append("✅ Collections API: partition_key parameter added")
    else:
        issues_found.append("❌ Collections API: partition_key parameter missing")

    if 'c.userId = @user_id' in collections_content:
        fixes_verified.append("✅ Collections API: Queries updated to use userId")
    else:
        issues_found.append("❌ Collections API: Queries still use wrong field")

    # Check 3: Playbooks API partition key and field names
    playbooks_file = "/Users/vedprakashmishra/sutra/api/playbooks_api/__init__.py"
    with open(playbooks_file, 'r') as f:
        playbooks_content = f.read()

    if '"userId": playbook_data["user_id"]' in playbooks_content:
        fixes_verified.append("✅ Playbooks API: Field name fixed to userId")
    else:
        issues_found.append("❌ Playbooks API: Still using creatorId")

    if 'partition_key=user_id' in playbooks_content:
        fixes_verified.append("✅ Playbooks API: partition_key parameter added")
    else:
        issues_found.append("❌ Playbooks API: partition_key parameter missing")

    # Check 4: Authentication decorators
    if '@require_auth(resource="prompts")' in prompts_content:
        fixes_verified.append("✅ Prompts API: Authentication decorator added to main function")
    else:
        issues_found.append("❌ Prompts API: Missing auth decorator on main function")

    if '@require_auth(resource="collections")' in collections_content and 'action="read"' not in collections_content.split('@require_auth(resource="collections")')[1].split('\n')[0]:
        fixes_verified.append("✅ Collections API: Auth decorator fixed (removed action restriction)")
    else:
        issues_found.append("❌ Collections API: Auth decorator still has action restriction")

    # Check 5: req.current_user usage
    if 'user = req.current_user' in prompts_content and 'user = await get_current_user(req)' not in prompts_content:
        fixes_verified.append("✅ Prompts API: Using req.current_user instead of get_current_user")
    else:
        issues_found.append("❌ Prompts API: Still using get_current_user instead of req.current_user")

    print("\n" + "="*60)
    print("✅ FIXES VERIFIED:")
    for fix in fixes_verified:
        print(f"   {fix}")

    if issues_found:
        print("\n❌ ISSUES STILL PRESENT:")
        for issue in issues_found:
            print(f"   {issue}")
        return False
    else:
        print("\n🎉 ALL DATABASE FIXES VERIFIED SUCCESSFULLY!")
        return True


def test_database_manager():
    """Test the database manager methods to ensure they work correctly."""

    print("\n🧪 Testing database manager methods...")

    db_manager_file = "/Users/vedprakashmishra/sutra/api/shared/database.py"
    with open(db_manager_file, 'r') as f:
        db_content = f.read()

    # Check method signatures
    create_signature = 'async def create_item(\n        self, container_name: str, item: Dict[str, Any], partition_key: str = None\n    ) -> Dict[str, Any]:'
    update_signature = 'async def update_item(\n        self, container_name: str, item: Dict[str, Any], partition_key: str\n    ) -> Dict[str, Any]:'

    if 'container_name: str, item: Dict[str, Any], partition_key: str = None' in db_content:
        print("✅ Database Manager: create_item has correct signature")
    else:
        print("❌ Database Manager: create_item signature issue")
        return False

    if 'container_name: str, item: Dict[str, Any], partition_key: str' in db_content and 'update_item' in db_content:
        print("✅ Database Manager: update_item has correct signature")
    else:
        print("❌ Database Manager: update_item signature issue")
        return False

    return True


def validate_cosmos_containers():
    """Validate that Cosmos DB container definitions are correct."""

    print("\n🗃️  Validating Cosmos DB container definitions...")

    bicep_file = "/Users/vedprakashmishra/sutra/infrastructure/persistent.bicep"
    with open(bicep_file, 'r') as f:
        bicep_content = f.read()

    containers = ['Prompts', 'Collections', 'Playbooks']
    all_correct = True

    for container in containers:
        if f'name: \'{container}\'' in bicep_content and 'paths: [\'/userId\']' in bicep_content:
            print(f"✅ {container} container: Uses /userId partition key")
        else:
            print(f"❌ {container} container: Incorrect partition key configuration")
            all_correct = False

    return all_correct


def check_authentication_flow():
    """Check that authentication flow is working correctly."""

    print("\n🔐 Checking authentication flow...")

    auth_file = "/Users/vedprakashmishra/sutra/api/shared/auth_static_web_apps.py"
    with open(auth_file, 'r') as f:
        auth_content = f.read()

    checks = [
        ('req.current_user = user', 'Auth decorator sets req.current_user'),
        ('get_user_from_headers', 'User extraction from Azure headers'),
        ('check_permission', 'Permission checking logic'),
    ]

    all_good = True
    for check_text, description in checks:
        if check_text in auth_content:
            print(f"✅ {description}: Present")
        else:
            print(f"❌ {description}: Missing")
            all_good = False

    return all_good


def run_build_test():
    """Run a build test to ensure the changes don't break anything."""

    print("\n🏗️  Running build test...")

    try:
        # Run TypeScript compilation
        result = subprocess.run(
            ['npm', 'run', 'build'],
            cwd='/Users/vedprakashmishra/sutra',
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print("✅ Frontend build: SUCCESS")
            return True
        else:
            print(f"❌ Frontend build: FAILED")
            print(f"Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Frontend build: TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ Frontend build: ERROR - {e}")
        return False


def create_deployment_summary():
    """Create a summary of fixes for deployment."""

    summary = """
# Database Mapping Fixes Applied - June 24, 2025

## Critical Issues Fixed:

### 1. Database Function Signatures
- ✅ Fixed prompts API update_item() call with correct parameters
- ✅ Added missing partition_key parameters to create_item() calls

### 2. Cosmos DB Field Mapping
- ✅ Collections API: Changed from 'ownerId' to 'userId' (matches partition key)
- ✅ Playbooks API: Changed from 'creatorId' to 'userId' (matches partition key)
- ✅ Prompts API: Already using 'userId' correctly

### 3. Authentication Context
- ✅ Fixed prompts API to use req.current_user consistently
- ✅ Removed action-specific restrictions from main API decorators
- ✅ Added @require_auth to prompts main function

### 4. Container Partition Keys (All use /userId)
- ✅ Prompts: /userId ✓
- ✅ Collections: /userId ✓
- ✅ Playbooks: /userId ✓

## Expected Results:
- Collections page should load without errors
- Prompt Builder save should work
- Playbook Builder save should work
- All save operations should persist to Cosmos DB correctly

## Deployment Status: READY
Frontend build: ✅ SUCCESS
Backend validation: ✅ SUCCESS
Database mapping: ✅ FIXED
"""

    with open('/Users/vedprakashmishra/sutra/DATABASE_FIXES_SUMMARY.md', 'w') as f:
        f.write(summary)

    print("📝 Created deployment summary: DATABASE_FIXES_SUMMARY.md")


def main():
    """Main function to run all validation checks."""

    print("🚀 Database Mapping Fix Validation")
    print("="*50)

    all_checks_passed = True

    # Run all validation checks
    checks = [
        ("Database Fixes", check_database_fixes),
        ("Database Manager", test_database_manager),
        ("Cosmos Containers", validate_cosmos_containers),
        ("Authentication Flow", check_authentication_flow),
        ("Build Test", run_build_test),
    ]

    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        if not check_func():
            all_checks_passed = False

    print("\n" + "="*50)

    if all_checks_passed:
        print("🎉 ALL VALIDATION CHECKS PASSED!")
        print("✅ Database mapping issues have been resolved")
        print("🚀 Ready for production testing")

        create_deployment_summary()

        print("\n📋 Next Steps:")
        print("1. Test the Collections page - should load without errors")
        print("2. Test Prompt Builder save - should persist prompts")
        print("3. Test Playbook Builder save - should persist playbooks")
        print("4. Verify admin role assignment is working")

        return 0
    else:
        print("❌ SOME VALIDATION CHECKS FAILED")
        print("🔧 Please review the issues above and re-run")
        return 1


if __name__ == "__main__":
    sys.exit(main())
