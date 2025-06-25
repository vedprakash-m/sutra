#!/usr/bin/env python3
"""
Script to fix the user role for Vedprakash.m@outlook.com
This script sets the user to admin role in the database.
"""
import asyncio
import os
import sys
from datetime import datetime

# Add the API path so we can import database modules
sys.path.append(os.path.join(os.path.dirname(__file__), "api"))

from shared.database import get_database_manager


async def fix_user_role():
    """Fix the user role for vedprakash.m@outlook.com"""
    try:
        db_manager = get_database_manager()

        # User ID as it appears in the system
        user_id = "vedprakash-m-outlook-com"

        print(f"Updating user {user_id} to admin role...")

        # First, check if user exists
        query = "SELECT * FROM c WHERE c.id = @user_id"
        parameters = [{"name": "@user_id", "value": user_id}]

        users = await db_manager.query_items(
            container_name="Users",
            query=query,
            parameters=parameters
        )

        if not users:
            print(f"User {user_id} not found in database")
            return

        user = users[0]
        print(f"Found user: {user.get('name', 'Unknown')} with current role: {user.get('role', 'Unknown')}")

        # Update the user's role to admin
        user['role'] = 'admin'
        user['updatedAt'] = datetime.now().isoformat()
        user['approvalStatus'] = 'approved'

        # Update in database
        updated_user = await db_manager.update_item(
            container_name="Users",
            item=user
        )

        print(f"Successfully updated user {user_id} to admin role")
        print(f"Updated user data: {updated_user}")

    except Exception as e:
        print(f"Error updating user role: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(fix_user_role())
