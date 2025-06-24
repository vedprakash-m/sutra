#!/bin/bash

# Admin User Assignment Script
# This script helps assign admin role to specific users

echo "🔑 ADMIN USER ASSIGNMENT"
echo "========================"
echo

# First, let's get your user ID by having you log in
echo "To assign admin role, we need your user ID from Azure Static Web Apps."
echo "Please:"
echo "1. Log in to your application: https://zealous-flower-04bbe021e.2.azurestaticapps.net"
echo "2. After logging in, visit: https://zealous-flower-04bbe021e.2.azurestaticapps.net/.auth/me"
echo "3. Copy your 'userId' from the JSON response"
echo

read -p "Enter your User ID: " USER_ID

if [ -z "$USER_ID" ]; then
    echo "❌ User ID is required"
    exit 1
fi

echo "Setting up admin role for user: $USER_ID"

# Create a simple Python script to update the user role
cat > /tmp/set_admin_role.py << EOF
import os
import sys
sys.path.append('/Users/vedprakashmishra/sutra/api')

from shared.database import get_database_manager
from datetime import datetime

def set_admin_role(user_id):
    try:
        db_manager = get_database_manager()
        container = db_manager.get_container("Users")

        # Try to get existing user
        try:
            user_doc = container.read_item(item=user_id, partition_key=user_id)
            print(f"Found existing user: {user_doc.get('name', 'Unknown')}")
        except:
            # Create new user document
            user_doc = {
                "id": user_id,
                "name": "Administrator",
                "email": "admin@sutra.app",
                "role": "admin",
                "identityProvider": "azureActiveDirectory",
                "createdAt": datetime.now().isoformat(),
                "lastLoginAt": datetime.now().isoformat(),
                "updatedAt": datetime.now().isoformat(),
                "type": "user"
            }

        # Update role to admin
        user_doc["role"] = "admin"
        user_doc["updatedAt"] = datetime.now().isoformat()

        # Upsert the document
        container.upsert_item(user_doc)

        print(f"✅ Successfully assigned admin role to user: {user_id}")
        print(f"   Name: {user_doc.get('name', 'Unknown')}")
        print(f"   Role: {user_doc['role']}")

    except Exception as e:
        print(f"❌ Error assigning admin role: {str(e)}")
        return False

    return True

if __name__ == "__main__":
    user_id = "$USER_ID"
    set_admin_role(user_id)
EOF

# Run the Python script
cd /Users/vedprakashmishra/sutra
if /Users/vedprakashmishra/sutra/.venv/bin/python /tmp/set_admin_role.py; then
    echo
    echo "🎉 Admin role assigned successfully!"
    echo
    echo "Next steps:"
    echo "1. Log out of the application"
    echo "2. Log in again to get updated roles"
    echo "3. You should now have access to admin features"
    echo "4. Visit /admin to configure API keys and monitor costs"
else
    echo "❌ Failed to assign admin role"
    exit 1
fi

# Clean up
rm -f /tmp/set_admin_role.py

echo
echo "✅ Admin setup complete!"
EOF
