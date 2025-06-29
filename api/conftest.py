"""
Centralized pytest configuration and fixtures for Sutra API tests.

This file provides common fixtures and test utilities used across all test modules,
particularly standardized authentication mocking patterns for Azure Static Web Apps.
"""

import pytest
import sys
import os
import base64
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

# Add the current directory to the path for imports
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from shared.models import User, UserRole


# Ensure testing mode is enabled for all tests
@pytest.fixture(autouse=True)
def enable_testing_mode():
    """Automatically enable testing mode for all tests."""
    with patch.dict(os.environ, {"TESTING_MODE": "true"}):
        yield


# Global Authentication Fixtures
@pytest.fixture
def mock_static_web_apps_auth():
    """Global fixture for Azure Static Web Apps authentication mocking."""

    def create_mock_request_with_auth(
        user_id="test-user-123",
        role="admin",
        identity_provider="azureActiveDirectory",
        user_name="Test User",
        claims=None,
        method="GET",
        body=None,
    ):
        """Create a mock request with proper Azure Static Web Apps headers."""

        # Create user principal data
        principal_data = {
            "identityProvider": identity_provider,
            "userId": user_id,
            "userDetails": user_name,
            "userRoles": [role] if isinstance(role, str) else role,
            "claims": claims or [],
        }

        # Encode as base64
        principal_b64 = base64.b64encode(
            json.dumps(principal_data).encode("utf-8")
        ).decode("utf-8")

        # Create mock request with headers
        mock_request = Mock()
        mock_request.headers = {
            "x-ms-client-principal": principal_b64,
            "x-ms-client-principal-id": user_id,
            "x-ms-client-principal-name": user_name,
            "x-ms-client-principal-idp": identity_provider,
        }
        mock_request.get_json.return_value = body or {}
        mock_request.method = method
        mock_request.get_body.return_value = (
            json.dumps(body or {}).encode("utf-8") if body else b"{}"
        )

        return mock_request

    return create_mock_request_with_auth


@pytest.fixture
def mock_auth_success(mock_static_web_apps_auth):
    """Global fixture for successful authentication mocking."""
    return mock_static_web_apps_auth(
        user_id="auth-user-123", role="user", user_name="Auth User"
    )


@pytest.fixture
def mock_admin_auth(mock_static_web_apps_auth):
    """Fixture for admin authenticated requests."""
    return mock_static_web_apps_auth(
        user_id="admin-user-123", role="admin", user_name="Test Admin"
    )


@pytest.fixture
def mock_user_auth(mock_static_web_apps_auth):
    """Fixture for regular user authenticated requests."""
    return mock_static_web_apps_auth(
        user_id="test-user-123", role="user", user_name="Test User"
    )


@pytest.fixture
def mock_non_admin_auth(mock_static_web_apps_auth):
    """Fixture for non-admin authenticated requests."""
    return mock_static_web_apps_auth(
        user_id="non-admin-123", role="user", user_name="Non Admin User"
    )


@pytest.fixture
def mock_auth_request(mock_static_web_apps_auth):
    """General purpose authenticated request fixture."""
    return mock_static_web_apps_auth(
        user_id="test-user-123", role="user", user_name="Test User"
    )


@pytest.fixture
def mock_no_auth():
    """Fixture for requests without authentication."""
    mock_request = Mock()
    mock_request.headers = {}
    mock_request.get_json.return_value = {}
    mock_request.method = "GET"
    mock_request.get_body.return_value = b"{}"
    return mock_request


@pytest.fixture
def mock_auth_failure():
    """Fixture for simulating authentication failure."""
    with patch("api.shared.auth_static_web_apps.TESTING_MODE", True):
        yield


# Database Mocking Fixtures
@pytest.fixture
def mock_cosmos_client():
    """Mock Cosmos DB client with proper container structure."""
    mock_client = Mock()

    # Mock containers with proper naming
    containers = {}
    container_names = [
        "Users",
        "Prompts",
        "Collections",
        "Playbooks",
        "Executions",
        "SystemConfig",
        "AuditLog",
        "usage",
        "config",
    ]

    for name in container_names:
        container = Mock()
        container.create_item = Mock(return_value={"id": "test-id", "created": True})
        container.read_item = Mock(return_value={"id": "test-id", "data": "test"})
        container.upsert_item = Mock(return_value={"id": "test-id", "updated": True})
        container.replace_item = Mock(return_value={"id": "test-id", "replaced": True})
        container.delete_item = Mock(return_value=True)
        container.query_items = Mock(return_value=[{"id": "test-id", "data": "test"}])
        container.read_all_items = Mock(
            return_value=[{"id": "test-id", "data": "test"}]
        )
        containers[name] = container

    # Mock database manager methods
    mock_database_manager = Mock()
    mock_database_manager.get_container = Mock(
        side_effect=lambda name: containers.get(name)
    )
    mock_database_manager.create_item = AsyncMock(
        return_value={"id": "test-id", "created": True}
    )
    mock_database_manager.read_item = AsyncMock(
        return_value={"id": "test-id", "data": "test"}
    )
    mock_database_manager.update_item = AsyncMock(
        return_value={"id": "test-id", "updated": True}
    )
    mock_database_manager.delete_item = AsyncMock(return_value=True)
    mock_database_manager.query_items = AsyncMock(
        return_value=[{"id": "test-id", "data": "test"}]
    )
    mock_database_manager.list_items = AsyncMock(
        return_value=[{"id": "test-id", "data": "test"}]
    )

    # Add container-specific access methods for backwards compatibility
    for name in container_names:
        setattr(
            mock_database_manager,
            f"get_{name.lower()}_container",
            Mock(return_value=containers[name]),
        )

    return mock_database_manager


@pytest.fixture
def mock_database_manager(mock_cosmos_client):
    """Fixture that provides a mocked database manager."""
    with patch("shared.database.get_database_manager") as mock_get_db:
        mock_get_db.return_value = mock_cosmos_client
        yield mock_cosmos_client


# Environment setup fixtures
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically setup test environment variables."""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["TESTING_MODE"] = "true"
    yield
    # Cleanup
    if "ENVIRONMENT" in os.environ:
        del os.environ["ENVIRONMENT"]
    if "TESTING_MODE" in os.environ:
        del os.environ["TESTING_MODE"]


# Time-based fixtures
@pytest.fixture
def fixed_datetime():
    """Fixture that provides a fixed datetime for consistent testing."""
    return datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def mock_datetime(fixed_datetime):
    """Mock datetime.now() to return a fixed time."""
    with patch("datetime.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_datetime
        mock_dt.utcnow.return_value = fixed_datetime.replace(tzinfo=None)
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        yield mock_dt


# Standard test data
@pytest.fixture
def sample_user_data():
    """Standard user data for testing."""
    return {
        "id": "test-user-123",
        "name": "Test User",
        "email": "test@example.com",
        "role": "user",
        "identityProvider": "azureActiveDirectory",
        "createdAt": "2023-01-01T12:00:00Z",
        "lastLoginAt": "2023-01-01T12:00:00Z",
        "updatedAt": "2023-01-01T12:00:00Z",
        "type": "user",
    }


@pytest.fixture
def sample_admin_data():
    """Standard admin data for testing."""
    return {
        "id": "admin-user-123",
        "name": "Admin User",
        "email": "admin@example.com",
        "role": "admin",
        "identityProvider": "azureActiveDirectory",
        "createdAt": "2023-01-01T12:00:00Z",
        "lastLoginAt": "2023-01-01T12:00:00Z",
        "updatedAt": "2023-01-01T12:00:00Z",
        "type": "user",
    }


# Unified Authentication Fixtures
@pytest.fixture
def unified_auth_setup():
    """Setup unified authentication for testing."""
    from shared.unified_auth import get_auth_provider

    # Set testing environment
    with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "true"}):
        auth_provider = get_auth_provider()
        yield auth_provider


@pytest.fixture
def mock_test_user():
    """Create a test user for unified auth tests."""
    user = User(
        id="test-user-123",
        email="test@example.com",
        name="Test User",
        role=UserRole.USER,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    # Add permissions attribute for testing using object.__setattr__ to bypass Pydantic validation
    object.__setattr__(
        user,
        "permissions",
        [
            "*",  # Wildcard permission for testing
            "cost.read",
            "cost.manage",  # Cost management permissions
            "collections.read",
            "collections.create",
            "collections.update",
            "collections.delete",  # Collections permissions
        ],
    )
    return user


@pytest.fixture
def mock_admin_user():
    """Create an admin user for unified auth tests."""
    user = User(
        id="admin-user-123",
        email="admin@example.com",
        name="Admin User",
        role=UserRole.ADMIN,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    # Add permissions attribute for testing using object.__setattr__ to bypass Pydantic validation
    object.__setattr__(
        user,
        "permissions",
        [
            "*",  # Wildcard permission for testing
            "cost.read",
            "cost.manage",  # Cost management permissions
            "collections.read",
            "collections.create",
            "collections.update",
            "collections.delete",  # Collections permissions
        ],
    )
    return user


@pytest.fixture
def auth_test_user(unified_auth_setup, mock_test_user):
    """Setup test user in unified auth system."""
    auth_provider = unified_auth_setup
    auth_provider.provider.set_test_user(mock_test_user)
    yield mock_test_user
    # Cleanup
    auth_provider.provider.set_test_user(None)


@pytest.fixture
def auth_admin_user(unified_auth_setup, mock_admin_user):
    """Setup admin user in unified auth system."""
    auth_provider = unified_auth_setup
    auth_provider.provider.set_test_user(mock_admin_user)
    yield mock_admin_user
    # Cleanup
    auth_provider.provider.set_test_user(None)


@pytest.fixture
def auth_no_user(unified_auth_setup):
    """Setup no authenticated user."""
    auth_provider = unified_auth_setup
    auth_provider.provider.set_test_user(None)
    yield None


# Helper function for creating requests in the new system
def create_auth_request(
    method="GET",
    body=None,
    headers=None,
    url="http://localhost/api/test",
    user_id=None,
    role="user",
):
    """Create a request for use with unified auth system.

    DEPRECATED: Use the proper unified auth fixtures instead.
    This function is kept for backward compatibility during migration.
    """
    import azure.functions as func
    import os

    if headers is None:
        headers = {}

    # Ensure we're in testing environment for unified auth
    os.environ["PYTEST_CURRENT_TEST"] = "true"

    return func.HttpRequest(
        method=method,
        url=url,
        body=json.dumps(body).encode("utf-8") if body else b"",
        headers=headers,
        route_params={},
        params={},
    )


# Helper functions for tests
def create_mock_request(
    method="GET", body=None, headers=None, user_id=None, role="user"
):
    """Helper to create mock requests with authentication."""
    if headers is None:
        headers = {}

    if user_id:
        # Add Azure Static Web Apps auth headers
        principal_data = {
            "identityProvider": "azureActiveDirectory",
            "userId": user_id,
            "userDetails": "Test User",
            "userRoles": [role],
            "claims": [],
        }
        principal_b64 = base64.b64encode(
            json.dumps(principal_data).encode("utf-8")
        ).decode("utf-8")
        headers.update(
            {
                "x-ms-client-principal": principal_b64,
                "x-ms-client-principal-id": user_id,
                "x-ms-client-principal-name": "Test User",
                "x-ms-client-principal-idp": "azureActiveDirectory",
            }
        )

    mock_request = Mock()
    mock_request.method = method
    mock_request.headers = headers
    mock_request.get_json.return_value = body or {}
    mock_request.get_body.return_value = (
        json.dumps(body or {}).encode("utf-8") if body else b"{}"
    )

    return mock_request


@pytest.fixture
def mock_get_user():
    """Mock get_user function for tests that still reference it."""

    def _mock_get_user(
        user_id=None, role="user", email="test@example.com", name="Test User"
    ):
        return User(
            id=user_id or "test-user-123",
            email=email,
            name=name,
            role=UserRole.ADMIN if role == "admin" else UserRole.USER,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    return _mock_get_user
