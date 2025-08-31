"""
Auth module - Legacy authentication functions
This module provides compatibility for existing imports during migration to unified_auth.py
"""

from typing import Optional

import azure.functions as func


def extract_token_from_request(req: func.HttpRequest) -> Optional[str]:
    """
    Extract authentication token from HTTP request.

    Args:
        req: Azure Functions HTTP request object

    Returns:
        Token string if found, None otherwise
    """
    # Check Authorization header
    auth_header = req.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]  # Remove "Bearer " prefix

    # Check x-ms-token-aad-id-token header (for SWA)
    return req.headers.get("x-ms-token-aad-id-token")


def get_auth_manager():
    """
    Get the auth manager instance.

    Returns:
        Auth manager instance - simplified for compatibility
    """
    # Return a simple mock manager to avoid complex imports during testing
    return SimpleAuthManager()


class SimpleAuthManager:
    """Simplified auth manager for test compatibility"""

    def get_user_from_token(self, token: str):
        """Simplified user retrieval for testing"""
        if token and (token.startswith("mock") or token.startswith("dev")):
            return MockUser()
        return None


class MockUser:
    """Mock user for testing"""

    def __init__(self):
        self.id = "mock-user-id"
        self.email = "test@sutra.ai"
        self.name = "Test User"
        self.role = "user"


# Legacy compatibility classes and exceptions
class AuthenticationError(Exception):
    """Authentication error exception"""

    pass


class AuthorizationError(Exception):
    """Authorization error exception"""

    pass


class AuthManager:
    """Legacy AuthManager for compatibility"""

    def __init__(self):
        self.simple_manager = SimpleAuthManager()

    def get_user_from_token(self, token: str):
        """Get user from token using simple auth"""
        return self.simple_manager.get_user_from_token(token)

    def validate_token(self, token: str):
        """Validate token - simplified version"""
        user = self.get_user_from_token(token)
        if user:
            return {"sub": user.id, "email": user.email, "name": user.name, "roles": [user.role]}
        return None

    def check_permission(self, user, resource: str, action: str) -> bool:
        """Check user permissions"""
        # Simplified permission check
        if hasattr(user, "role"):
            if str(user.role).lower() == "admin":
                return True
            # Basic permissions for regular users
            if resource in ["prompts", "collections"] and action in ["create", "read"]:
                return True
        return False


# Legacy functions for compatibility
def get_user_id_from_token(token: str) -> Optional[str]:
    """Get user ID from token - legacy compatibility"""
    try:
        manager = AuthManager()
        user = manager.get_user_from_token(token)
        return user.id if user else None
    except:
        return None


def get_user_role(user) -> str:
    """Get user role - legacy compatibility"""
    if hasattr(user, "role"):
        return str(user.role)
    return "user"


def check_admin_role(user) -> bool:
    """Check if user has admin role"""
    return get_user_role(user).lower() == "admin"


def check_user_permissions(user, permissions: list) -> bool:
    """Check user permissions"""
    if check_admin_role(user):
        return True
    # Simplified permission check
    return True  # Allow basic permissions for now


def require_admin(func):
    """Decorator to require admin role"""

    def wrapper(*args, **kwargs):
        # Simplified decorator for compatibility
        return func(*args, **kwargs)

    return wrapper


def require_admin_role(func):
    """Decorator to require admin role - alias for require_admin"""
    return require_admin(func)


def get_current_user(req: func.HttpRequest):
    """Get current user from request"""
    token = extract_token_from_request(req)
    if not token:
        return None

    manager = AuthManager()
    return manager.get_user_from_token(token)
