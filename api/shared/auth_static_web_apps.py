"""
Azure Static Web Apps Authentication Module
Correctly handles authentication for Azure Static Web Apps with Entra External ID
"""

import os
import logging
import base64
import json
from typing import Optional, Dict, Any
from functools import wraps
import azure.functions as func
from .models import User, UserRole


class AuthenticationError(Exception):
    """Authentication related errors."""
    pass


class AuthorizationError(Exception):
    """Authorization related errors."""
    pass


class StaticWebAppsAuthManager:
    """
    Handles authentication for Azure Static Web Apps.

    Azure Static Web Apps automatically handles authentication and passes
    user information via headers to Azure Functions.
    """

    def get_user_from_headers(self, req: func.HttpRequest) -> Optional[User]:
        """
        Extract user information from Azure Static Web Apps headers.

        Azure Static Web Apps passes user info via these headers:
        - x-ms-client-principal: Base64 encoded JSON with user details
        - x-ms-client-principal-id: User ID
        - x-ms-client-principal-name: User display name
        - x-ms-client-principal-idp: Identity provider
        """
        try:
            # Method 1: Try to get user from x-ms-client-principal header
            principal_header = req.headers.get("x-ms-client-principal")
            if principal_header:
                try:
                    # Decode base64 JSON
                    principal_data = base64.b64decode(principal_header).decode('utf-8')
                    principal = json.loads(principal_data)

                    user_id = principal.get("userId") or principal.get("sub")
                    user_name = principal.get("userDetails") or principal.get("name")
                    identity_provider = principal.get("identityProvider", "azureActiveDirectory")
                    user_roles = principal.get("userRoles", ["user"])

                    # Determine primary role (Azure Static Web Apps can have multiple roles)
                    role = UserRole.ADMIN if "admin" in user_roles else UserRole.USER

                    return User(
                        id=user_id,
                        email=user_name,  # In Entra External ID, userDetails is often email
                        name=user_name,
                        role=role,
                        identity_provider=identity_provider
                    )

                except (ValueError, json.JSONDecodeError) as e:
                    logging.warning(f"Failed to decode x-ms-client-principal: {e}")

            # Method 2: Try individual headers (fallback)
            user_id = req.headers.get("x-ms-client-principal-id")
            user_name = req.headers.get("x-ms-client-principal-name")
            identity_provider = req.headers.get("x-ms-client-principal-idp", "azureActiveDirectory")

            if user_id:
                # Default to user role, could be enhanced with database lookup
                role = UserRole.USER

                return User(
                    id=user_id,
                    email=user_name or f"{user_id}@unknown.com",
                    name=user_name or "Unknown User",
                    role=role,
                    identity_provider=identity_provider
                )

            return None

        except Exception as e:
            logging.error(f"Error extracting user from headers: {e}")
            return None

    def check_permission(self, user: User, resource: str, action: str) -> bool:
        """Check if user has permission for the specified action on resource."""
        # Admin users have all permissions
        if user.role == UserRole.ADMIN:
            return True

        # Define permission rules
        permissions = {
            "prompts": {
                "create": [UserRole.USER, UserRole.ADMIN],
                "read": [UserRole.USER, UserRole.ADMIN],
                "update": [UserRole.USER, UserRole.ADMIN],
                "delete": [UserRole.USER, UserRole.ADMIN],
            },
            "collections": {
                "create": [UserRole.USER, UserRole.ADMIN],
                "read": [UserRole.USER, UserRole.ADMIN],
                "update": [UserRole.USER, UserRole.ADMIN],
                "delete": [UserRole.USER, UserRole.ADMIN],
            },
            "playbooks": {
                "create": [UserRole.USER, UserRole.ADMIN],
                "read": [UserRole.USER, UserRole.ADMIN],
                "update": [UserRole.USER, UserRole.ADMIN],
                "delete": [UserRole.USER, UserRole.ADMIN],
                "execute": [UserRole.USER, UserRole.ADMIN],
            },
            "admin": {
                "read": [UserRole.ADMIN],
                "update": [UserRole.ADMIN],
                "delete": [UserRole.ADMIN],
                "manage_users": [UserRole.ADMIN],
                "manage_providers": [UserRole.ADMIN],
                "view_usage": [UserRole.ADMIN],
            },
        }

        resource_permissions = permissions.get(resource, {})
        allowed_roles = resource_permissions.get(action, [])

        return user.role in allowed_roles


# Global auth manager instance
_auth_manager = None


def get_auth_manager() -> StaticWebAppsAuthManager:
    """Get the global AuthManager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = StaticWebAppsAuthManager()
    return _auth_manager


def require_auth(resource: str = None, action: str = "read"):
    """
    Decorator to require authentication for Azure Function endpoints.

    Works with Azure Static Web Apps authentication by reading user info
    from headers instead of validating JWT tokens.
    """
    def decorator(func_to_decorate):
        @wraps(func_to_decorate)
        async def wrapper(req: func.HttpRequest) -> func.HttpResponse:
            try:
                # Skip authentication in testing mode
                if TESTING_MODE:
                    # Create a mock user for testing
                    req.current_user = create_mock_user("test-user-123", "user")
                    return await func_to_decorate(req)

                # Get user from Azure Static Web Apps headers
                auth_mgr = get_auth_manager()
                user = auth_mgr.get_user_from_headers(req)

                if not user:
                    return func.HttpResponse(
                        json.dumps({
                            "error": "authentication_required",
                            "message": "User not authenticated via Azure Static Web Apps"
                        }),
                        status_code=401,
                        headers={"Content-Type": "application/json"},
                    )

                # Check permissions if resource and action specified
                if resource and action:
                    if not auth_mgr.check_permission(user, resource, action):
                        return func.HttpResponse(
                            json.dumps({
                                "error": "access_denied",
                                "message": "Insufficient permissions"
                            }),
                            status_code=403,
                            headers={"Content-Type": "application/json"},
                        )

                # Add user to request context
                req.current_user = user

                # Call the original function
                return await func_to_decorate(req)

            except AuthenticationError as e:
                return func.HttpResponse(
                    json.dumps({
                        "error": "authentication_failed",
                        "message": str(e)
                    }),
                    status_code=401,
                    headers={"Content-Type": "application/json"},
                )
            except AuthorizationError as e:
                return func.HttpResponse(
                    json.dumps({
                        "error": "authorization_failed",
                        "message": str(e)
                    }),
                    status_code=403,
                    headers={"Content-Type": "application/json"},
                )
            except Exception as e:
                logging.error(f"Authentication error: {e}")
                return func.HttpResponse(
                    json.dumps({
                        "error": "internal_error",
                        "message": "Authentication system error"
                    }),
                    status_code=500,
                    headers={"Content-Type": "application/json"},
                )

        return wrapper
    return decorator


def require_admin(func_to_decorate):
    """Decorator to require admin role for Azure Function endpoints."""
    return require_auth(resource="admin", action="read")(func_to_decorate)


async def get_current_user(req: func.HttpRequest) -> Optional[User]:
    """Get current user from request (if authenticated)."""
    return getattr(req, "current_user", None)


def check_admin_role(req: func.HttpRequest) -> bool:
    """Check if the authenticated user has admin role."""
    try:
        auth_mgr = get_auth_manager()
        user = auth_mgr.get_user_from_headers(req)
        return user and user.role == UserRole.ADMIN
    except Exception:
        return False


# Legacy compatibility functions (for gradual migration)
def verify_jwt_token(req: func.HttpRequest) -> Dict[str, Any]:
    """
    Legacy compatibility function.
    In Azure Static Web Apps, we don't validate JWT tokens.
    """
    try:
        auth_mgr = get_auth_manager()
        user = auth_mgr.get_user_from_headers(req)

        if user:
            return {
                "valid": True,
                "message": "User authenticated via Azure Static Web Apps",
                "claims": {
                    "sub": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role.value,
                }
            }
        else:
            return {
                "valid": False,
                "message": "No authenticated user found in headers"
            }
    except Exception as e:
        logging.error(f"Error in verify_jwt_token compatibility function: {e}")
        return {
            "valid": False,
            "message": "Authentication verification failed"
        }


def get_user_id_from_token(req: func.HttpRequest) -> Optional[str]:
    """
    Legacy compatibility function.
    In Azure Static Web Apps, we get user ID from headers.
    """
    try:
        auth_mgr = get_auth_manager()
        user = auth_mgr.get_user_from_headers(req)
        return user.id if user else None
    except Exception:
        return None


# Testing support - environment variable to disable decorators during testing
TESTING_MODE = os.getenv("TESTING_MODE", "false").lower() == "true"

def create_mock_user(user_id: str = "test-user-123", role: str = "user"):
    """Create a mock user object for testing."""
    class MockUser:
        def __init__(self, user_id: str, role: str):
            self.id = user_id
            self.role = role
            self.email = f"{user_id}@test.com"

    return MockUser(user_id, role)
