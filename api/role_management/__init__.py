"""
Advanced Role Management System for Sutra
Provides comprehensive role-based access control with Static Web Apps integration
"""

import json
import logging
import os
import sys
import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import azure.functions as func

# Add the root directory to Python path for proper imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from shared.database import get_database_manager
from shared.models import UserRole

# Initialize logging
logger = logging.getLogger(__name__)


class RolePermission(Enum):
    """Define granular permissions for role-based access control"""

    # User management
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"

    # Prompt management
    PROMPT_READ = "prompt:read"
    PROMPT_WRITE = "prompt:write"
    PROMPT_DELETE = "prompt:delete"
    PROMPT_SHARE = "prompt:share"

    # Collection management
    COLLECTION_READ = "collection:read"
    COLLECTION_WRITE = "collection:write"
    COLLECTION_DELETE = "collection:delete"
    COLLECTION_SHARE = "collection:share"

    # Playbook management
    PLAYBOOK_READ = "playbook:read"
    PLAYBOOK_WRITE = "playbook:write"
    PLAYBOOK_DELETE = "playbook:delete"
    PLAYBOOK_EXECUTE = "playbook:execute"

    # System administration
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"
    ADMIN_INTEGRATIONS = "admin:integrations"
    ADMIN_ANALYTICS = "admin:analytics"


class RoleManager:
    """Advanced role management with permission-based access control"""

    # Role to permissions mapping
    ROLE_PERMISSIONS = {
        UserRole.USER: [
            RolePermission.PROMPT_READ,
            RolePermission.PROMPT_WRITE,
            RolePermission.PROMPT_DELETE,  # Own prompts only
            RolePermission.COLLECTION_READ,
            RolePermission.COLLECTION_WRITE,
            RolePermission.COLLECTION_DELETE,  # Own collections only
            RolePermission.PLAYBOOK_READ,
            RolePermission.PLAYBOOK_WRITE,
            RolePermission.PLAYBOOK_EXECUTE,
        ],
        UserRole.ADMIN: [
            # All user permissions plus admin permissions
            RolePermission.USER_READ,
            RolePermission.USER_WRITE,
            RolePermission.USER_DELETE,
            RolePermission.PROMPT_READ,
            RolePermission.PROMPT_WRITE,
            RolePermission.PROMPT_DELETE,
            RolePermission.PROMPT_SHARE,
            RolePermission.COLLECTION_READ,
            RolePermission.COLLECTION_WRITE,
            RolePermission.COLLECTION_DELETE,
            RolePermission.COLLECTION_SHARE,
            RolePermission.PLAYBOOK_READ,
            RolePermission.PLAYBOOK_WRITE,
            RolePermission.PLAYBOOK_DELETE,
            RolePermission.PLAYBOOK_EXECUTE,
            RolePermission.ADMIN_USERS,
            RolePermission.ADMIN_SYSTEM,
            RolePermission.ADMIN_INTEGRATIONS,
            RolePermission.ADMIN_ANALYTICS,
        ],
    }

    def __init__(self):
        self.db_manager = get_database_manager()
        self.users_container = self.db_manager.get_container("Users")

    def get_user_permissions(self, user_role: UserRole) -> List[RolePermission]:
        """Get all permissions for a given role"""
        return self.ROLE_PERMISSIONS.get(user_role, [])

    def has_permission(self, user_role: UserRole, permission: RolePermission) -> bool:
        """Check if a role has a specific permission"""
        user_permissions = self.get_user_permissions(user_role)
        return permission in user_permissions

    async def assign_role(self, user_id: str, new_role: UserRole, assigned_by: str) -> Dict[str, Any]:
        """Assign a new role to a user"""
        try:
            # Get user document
            user_doc = self.users_container.read_item(item=user_id, partition_key=user_id)

            old_role = user_doc.get("role", "user")

            # Update user role
            user_doc["role"] = new_role.value
            user_doc["roleUpdatedAt"] = datetime.now(timezone.utc).isoformat()
            user_doc["roleUpdatedBy"] = assigned_by

            # Save updated user
            self.users_container.replace_item(item=user_id, body=user_doc)

            # Log role change
            role_change_log = {
                "id": f"role_change_{user_id}_{datetime.now().timestamp()}",
                "type": "role_change",
                "userId": user_id,
                "oldRole": old_role,
                "newRole": new_role.value,
                "assignedBy": assigned_by,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Store in audit log (if exists)
            try:
                audit_container = self.db_manager.get_container("AuditLog")
                audit_container.create_item(role_change_log)
            except Exception as e:
                logger.warning(f"Failed to log role change: {e}")

            return {
                "success": True,
                "message": f"Role updated from {old_role} to {new_role.value}",
                "user_id": user_id,
                "new_role": new_role.value,
            }

        except Exception as e:
            logger.error(f"Failed to assign role: {e}")
            return {"success": False, "message": f"Failed to assign role: {str(e)}"}

    async def get_user_role_info(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive role information for a user"""
        try:
            user_doc = self.users_container.read_item(item=user_id, partition_key=user_id)

            user_role = UserRole(user_doc.get("role", "user"))
            permissions = self.get_user_permissions(user_role)

            return {
                "user_id": user_id,
                "role": user_role.value,
                "permissions": [perm.value for perm in permissions],
                "role_updated_at": user_doc.get("roleUpdatedAt"),
                "role_updated_by": user_doc.get("roleUpdatedBy"),
            }

        except Exception as e:
            logger.error(f"Failed to get user role info: {e}")
            return {
                "user_id": user_id,
                "role": "user",
                "permissions": [perm.value for perm in self.get_user_permissions(UserRole.USER)],
                "error": str(e),
            }

    async def list_users_by_role(self, role: Optional[UserRole] = None) -> List[Dict[str, Any]]:
        """List all users, optionally filtered by role"""
        try:
            query = "SELECT * FROM c WHERE c.type = 'user'"
            if role:
                query += f" AND c.role = '{role.value}'"

            users = list(self.users_container.query_items(query=query, enable_cross_partition_query=True))

            return [
                {
                    "id": user["id"],
                    "name": user.get("name", "Unknown"),
                    "email": user.get("email", ""),
                    "role": user.get("role", "user"),
                    "created_at": user.get("createdAt"),
                    "last_login": user.get("lastLoginAt"),
                    "identity_provider": user.get("identityProvider", "azureActiveDirectory"),
                }
                for user in users
            ]

        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return []


# Global role manager instance
_role_manager = None


def get_role_manager() -> RoleManager:
    """Get the global RoleManager instance"""
    global _role_manager
    if _role_manager is None:
        _role_manager = RoleManager()
    return _role_manager


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Advanced Role Management API

    GET /api/role_management?user_id=<id> - Get user role info
    GET /api/role_management?list_users=true&role=<role> - List users by role
    PUT /api/role_management - Assign role to user
    """

    try:
        # Manual authentication - no decorator - admin only
        from shared.unified_auth import require_authentication

        user = await require_authentication(req)

        # Check if user is admin
        if not user.is_admin:
            return func.HttpResponse(
                json.dumps({"error": "Admin access required"}),
                status_code=403,
                mimetype="application/json",
            )

        role_manager = get_role_manager()
        current_user = user

        if req.method == "GET":
            # Get specific user role info
            user_id = req.params.get("user_id")
            if user_id:
                role_info = await role_manager.get_user_role_info(user_id)
                return func.HttpResponse(json.dumps(role_info), status_code=200, mimetype="application/json")

            # List users by role
            list_users = req.params.get("list_users")
            if list_users:
                role_filter = req.params.get("role")
                role_enum = UserRole(role_filter) if role_filter else None

                users = await role_manager.list_users_by_role(role_enum)
                return func.HttpResponse(
                    json.dumps({"users": users}),
                    status_code=200,
                    mimetype="application/json",
                )

            # Return role permissions info
            permissions_info = {
                "roles": {role.value: [perm.value for perm in perms] for role, perms in RoleManager.ROLE_PERMISSIONS.items()},
                "current_user": {
                    "id": current_user.id,
                    "role": current_user.role.value,
                    "permissions": [perm.value for perm in role_manager.get_user_permissions(current_user.role)],
                },
            }

            return func.HttpResponse(
                json.dumps(permissions_info),
                status_code=200,
                mimetype="application/json",
            )

        elif req.method == "PUT":
            # Assign role to user
            try:
                request_body = req.get_json()
                user_id = request_body.get("user_id")
                new_role = request_body.get("role")

                if not user_id or not new_role:
                    return func.HttpResponse(
                        json.dumps({"error": "user_id and role are required"}),
                        status_code=400,
                        mimetype="application/json",
                    )

                # Validate role
                try:
                    role_enum = UserRole(new_role)
                except ValueError:
                    return func.HttpResponse(
                        json.dumps({"error": f"Invalid role: {new_role}"}),
                        status_code=400,
                        mimetype="application/json",
                    )

                # Assign role
                result = await role_manager.assign_role(user_id=user_id, new_role=role_enum, assigned_by=current_user.id)

                status_code = 200 if result["success"] else 400
                return func.HttpResponse(
                    json.dumps(result),
                    status_code=status_code,
                    mimetype="application/json",
                )

            except Exception as e:
                return func.HttpResponse(
                    json.dumps({"error": f"Invalid request body: {str(e)}"}),
                    status_code=400,
                    mimetype="application/json",
                )

        else:
            return func.HttpResponse(
                json.dumps({"error": "Method not allowed"}),
                status_code=405,
                mimetype="application/json",
            )

    except Exception as e:
        logger.error(f"Role management error: {e}")
        logger.error(traceback.format_exc())

        # Return proper error response
        if "Authentication required" in str(e) or "401" in str(e):
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "authentication_required",
                        "message": "Please log in to access this resource",
                    }
                ),
                status_code=401,
                mimetype="application/json",
            )
        elif "Admin access required" in str(e) or "403" in str(e):
            return func.HttpResponse(
                json.dumps({"error": "forbidden", "message": "Admin access required"}),
                status_code=403,
                mimetype="application/json",
            )
        else:
            return func.HttpResponse(
                json.dumps({"error": "internal_error", "message": "An internal error occurred"}),
                status_code=500,
                mimetype="application/json",
            )
