"""
Authentication helper functions for extracting user information from HTTP requests.
This module provides utilities for authentication and user info extraction.
"""

import logging
from typing import Dict, Optional

import azure.functions as func
from shared.auth import extract_token_from_request, get_auth_manager


def extract_user_info(req: func.HttpRequest) -> Optional[Dict[str, str]]:
    """
    Extract user information from HTTP request.

    Args:
        req: Azure Functions HTTP request object

    Returns:
        Dictionary containing user information if authenticated, None otherwise
    """
    try:
        # Extract token from request
        token = extract_token_from_request(req)
        if not token:
            logging.warning("No authentication token found in request")
            return None

        # Get auth manager and validate token
        auth_manager = get_auth_manager()
        user = auth_manager.get_user_from_token(token)

        if not user:
            logging.warning("Failed to get user from token")
            return None

        # Return user information as dictionary
        return {
            "id": user.id,
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "given_name": getattr(user, "given_name", ""),
            "family_name": getattr(user, "family_name", ""),
            "organization_id": getattr(user, "organization_id", None),
        }

    except Exception as e:
        logging.error(f"Error extracting user info: {e}")
        return None


def get_user_id(req: func.HttpRequest) -> Optional[str]:
    """
    Extract user ID from HTTP request.

    Args:
        req: Azure Functions HTTP request object

    Returns:
        User ID if authenticated, None otherwise
    """
    user_info = extract_user_info(req)
    return user_info.get("id") if user_info else None


def get_user_email(req: func.HttpRequest) -> Optional[str]:
    """
    Extract user email from HTTP request.

    Args:
        req: Azure Functions HTTP request object

    Returns:
        User email if authenticated, None otherwise
    """
    user_info = extract_user_info(req)
    return user_info.get("email") if user_info else None


def is_authenticated(req: func.HttpRequest) -> bool:
    """
    Check if request is from an authenticated user.

    Args:
        req: Azure Functions HTTP request object

    Returns:
        True if authenticated, False otherwise
    """
    return extract_user_info(req) is not None


def is_admin(req: func.HttpRequest) -> bool:
    """
    Check if request is from an admin user.

    Args:
        req: Azure Functions HTTP request object

    Returns:
        True if user is admin, False otherwise
    """
    user_info = extract_user_info(req)
    if not user_info:
        return False

    return user_info.get("role", "").lower() == "admin"
