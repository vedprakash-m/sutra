#!/usr/bin/env python3
"""
Quick Admin Setup Script
Makes a user an admin by directly updating Cosmos DB
"""

import os
import sys
from datetime import datetime
import json

# Set up the environment
sys.path.append('/Users/vedprakashmishra/sutra/api')
os.chdir('/Users/vedprakashmishra/sutra/api')

# Load environment variables from local.settings.json
try:
    with open('local.settings.json', 'r') as f:
        settings = json.load(f)
        for key, value in settings.get('Values', {}).items():
            os.environ[key] = value
    print("✅ Loaded local environment settings")
except FileNotFoundError:
    print("⚠️  local.settings.json not found, using system environment")

try:
    from shared.database import get_database_manager
    
    def make_user_admin(user_id):
        """Make a user an admin"""
        try:
            print(f"🔧 Setting up admin role for: {user_id}")
            
            db_manager = get_database_manager()
            container = db_manager.get_container("Users")
            
            # Try to get existing user
            try:
                user_doc = container.read_item(item=user_id, partition_key=user_id)
                print(f"✅ Found existing user: {user_doc.get('name', 'Unknown')}")
            except:
                # Create new user document
                print("📝 Creating new user document...")
                user_doc = {
                    "id": user_id,
                    "name": "Administrator",
                    "email": user_id,
                    "role": "admin",
                    "identityProvider": "azureActiveDirectory",
                    "createdAt": datetime.now().isoformat(),
                    "lastLoginAt": datetime.now().isoformat(),
                    "updatedAt": datetime.now().isoformat(),
                    "type": "user",
                    "approvalStatus": "approved"
                }
            
            # Update role to admin
            user_doc["role"] = "admin"
            user_doc["approvalStatus"] = "approved"
            user_doc["updatedAt"] = datetime.now().isoformat()
            
            # Upsert the document
            container.upsert_item(user_doc)
            
            print(f"🎉 Successfully assigned admin role to user: {user_id}")
            print(f"   Name: {user_doc.get('name', 'Unknown')}")
            print(f"   Email: {user_doc.get('email', 'Unknown')}")
            print(f"   Role: {user_doc['role']}")
            print(f"   Status: {user_doc.get('approvalStatus', 'approved')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error assigning admin role: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    if __name__ == "__main__":
        user_id = "vedprakash.m@outlook.com"
        if make_user_admin(user_id):
            print("\n✅ Admin setup complete!")
            print("\nNext steps:")
            print("1. Log out of the application")
            print("2. Log in again to get updated roles")
            print("3. Visit https://zealous-flower-04bbe021e.2.azurestaticapps.net/admin.html")
        else:
            print("\n❌ Admin setup failed!")
            sys.exit(1)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the right directory and have the right dependencies")
    sys.exit(1)
