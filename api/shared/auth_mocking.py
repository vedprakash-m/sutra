"""
Comprehensive Authentication Mocking Utilities for Sutra Tests

This module provides standardized authentication mocking patterns to ensure
consistent behavior across all test files and improve CI/CD reliability.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest

from .models import User, UserRole


class MockAuthManager:
    """Mock AuthManager for testing purposes."""

    def __init__(
        self,
        user_id: str = "test-user-123",
        email: str = "test@sutra.ai",
        name: str = "Test User",
        role: UserRole = None,
    ):
        """Initialize mock auth manager with default test user."""
        self.user_id = user_id
        self.email = email
        self.name = name
        self.role = role or UserRole.USER
        self._auth_config = {
            "tenant_id": "test-tenant",
            "client_id": "test-client",
            "policy": "test-policy",
            "issuer": "https://test-issuer.com",
            "jwks_uri": "https://test-jwks.com",
        }

    async def get_auth_config(self) -> Dict[str, Any]:
        """Return mock auth configuration."""
        return self._auth_config

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Mock token validation."""
        if token == "invalid-token":
            from .auth import AuthenticationError

            raise AuthenticationError("Invalid token")

        return {
            "sub": self.user_id,
            "email": self.email,
            "name": self.name,
            "roles": [self.role.value],
            "iat": datetime.now(timezone.utc).timestamp(),
            "exp": (datetime.now(timezone.utc).timestamp() + 3600),
        }

    async def get_user_from_token(self, token: str) -> User:
        """Return mock user from token."""
        return User(
            id=self.user_id,
            email=self.email,
            name=self.name,
            role=self.role,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    async def check_permission(self, user: User, resource: str, action: str) -> bool:
        """Mock permission check."""
        # Admin users have all permissions
        if user.role == UserRole.ADMIN:
            return True

        # Regular users have basic permissions
        return action in ["read", "create", "update", "delete"]


class AuthMockingHelper:
    """Helper class for creating consistent authentication mocks."""

    @staticmethod
    def create_mock_request(
        user_id: str = "test-user-123",
        token: str = "test-token",
        headers: Optional[Dict[str, str]] = None,
    ) -> Mock:
        """Create a mock HTTP request with authentication headers."""
        mock_req = Mock()
        mock_req.headers = headers or {"Authorization": f"Bearer {token}"}
        mock_req.get_json.return_value = {"user_id": user_id}
        return mock_req

    @staticmethod
    def create_admin_user() -> User:
        """Create a mock admin user."""
        return User(
            id="admin-user-123",
            email="admin@sutra.ai",
            name="Admin User",
            role=UserRole.ADMIN,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def create_regular_user(user_id: str = "user-123") -> User:
        """Create a mock regular user."""
        return User(
            id=user_id,
            email=f"user{user_id}@sutra.ai",
            name=f"User {user_id}",
            role=UserRole.USER,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def mock_jwt_verification(return_value: Dict[str, Any] = None, side_effect=None):
        """Create a mock for JWT verification functions."""
        if return_value is None:
            return_value = {
                "valid": True,
                "sub": "test-user-123",
                "email": "test@sutra.ai",
                "roles": ["user"],
            }

        return Mock(return_value=return_value, side_effect=side_effect)


# Pytest fixtures for common authentication scenarios
@pytest.fixture
def mock_auth_manager():
    """Fixture providing a mock AuthManager instance."""
    return MockAuthManager()


@pytest.fixture
def mock_admin_auth_manager():
    """Fixture providing a mock AuthManager for admin user."""
    return MockAuthManager(
        user_id="admin-user-123",
        email="admin@sutra.ai",
        name="Admin User",
        roles=[UserRole.USER, UserRole.ADMIN],
    )


@pytest.fixture
def mock_auth_success():
    """Fixture for successful authentication mocking."""
    mock_auth_manager = MockAuthManager()

    with patch("api.shared.auth.get_auth_manager") as mock_get_auth, patch(
        "api.shared.auth.extract_token_from_request"
    ) as mock_extract_token, patch("api.shared.auth.verify_jwt_token") as mock_verify_jwt, patch(
        "api.shared.auth.get_user_id_from_token"
    ) as mock_get_user_id:
        # Configure mocks
        mock_get_auth.return_value = mock_auth_manager
        mock_extract_token.return_value = "test-token"
        mock_verify_jwt.return_value = {
            "valid": True,
            "sub": "test-user-123",
            "email": "test@sutra.ai",
        }
        mock_get_user_id.return_value = "test-user-123"

        yield {
            "auth_manager": mock_auth_manager,
            "extract_token": mock_extract_token,
            "verify_jwt": mock_verify_jwt,
            "get_user_id": mock_get_user_id,
        }


@pytest.fixture
def mock_admin_auth_success():
    """Fixture for successful admin authentication mocking."""
    mock_auth_manager = MockAuthManager(
        user_id="admin-user-123",
        email="admin@sutra.ai",
        name="Admin User",
        roles=[UserRole.USER, UserRole.ADMIN],
    )

    with patch("api.shared.auth.get_auth_manager") as mock_get_auth, patch(
        "api.shared.auth.extract_token_from_request"
    ) as mock_extract_token, patch("api.shared.auth.verify_jwt_token") as mock_verify_jwt, patch(
        "api.shared.auth.get_user_id_from_token"
    ) as mock_get_user_id, patch(
        "api.shared.auth.check_admin_role"
    ) as mock_check_admin:
        # Configure mocks
        mock_get_auth.return_value = mock_auth_manager
        mock_extract_token.return_value = "admin-token"
        mock_verify_jwt.return_value = {
            "valid": True,
            "sub": "admin-user-123",
            "email": "admin@sutra.ai",
            "roles": ["user", "admin"],
        }
        mock_get_user_id.return_value = "admin-user-123"
        mock_check_admin.return_value = True

        yield {
            "auth_manager": mock_auth_manager,
            "extract_token": mock_extract_token,
            "verify_jwt": mock_verify_jwt,
            "get_user_id": mock_get_user_id,
            "check_admin": mock_check_admin,
        }


@pytest.fixture
def mock_auth_failure():
    """Fixture for authentication failure mocking."""
    with patch("api.shared.auth.extract_token_from_request") as mock_extract_token, patch(
        "api.shared.auth.verify_jwt_token"
    ) as mock_verify_jwt:
        mock_extract_token.return_value = None
        mock_verify_jwt.side_effect = Exception("Authentication failed")

        yield {"extract_token": mock_extract_token, "verify_jwt": mock_verify_jwt}


class StandardAuthMocks:
    """Standard authentication mocking patterns for different scenarios."""

    @staticmethod
    def patch_auth_success(module_name: str, user_id: str = "test-user-123"):
        """Standard successful authentication patching for a specific module."""
        return [
            patch(
                f"{module_name}.verify_jwt_token",
                return_value={"valid": True, "sub": user_id, "email": "test@sutra.ai"},
            ),
            patch(f"{module_name}.get_user_id_from_token", return_value=user_id),
        ]

    @staticmethod
    def patch_admin_auth_success(module_name: str, user_id: str = "admin-user-123"):
        """Standard admin authentication patching for a specific module."""
        return [
            patch(
                f"{module_name}.verify_jwt_token",
                return_value={
                    "valid": True,
                    "sub": user_id,
                    "email": "admin@sutra.ai",
                    "roles": ["user", "admin"],
                },
            ),
            patch(f"{module_name}.get_user_id_from_token", return_value=user_id),
            patch(f"{module_name}.check_admin_role", return_value=True),
        ]

    @staticmethod
    def patch_auth_failure(module_name: str):
        """Standard authentication failure patching for a specific module."""
        return [
            patch(
                f"{module_name}.verify_jwt_token",
                return_value={"valid": False, "message": "Authentication failed"},
            ),
            patch(f"{module_name}.get_user_id_from_token", return_value=None),
        ]


# Decorator for easy auth mocking in test classes
def with_auth_mocking(auth_type: str = "success", user_type: str = "regular"):
    """
    Decorator to apply standard authentication mocking to test methods.

    Args:
        auth_type: "success", "failure", or "admin"
        user_type: "regular" or "admin"
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            if auth_type == "success":
                if user_type == "admin":
                    with patch("api.shared.auth.get_auth_manager") as mock_auth:
                        mock_auth.return_value = MockAuthManager(
                            user_id="admin-user-123",
                            roles=[UserRole.USER, UserRole.ADMIN],
                        )
                        return func(*args, **kwargs)
                else:
                    with patch("api.shared.auth.get_auth_manager") as mock_auth:
                        mock_auth.return_value = MockAuthManager()
                        return func(*args, **kwargs)
            elif auth_type == "failure":
                with patch("api.shared.auth.verify_jwt_token") as mock_verify:
                    mock_verify.side_effect = Exception("Auth failed")
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Context managers for authentication mocking
class MockAuthContext:
    """Context manager for authentication mocking."""

    def __init__(self, user_type: str = "regular", auth_success: bool = True):
        self.user_type = user_type
        self.auth_success = auth_success
        self.patches = []

    def __enter__(self):
        if self.auth_success:
            if self.user_type == "admin":
                auth_manager = MockAuthManager(
                    user_id="admin-user-123",
                    email="admin@sutra.ai",
                    roles=[UserRole.USER, UserRole.ADMIN],
                )
            else:
                auth_manager = MockAuthManager()

            # Patch common auth functions
            self.patches = [
                patch("api.shared.auth.get_auth_manager", return_value=auth_manager),
                patch(
                    "api.shared.auth.extract_token_from_request",
                    return_value="test-token",
                ),
                patch("api.shared.auth.verify_jwt_token", return_value={"valid": True}),
            ]
        else:
            # Mock authentication failure
            self.patches = [
                patch("api.shared.auth.extract_token_from_request", return_value=None),
                patch(
                    "api.shared.auth.verify_jwt_token",
                    side_effect=Exception("Auth failed"),
                ),
            ]

        for p in self.patches:
            p.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for p in self.patches:
            p.stop()


# Example usage functions for documentation
def example_usage():
    """
    Example usage of authentication mocking utilities:

    # Using fixtures in test functions
    async def test_with_fixture(mock_auth_success):
        # Authentication is already mocked
        pass

    # Using context manager
    def test_with_context():
        with MockAuthContext(user_type="admin"):
            # Test admin functionality
            pass

    # Using decorator
    @with_auth_mocking(auth_type="success", user_type="admin")
    def test_with_decorator():
        # Test with admin auth
        pass

    # Manual mocking for specific cases
    def test_manual_mocking():
        with patch("api.shared.auth.verify_jwt_token") as mock_verify:
            mock_verify.return_value = {"valid": True, "sub": "custom-user"}
            # Custom test logic
            pass
    """
    pass


# Export commonly used utilities
__all__ = [
    "MockAuthManager",
    "AuthMockingHelper",
    "StandardAuthMocks",
    "MockAuthContext",
    "with_auth_mocking",
    "mock_auth_success",
    "mock_admin_auth_success",
    "mock_auth_failure",
]
