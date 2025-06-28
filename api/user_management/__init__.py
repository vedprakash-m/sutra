"""
User Management API for Admin Users
Provides endpoints for managing user roles and approvals
"""

import azure.functions as func
import json
import logging
import os
import sys
from datetime import datetime

# Add the root directory to Python path for proper imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# NEW: Use unified authentication and validation systems
from shared.unified_auth import auth_required
from shared.utils.fieldConverter import convert_snake_to_camel, convert_camel_to_snake
from shared.utils.schemaValidator import validate_entity
from shared.real_time_cost import get_cost_manager
from shared.database import get_database_manager
from shared.models import User

# Initialize logging
logger = logging.getLogger(__name__)


@auth_required(admin_only=True)
async def main(req: func.HttpRequest, user: User) -> func.HttpResponse:
    """
    User Management API Endpoint

    GET /api/admin/users - List all users
    POST /api/admin/users/{user_id}/approve - Approve a pending user
    POST /api/admin/users/{user_id}/role - Change user role
    DELETE /api/admin/users/{user_id} - Remove user access
    """
    try:
        method = req.method
        route_params = req.route_params
        user_id_param = route_params.get('user_id') if route_params else None

        if method == "GET":
            return await list_users(req)
        elif method == "POST" and user_id_param:
            if req.url.endswith('/approve'):
                return await approve_user(req, user_id_param)
            elif req.url.endswith('/role'):
                return await change_user_role(req, user_id_param)
        elif method == "DELETE" and user_id_param:
            return await remove_user(req, user_id_param)
        else:
            return func.HttpResponse(
                json.dumps({"error": "Invalid endpoint or method"}),
                status_code=400,
                mimetype="application/json"
            )

    except Exception as e:
        logger.error(f"Error in user management API: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )


async def list_users(req: func.HttpRequest) -> func.HttpResponse:
    """List all users with their roles and approval status"""
    try:
        db_manager = get_database_manager()
        container = db_manager.get_container("Users")

        # Query all users
        query = "SELECT * FROM c WHERE c.type = 'user' ORDER BY c.createdAt DESC"
        users = list(container.query_items(query=query, enable_cross_partition_query=True))

        # Format user data for admin display
        user_data = []
        for user in users:
            user_data.append({
                "id": user["id"],
                "name": user.get("name", "Unknown"),
                "email": user.get("email", ""),
                "role": user.get("role", "user"),
                "approvalStatus": user.get("approvalStatus", "approved"),
                "identityProvider": user.get("identityProvider", ""),
                "createdAt": user.get("createdAt", ""),
                "lastLoginAt": user.get("lastLoginAt", "")
            })

        # Get summary statistics
        total_users = len(user_data)
        pending_users = len([u for u in user_data if u["approvalStatus"] == "pending"])
        admin_users = len([u for u in user_data if u["role"] == "admin"])

        response_data = {
            "users": user_data,
            "summary": {
                "total": total_users,
                "pending": pending_users,
                "admins": admin_users,
                "active": total_users - pending_users
            }
        }

        return func.HttpResponse(
            json.dumps(response_data),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to list users"}),
            status_code=500,
            mimetype="application/json"
        )


async def approve_user(req: func.HttpRequest, user_id: str) -> func.HttpResponse:
    """Approve a pending user and assign them user role"""
    try:
        db_manager = get_database_manager()
        container = db_manager.get_container("Users")

        # Get user document
        user_doc = container.read_item(item=user_id, partition_key=user_id)

        if user_doc.get("role") != "pending_approval":
            return func.HttpResponse(
                json.dumps({"error": "User is not pending approval"}),
                status_code=400,
                mimetype="application/json"
            )

        # Update user to approved status
        user_doc["role"] = "user"
        user_doc["approvalStatus"] = "approved"
        user_doc["updatedAt"] = datetime.now().isoformat()

        container.upsert_item(user_doc)

        logger.info(f"Approved user: {user_id}")

        return func.HttpResponse(
            json.dumps({"message": f"User {user_id} approved successfully"}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Error approving user {user_id}: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to approve user"}),
            status_code=500,
            mimetype="application/json"
        )


async def change_user_role(req: func.HttpRequest, user_id: str) -> func.HttpResponse:
    """Change a user's role (user, admin)"""
    try:
        request_data = json.loads(req.get_body().decode('utf-8'))
        new_role = request_data.get("role")

        if new_role not in ["user", "admin"]:
            return func.HttpResponse(
                json.dumps({"error": "Invalid role. Must be 'user' or 'admin'"}),
                status_code=400,
                mimetype="application/json"
            )

        db_manager = get_database_manager()
        container = db_manager.get_container("Users")

        # Get user document
        user_doc = container.read_item(item=user_id, partition_key=user_id)

        # Update user role
        user_doc["role"] = new_role
        user_doc["updatedAt"] = datetime.now().isoformat()

        container.upsert_item(user_doc)

        logger.info(f"Changed user {user_id} role to: {new_role}")

        return func.HttpResponse(
            json.dumps({"message": f"User role changed to {new_role}"}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Error changing user role for {user_id}: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to change user role"}),
            status_code=500,
            mimetype="application/json"
        )


async def remove_user(req: func.HttpRequest, user_id: str) -> func.HttpResponse:
    """Remove a user's access (delete user document)"""
    try:
        db_manager = get_database_manager()
        container = db_manager.get_container("Users")

        # Delete user document
        container.delete_item(item=user_id, partition_key=user_id)

        logger.info(f"Removed user: {user_id}")

        return func.HttpResponse(
            json.dumps({"message": f"User {user_id} removed successfully"}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Error removing user {user_id}: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to remove user"}),
            status_code=500,
            mimetype="application/json"
        )
