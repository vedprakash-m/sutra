"""
Centralized pytest configuration and fixtures for Sutra API tests.

This file provides common fixtures and test utilities used across all test modules,
particularly standardized authentication mocking patterns.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

# Add the shared module to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

from shared.auth_mocking import (
    MockAuthManager,
    AuthMockingHelper,
    StandardAuthMocks,
    MockAuthContext
)
from shared.models import User, UserRole


# Global Authentication Fixtures
@pytest.fixture
def mock_auth_success():
    """Global fixture for successful authentication mocking."""
    mock_auth_manager = MockAuthManager()

    with patch("api.shared.auth.get_auth_manager") as mock_get_auth, \
         patch("api.shared.auth.extract_token_from_request") as mock_extract_token, \
         patch("api.shared.auth.verify_jwt_token") as mock_verify_jwt, \
         patch("api.shared.auth.get_user_id_from_token") as mock_get_user_id:

        # Configure mocks
        mock_get_auth.return_value = mock_auth_manager
        mock_extract_token.return_value = "test-token"
        mock_verify_jwt.return_value = {
            "valid": True,
            "sub": "test-user-123",
            "email": "test@sutra.ai"
        }
        mock_get_user_id.return_value = "test-user-123"

        yield {
            "auth_manager": mock_auth_manager,
            "extract_token": mock_extract_token,
            "verify_jwt": mock_verify_jwt,
            "get_user_id": mock_get_user_id
        }


@pytest.fixture
def mock_admin_auth_success():
    """Global fixture for successful admin authentication mocking."""
    mock_auth_manager = MockAuthManager(
        user_id="admin-user-123",
        email="admin@sutra.ai",
        name="Admin User",
        roles=[UserRole.USER, UserRole.ADMIN]
    )

    with patch("api.shared.auth.get_auth_manager") as mock_get_auth, \
         patch("api.shared.auth.extract_token_from_request") as mock_extract_token, \
         patch("api.shared.auth.verify_jwt_token") as mock_verify_jwt, \
         patch("api.shared.auth.get_user_id_from_token") as mock_get_user_id, \
         patch("api.shared.auth.check_admin_role") as mock_check_admin:

        # Configure mocks
        mock_get_auth.return_value = mock_auth_manager
        mock_extract_token.return_value = "admin-token"
        mock_verify_jwt.return_value = {
            "valid": True,
            "sub": "admin-user-123",
            "email": "admin@sutra.ai",
            "roles": ["user", "admin"]
        }
        mock_get_user_id.return_value = "admin-user-123"
        mock_check_admin.return_value = True

        yield {
            "auth_manager": mock_auth_manager,
            "extract_token": mock_extract_token,
            "verify_jwt": mock_verify_jwt,
            "get_user_id": mock_get_user_id,
            "check_admin": mock_check_admin
        }


@pytest.fixture
def mock_auth_failure():
    """Global fixture for authentication failure mocking."""
    with patch("api.shared.auth.extract_token_from_request") as mock_extract_token, \
         patch("api.shared.auth.verify_jwt_token") as mock_verify_jwt:

        mock_extract_token.return_value = None
        mock_verify_jwt.side_effect = Exception("Authentication failed")

        yield {
            "extract_token": mock_extract_token,
            "verify_jwt": mock_verify_jwt
        }


# Database Mocking Fixtures
@pytest.fixture
def mock_cosmos_client():
    """Global fixture for Cosmos DB mocking."""
    with patch("api.shared.database.get_database_manager") as mock_db_manager:
        mock_manager = Mock()

        # Make all database methods async
        mock_manager.query_items = AsyncMock()
        mock_manager.create_item = AsyncMock()
        mock_manager.replace_item = AsyncMock()
        mock_manager.update_item = AsyncMock()
        mock_manager.delete_item = AsyncMock()
        mock_manager.read_item = AsyncMock()
        mock_manager.upsert_item = AsyncMock()
        mock_manager.get_container = Mock(return_value=mock_manager)

        mock_db_manager.return_value = mock_manager
        yield mock_manager


@pytest.fixture
def mock_request():
    """Global fixture for creating mock HTTP requests."""
    def _create_request(
        method="GET",
        url="http://localhost/api/test",
        body=None,
        headers=None,
        route_params=None,
        params=None
    ):
        import azure.functions as func

        return func.HttpRequest(
            method=method,
            url=url,
            body=body.encode() if isinstance(body, str) else body or b"",
            headers=headers or {},
            route_params=route_params or {},
            params=params or {}
        )

    return _create_request


# Test Environment Setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables and configurations."""
    import os

    # Set test environment variables (only if not already set)
    test_env_vars = {
        "FUNCTIONS_WORKER_RUNTIME": "python",
        "KEY_VAULT_URI": "https://test-keyvault.vault.azure.net/",
        "COSMOS_DB_CONNECTION_STRING": "test-cosmos-connection",
        # Don't set SUTRA_ENVIRONMENT and SUTRA_MAX_REQUESTS_PER_MINUTE here
        # to allow individual tests to control these values
    }

    # Store original values to restore later
    original_values = {}

    for key, value in test_env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    yield

    # Restore original environment variables
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


# Helper Fixtures for Common Test Data
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "test-user-123",
        "email": "test@sutra.ai",
        "name": "Test User",
        "roles": ["user"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def sample_admin_data():
    """Sample admin user data for testing."""
    return {
        "id": "admin-user-123",
        "email": "admin@sutra.ai",
        "name": "Admin User",
        "roles": ["user", "admin"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def sample_collection_data():
    """Sample collection data for testing."""
    return {
        "id": "test-collection-123",
        "name": "Test Collection",
        "description": "A test collection for unit tests",
        "type": "private",
        "ownerId": "test-user-123",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def sample_prompt_data():
    """Sample prompt data for testing."""
    return {
        "id": "test-prompt-123",
        "title": "Test Prompt",
        "description": "A test prompt for unit tests",
        "template": "Hello {{name}}, how are you?",
        "variables": [{"name": "name", "type": "string", "required": True}],
        "tags": ["test", "example"],
        "ownerId": "test-user-123",
        "collectionId": "test-collection-123",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


# Async Test Support
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test Markers for Organization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication-related"
    )
    config.addinivalue_line(
        "markers", "admin: mark test as admin-only functionality"
    )
    config.addinivalue_line(
        "markers", "database: mark test as database-dependent"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# Test Utilities
class TestUtils:
    """Utility class for common test operations."""

    @staticmethod
    def create_mock_http_request(
        method="GET",
        path="/api/test",
        headers=None,
        body=None,
        auth_token="test-token"
    ):
        """Create a standardized mock HTTP request."""
        import azure.functions as func

        default_headers = {"Authorization": f"Bearer {auth_token}"}
        if headers:
            default_headers.update(headers)

        return func.HttpRequest(
            method=method,
            url=f"http://localhost{path}",
            body=body.encode() if isinstance(body, str) else body or b"",
            headers=default_headers,
            route_params={},
            params={}
        )

    @staticmethod
    def assert_error_response(response, expected_status, expected_message_contains=None):
        """Assert that a response contains expected error information."""
        import json

        assert response.status_code == expected_status
        response_data = json.loads(response.get_body())
        assert "error" in response_data

        if expected_message_contains:
            assert expected_message_contains.lower() in response_data["error"].lower()

    @staticmethod
    def assert_success_response(response, expected_status=200, expected_keys=None):
        """Assert that a response is successful and contains expected data."""
        import json

        assert response.status_code == expected_status
        response_data = json.loads(response.get_body())

        if expected_keys:
            for key in expected_keys:
                assert key in response_data


@pytest.fixture
def test_utils():
    """Provide test utilities."""
    return TestUtils
