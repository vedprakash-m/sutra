#!/usr/bin/env python3

import os
import sys
import json
from datetime import datetime

# Add the API directory to Python path
sys.path.append('/Users/vedprakashmishra/sutra/api')

try:
    from shared.database import get_database_manager
    
    def find_and_promote_first_user():
        """Find the first/only user and make them admin"""
        try:
            print("🔍 Connecting to database...")
            db_manager = get_database_manager()
            container = db_manager.get_container("Users")
            
            print("📋 Querying for existing users...")
            # Query all users
            query = "SELECT * FROM c WHERE c.type = 'user'"
            users = list(container.query_items(query=query, enable_cross_partition_query=True))
            
            if not users:
                print("❌ No users found in database")
                print("ℹ️  This means you haven't logged in through the web app yet")
                print("   Please log in at: https://zealous-flower-04bbe021e.2.azurestaticapps.net")
                return False
            
            print(f"✅ Found {len(users)} user(s):")
            for i, user in enumerate(users, 1):
                print(f"   {i}. ID: {user['id']}")
                print(f"      Name: {user.get('name', 'Unknown')}")
                print(f"      Email: {user.get('email', 'Unknown')}")
                print(f"      Role: {user.get('role', 'user')}")
                print(f"      Created: {user.get('createdAt', 'Unknown')}")
                print()
            
            # If there's only one user, automatically promote them
            if len(users) == 1:
                user = users[0]
                if user.get('role') == 'admin':
                    print(f"✅ User {user['id']} is already an admin!")
                    return True
                
                print(f"🔄 Making user {user['id']} an admin...")
                user['role'] = 'admin'
                user['updatedAt'] = datetime.now().isoformat()
                user['approvalStatus'] = 'approved'
                
                container.upsert_item(user)
                
                print(f"🎉 Successfully promoted user to admin!")
                print(f"   User ID: {user['id']}")
                print(f"   Name: {user.get('name', 'Unknown')}")
                print(f"   Email: {user.get('email', 'Unknown')}")
                print(f"   Role: {user['role']}")
                print()
                print("📝 Next steps:")
                print("   1. Log out of the application")
                print("   2. Log in again to get updated roles")
                print("   3. Visit https://zealous-flower-04bbe021e.2.azurestaticapps.net/admin.html")
                return True
            
            # Multiple users - ask which one to promote
            else:
                print("🤔 Multiple users found. Which one is you?")
                while True:
                    try:
                        choice = int(input("Enter the number (1-{}): ".format(len(users))))
                        if 1 <= choice <= len(users):
                            user = users[choice - 1]
                            break
                        else:
                            print("❌ Invalid choice. Please try again.")
                    except ValueError:
                        print("❌ Please enter a valid number.")
                
                if user.get('role') == 'admin':
                    print(f"✅ User {user['id']} is already an admin!")
                    return True
                
                print(f"🔄 Making user {user['id']} an admin...")
                user['role'] = 'admin'
                user['updatedAt'] = datetime.now().isoformat()
                user['approvalStatus'] = 'approved'
                
                container.upsert_item(user)
                
                print(f"🎉 Successfully promoted user to admin!")
                print(f"   User ID: {user['id']}")
                print(f"   Name: {user.get('name', 'Unknown')}")
                print(f"   Email: {user.get('email', 'Unknown')}")
                print(f"   Role: {user['role']}")
                return True
                
        except Exception as e:
            print(f"❌ Database error: {str(e)}")
            return False
    
    if __name__ == "__main__":
        print("🔑 FIND AND PROMOTE ADMIN USER")
        print("===============================")
        print()
        
        success = find_and_promote_first_user()
        
        if success:
            print()
            print("✅ Admin setup complete!")
        else:
            print()
            print("❌ Admin setup failed!")
            sys.exit(1)

except ImportError as e:
    print(f"❌ Import error: {str(e)}")
    print("   Make sure you're running this from the correct directory")
    print("   and that the virtual environment is activated")
    sys.exit(1)
