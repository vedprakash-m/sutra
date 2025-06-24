"""
Azure Static Web Apps Role Assignment Endpoint
This endpoint is called by Azure Static Web Apps to determine user roles.
"""

import azure.functions as func
import json
import logging
import os
import sys
from datetime import datetime

# Add the root directory to Python path for proper imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from shared.database import get_database_manager
from shared.models import UserRole

# Initialize logging
logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
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
                mimetype="application/json"
            )

        try:
            # Get user from database to determine role
            db_manager = get_database_manager()
            container = db_manager.get_container("Users")

            # Try to get existing user
            try:
                user_doc = container.read_item(item=user_id, partition_key=user_id)
                user_role = user_doc.get("role", "user")
                logger.info(f"Found existing user {user_id} with role: {user_role}")
            except:
                # User doesn't exist - implement approval system
                # Check if this is the first user (make them admin) or require approval

                # Check if any admin users exist
                query = "SELECT * FROM c WHERE c.role = 'admin'"
                admin_users = list(container.query_items(query=query, enable_cross_partition_query=True))

                if not admin_users:
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
                    "approvalStatus": "pending" if user_role == "pending_approval" else "approved"
                }

                container.create_item(user_doc)
                logger.info(f"Created new user {user_id} with role: {user_role}")

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

            return func.HttpResponse(
                json.dumps(response_data),
                status_code=200,
                mimetype="application/json"
            )

        except Exception as db_error:
            logger.error(f"Database error in role assignment: {str(db_error)}")
            # Fallback to default user role if database fails
            return func.HttpResponse(
                json.dumps({"roles": ["user"]}),
                status_code=200,
                mimetype="application/json"
            )

    except Exception as e:
        logger.error(f"Error in getroles endpoint: {str(e)}")
        # Always return a valid response with default role
        return func.HttpResponse(
            json.dumps({"roles": ["user"]}),
            status_code=200,
            mimetype="application/json"
        )
