"""
Azure Static Web Apps Role Assignment Endpoint
This endpoint is called by Azure Static Web Apps to determine user roles.
"""

import json
import logging
import os
import sys
from datetime import datetime

import azure.functions as func

# Add the root directory to Python path for proper imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from shared.database import get_database_manager
from shared.models import UserRole

# Initialize logging
logger = logging.getLogger(__name__)


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Static Web Apps Role Assignment Endpoint

    This function is automatically called by Azure Static Web Apps
    after user authentication to determine the user's roles.

    Azure Static Web Apps passes user information via headers:
    - x-ms-client-principal-id: User ID
    - x-ms-client-principal-name: User display name
    - x-ms-client-principal-idp: Identity provider
    """
    try:
        # Get user information from Azure Static Web Apps headers
        user_id = req.headers.get("x-ms-client-principal-id")
        user_name = req.headers.get("x-ms-client-principal-name")
        identity_provider = req.headers.get("x-ms-client-principal-idp")

        logger.info(f"Role assignment request for user: {user_id} ({user_name})")

        if not user_id:
            logger.warning("No user ID provided in headers")
            return func.HttpResponse(
                json.dumps({"roles": ["user"]}),  # Default to user role
                status_code=200,
                mimetype="application/json",
            )

        try:
            # Get user from database to determine role
            db_manager = get_database_manager()

            # Try to get existing user using async database manager
            try:
                user_items = await db_manager.query_items(
                    container_name="Users",
                    query="SELECT * FROM c WHERE c.id = @user_id",
                    parameters=[{"name": "@user_id", "value": user_id}],
                )

                if user_items:
                    user_doc = user_items[0]
                    user_role = user_doc.get("role", "user")

                    # Special case: Force admin role for specific user in development
                    if user_name and user_name.lower() == "vedprakash.m@outlook.com":
                        user_role = "admin"
                        # Update the database record if it's not already admin
                        if user_doc.get("role") != "admin":
                            user_doc["role"] = "admin"
                            user_doc["approvalStatus"] = "approved"
                            user_doc["updatedAt"] = datetime.now().isoformat()
                            # In development mode, just log the change (since database is mocked)
                            logger.info(f"DEVELOPMENT: Setting {user_name} as admin user")

                    logger.info(f"Found existing user {user_id} with role: {user_role}")

                    # Update last login time (only in non-dev mode to avoid database calls)
                    if not db_manager._development_mode:
                        user_doc["lastLoginAt"] = datetime.now().isoformat()
                        user_doc["updatedAt"] = datetime.now().isoformat()

                        await db_manager.update_item(container_name="Users", item=user_doc)
                else:
                    # User doesn't exist - implement approval system
                    # Check if this is the first user (make them admin) or require approval

                    # Check if any admin users exist
                    admin_users = await db_manager.query_items(
                        container_name="Users",
                        query="SELECT * FROM c WHERE c.role = 'admin'",
                        parameters=[],
                    )

                    # Special case: Make vedprakash.m@outlook.com admin regardless
                    if user_name and user_name.lower() == "vedprakash.m@outlook.com":
                        user_role = "admin"
                        logger.info(f"Making {user_name} admin (special admin user)")
                    elif not admin_users:
                        # No admin users exist, make this user an admin (first user)
                        user_role = "admin"
                        logger.info(f"No admin users found, making {user_id} the first admin")
                    else:
                        # Admin users exist, new users need approval
                        user_role = "pending_approval"
                        logger.info(f"Admin users exist, new user {user_id} requires approval")

                    user_doc = {
                        "id": user_id,
                        "name": user_name or "Unknown User",
                        "email": user_name or f"{user_id}@unknown.com",
                        "role": user_role,
                        "identityProvider": identity_provider or "azureActiveDirectory",
                        "createdAt": datetime.now().isoformat(),
                        "lastLoginAt": datetime.now().isoformat(),
                        "updatedAt": datetime.now().isoformat(),
                        "type": "user",
                        "approvalStatus": "pending" if user_role == "pending_approval" else "approved",
                    }

                    await db_manager.create_item(container_name="Users", item=user_doc, partition_key=user_id)
                    logger.info(f"Created new user {user_id} with role: {user_role}")
            except Exception as user_error:
                logger.error(f"Error handling user {user_id}: {str(user_error)}")
                # Default to user role if there's an error
                user_role = "user"

            # Return roles array as expected by Azure Static Web Apps
            if user_role == "pending_approval":
                roles = ["anonymous"]  # Restrict access for pending users
            else:
                roles = [user_role]

            # Add any additional roles based on business logic
            if user_role == "admin":
                roles.append("user")  # Admins also have user permissions

            response_data = {"roles": roles}
            logger.info(f"Returning roles for user {user_id}: {roles}")

            return func.HttpResponse(json.dumps(response_data), status_code=200, mimetype="application/json")

        except Exception as db_error:
            logger.error(f"Database error in role assignment: {str(db_error)}")
            # Fallback to default user role if database fails
            return func.HttpResponse(
                json.dumps({"roles": ["user"]}),
                status_code=200,
                mimetype="application/json",
            )

    except Exception as e:
        logger.error(f"Error in getroles endpoint: {str(e)}")
        # Always return a valid response with default role
        return func.HttpResponse(
            json.dumps({"roles": ["user"]}),
            status_code=200,
            mimetype="application/json",
        )
