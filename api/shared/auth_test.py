"""
Tests for auth.py module - Authentication and authorization
"""

import pytest
import os
import jwt
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone
import azure.functions as func

from api.shared.auth import (
    AuthManager,
    AuthenticationError,
    AuthorizationError,
    get_auth_manager,
    extract_token_from_request,
    require_auth,
    require_admin,
    get_current_user,
    check_admin_role,
    check_user_permissions,
    get_user_role,
    require_admin_role,
    require_permission,
    verify_jwt_token,
    get_user_id_from_token,
)
from api.shared.models import User, UserRole


class TestAuthManager:
    """Test suite for AuthManager class."""

    def test_init(self):
        """Test AuthManager initialization."""
        auth_manager = AuthManager()
        assert auth_manager._kv_client is None
        assert auth_manager._auth_config is None

    @patch("api.shared.auth.SecretClient")
    @patch("api.shared.auth.DefaultAzureCredential")
    def test_kv_client_property(self, mock_credential, mock_secret_client):
        """Test Key Vault client property."""
        mock_cred_instance = Mock()
        mock_credential.return_value = mock_cred_instance
        mock_client_instance = Mock()
        mock_secret_client.return_value = mock_client_instance

        with patch.dict(
            os.environ, {"KEY_VAULT_URI": "https://test-kv.vault.azure.net/"}
        ):
            auth_manager = AuthManager()
            client = auth_manager.kv_client

            assert client == mock_client_instance
            mock_secret_client.assert_called_once_with(
                vault_url="https://test-kv.vault.azure.net/",
                credential=mock_cred_instance,
            )

    def test_kv_client_property_no_uri(self):
        """Test Key Vault client property without URI."""
        with patch.dict(os.environ, {}, clear=True):
            auth_manager = AuthManager()
            with pytest.raises(
                ValueError, match="KEY_VAULT_URI environment variable is required"
            ):
                _ = auth_manager.kv_client

    @pytest.mark.asyncio
    @patch("api.shared.auth.SecretClient")
    @patch("api.shared.auth.DefaultAzureCredential")
    async def test_get_auth_config_success(self, mock_credential, mock_secret_client):
        """Test successful auth config retrieval."""
        mock_client_instance = Mock()
        mock_secret_client.return_value = mock_client_instance

        # Mock secrets
        tenant_secret = Mock()
        tenant_secret.value = "test-tenant"
        client_secret = Mock()
        client_secret.value = "test-client"
        policy_secret = Mock()
        policy_secret.value = "test-policy"

        mock_client_instance.get_secret.side_effect = [
            tenant_secret,
            client_secret,
            policy_secret,
        ]

        with patch.dict(
            os.environ, {"KEY_VAULT_URI": "https://test-kv.vault.azure.net/"}
        ):
            auth_manager = AuthManager()
            config = await auth_manager.get_auth_config()

            assert config["tenant_id"] == "test-tenant"
            assert config["client_id"] == "test-client"
            assert config["policy"] == "test-policy"
            assert "issuer" in config
            assert "jwks_uri" in config

    @pytest.mark.asyncio
    @patch("api.shared.auth.SecretClient")
    @patch("api.shared.auth.DefaultAzureCredential")
    async def test_get_auth_config_fallback(self, mock_credential, mock_secret_client):
        """Test auth config fallback to mock."""
        mock_client_instance = Mock()
        mock_secret_client.return_value = mock_client_instance
        mock_client_instance.get_secret.side_effect = Exception("Key Vault error")

        with patch.dict(
            os.environ, {"KEY_VAULT_URI": "https://test-kv.vault.azure.net/"}
        ):
            auth_manager = AuthManager()
            config = await auth_manager.get_auth_config()

            assert config["tenant_id"] == "mock-tenant"
            assert config["client_id"] == "mock-client"

    @pytest.mark.asyncio
    async def test_validate_token_mock_token(self):
        """Test token validation with mock token."""
        auth_manager = AuthManager()
        claims = await auth_manager.validate_token("mock-token")

        assert claims["sub"] == "mock-user-id"
        assert claims["email"] == "dev@sutra.ai"
        assert "user" in claims["roles"]

    @pytest.mark.asyncio
    async def test_validate_token_dev_token(self):
        """Test token validation with dev token."""
        auth_manager = AuthManager()
        claims = await auth_manager.validate_token("dev-12345")

        assert claims["sub"] == "mock-user-id"
        assert claims["email"] == "dev@sutra.ai"

    @pytest.mark.asyncio
    @patch("jwt.decode")
    async def test_validate_token_production(self, mock_jwt_decode):
        """Test token validation in production mode."""
        mock_jwt_decode.return_value = {
            "iss": "mock-issuer",
            "aud": "mock-client",
            "exp": datetime.now(timezone.utc).timestamp() + 3600,
            "sub": "user-123",
        }

        auth_manager = AuthManager()
        # Set mock config
        auth_manager._auth_config = {
            "issuer": "mock-issuer",
            "client_id": "mock-client",
        }

        claims = await auth_manager.validate_token("real-jwt-token")
        assert claims["sub"] == "user-123"

    @pytest.mark.asyncio
    @patch("jwt.decode")
    async def test_validate_token_invalid_issuer(self, mock_jwt_decode):
        """Test token validation with invalid issuer."""
        mock_jwt_decode.return_value = {
            "iss": "wrong-issuer",
            "aud": "mock-client",
            "exp": datetime.now(timezone.utc).timestamp() + 3600,
        }

        auth_manager = AuthManager()
        auth_manager._auth_config = {
            "issuer": "mock-issuer",
            "client_id": "mock-client",
        }

        with pytest.raises(AuthenticationError, match="Invalid token issuer"):
            await auth_manager.validate_token("invalid-token")

    @pytest.mark.asyncio
    @patch("jwt.decode")
    async def test_validate_token_expired(self, mock_jwt_decode):
        """Test token validation with expired token."""
        mock_jwt_decode.return_value = {
            "iss": "mock-issuer",
            "aud": "mock-client",
            "exp": datetime.now(timezone.utc).timestamp() - 3600,  # Expired
        }

        auth_manager = AuthManager()
        auth_manager._auth_config = {
            "issuer": "mock-issuer",
            "client_id": "mock-client",
        }

        with pytest.raises(AuthenticationError, match="Token has expired"):
            await auth_manager.validate_token("expired-token")

    @pytest.mark.asyncio
    async def test_get_user_from_token(self):
        """Test user extraction from token."""
        auth_manager = AuthManager()
        user = await auth_manager.get_user_from_token("mock-token")

        assert isinstance(user, User)
        assert user.id == "mock-user-id"
        assert user.email == "dev@sutra.ai"
        assert UserRole.USER in user.roles

    @pytest.mark.asyncio
    async def test_get_user_from_token_admin(self):
        """Test admin user extraction from token."""
        auth_manager = AuthManager()
        user = await auth_manager.get_user_from_token("mock-token")

        # Modify user to be admin for testing
        with patch.object(auth_manager, "validate_token") as mock_validate:
            mock_validate.return_value = {
                "sub": "admin-123",
                "email": "admin@sutra.ai",
                "name": "Admin User",
                "roles": ["admin"],
            }

            user = await auth_manager.get_user_from_token("admin-token")
            assert UserRole.ADMIN in user.roles

    @pytest.mark.asyncio
    async def test_check_permission_admin(self):
        """Test permission check for admin user."""
        auth_manager = AuthManager()
        user = User(
            id="admin-123",
            email="admin@test.com",
            name="Admin User",
            roles=[UserRole.ADMIN],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Admin should have all permissions
        assert await auth_manager.check_permission(user, "prompts", "create")
        assert await auth_manager.check_permission(user, "admin", "manage_users")

    @pytest.mark.asyncio
    async def test_check_permission_user(self):
        """Test permission check for regular user."""
        auth_manager = AuthManager()
        user = User(
            id="user-123",
            email="user@test.com",
            name="Regular User",
            roles=[UserRole.USER],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # User should have basic permissions
        assert await auth_manager.check_permission(user, "prompts", "create")
        assert await auth_manager.check_permission(user, "collections", "read")

        # User should not have admin permissions
        assert not await auth_manager.check_permission(user, "admin", "manage_users")


class TestAuthFunctions:
    """Test suite for authentication utility functions."""

    def test_get_auth_manager_singleton(self):
        """Test that get_auth_manager returns singleton."""
        manager1 = get_auth_manager()
        manager2 = get_auth_manager()
        assert manager1 is manager2

    def test_extract_token_from_request_valid(self):
        """Test token extraction from valid request."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"Authorization": "Bearer test-token-123"}

        token = extract_token_from_request(req)
        assert token == "test-token-123"

    def test_extract_token_from_request_no_bearer(self):
        """Test token extraction without Bearer prefix."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"Authorization": "test-token-123"}

        token = extract_token_from_request(req)
        assert token is None

    def test_extract_token_from_request_no_header(self):
        """Test token extraction without Authorization header."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {}

        token = extract_token_from_request(req)
        assert token is None

    def test_verify_jwt_token_mock_token(self):
        """Test JWT token verification with mock token."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"Authorization": "Bearer mock-token"}

        result = verify_jwt_token(req)
        assert result["valid"] is True
        assert result["claims"]["sub"] == "mock-user-id"

    def test_verify_jwt_token_admin_token(self):
        """Test JWT token verification with admin token."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"Authorization": "Bearer mock-admin-token"}

        result = verify_jwt_token(req)
        assert result["valid"] is True
        assert "admin" in result["claims"]["roles"]

    def test_verify_jwt_token_no_token(self):
        """Test JWT token verification without token."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {}

        result = verify_jwt_token(req)
        assert result["valid"] is False
        assert "No token provided" in result["message"]

    @patch("jwt.decode")
    def test_verify_jwt_token_real_token(self, mock_jwt_decode):
        """Test JWT token verification with real token."""
        mock_jwt_decode.return_value = {"sub": "user-123", "email": "user@test.com"}

        req = Mock(spec=func.HttpRequest)
        req.headers = {"Authorization": "Bearer real-jwt-token"}

        result = verify_jwt_token(req)
        assert result["valid"] is True
        assert result["claims"]["sub"] == "user-123"

    def test_get_user_id_from_token_mock(self):
        """Test user ID extraction from mock token."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"Authorization": "Bearer mock-token"}

        user_id = get_user_id_from_token(req)
        assert user_id == "mock-user-id"

    def test_get_user_id_from_token_dev(self):
        """Test user ID extraction from dev token."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"Authorization": "Bearer dev-12345"}

        user_id = get_user_id_from_token(req)
        assert user_id == "mock-user-id"

    @patch("jwt.decode")
    def test_get_user_id_from_token_real(self, mock_jwt_decode):
        """Test user ID extraction from real token."""
        mock_jwt_decode.return_value = {"sub": "user-123"}

        req = Mock(spec=func.HttpRequest)
        req.headers = {"Authorization": "Bearer real-token"}

        user_id = get_user_id_from_token(req)
        assert user_id == "user-123"

    def test_get_user_id_from_token_no_token(self):
        """Test user ID extraction without token."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {}

        user_id = get_user_id_from_token(req)
        assert user_id is None

    def test_check_admin_role_development(self):
        """Test admin role check in development mode."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"Authorization": "Bearer mock-admin-token"}

        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            result = check_admin_role(req)
            assert result is True

    def test_check_admin_role_no_admin(self):
        """Test admin role check without admin token."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"Authorization": "Bearer mock-token"}

        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            result = check_admin_role(req)
            assert result is False

    @patch("jwt.decode")
    def test_check_admin_role_jwt(self, mock_jwt_decode):
        """Test admin role check with JWT token."""
        mock_jwt_decode.return_value = {"sub": "user-123", "roles": ["admin"]}

        req = Mock(spec=func.HttpRequest)
        req.headers = {"Authorization": "Bearer jwt-token"}

        result = check_admin_role(req)
        assert result is True

    @patch("jwt.decode")
    def test_check_admin_role_no_admin_jwt(self, mock_jwt_decode):
        """Test admin role check with non-admin JWT token."""
        mock_jwt_decode.return_value = {"roles": ["user"]}

        req = Mock(spec=func.HttpRequest)
        req.headers = {"Authorization": "Bearer jwt-token"}

        result = check_admin_role(req)
        assert result is False


class TestAuthDecorators:
    """Test suite for authentication decorators."""

    @pytest.mark.asyncio
    async def test_require_auth_success(self):
        """Test require_auth decorator with valid token."""

        @require_auth()
        async def test_func(req):
            return func.HttpResponse("Success", status_code=200)

        req = Mock(spec=func.HttpRequest)
        req.headers = {"Authorization": "Bearer mock-token"}

        response = await test_func(req)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_require_auth_no_token(self):
        """Test require_auth decorator without token."""

        @require_auth()
        async def test_func(req):
            return func.HttpResponse("Success", status_code=200)

        req = Mock(spec=func.HttpRequest)
        req.headers = {}

        response = await test_func(req)
        assert response.status_code == 401
        assert "authentication_required" in response.get_body().decode()

    @pytest.mark.asyncio
    async def test_require_auth_with_permissions(self):
        """Test require_auth decorator with permission check."""

        @require_auth(resource="prompts", action="create")
        async def test_func(req):
            return func.HttpResponse("Success", status_code=200)

        req = Mock(spec=func.HttpRequest)
        req.headers = {"Authorization": "Bearer mock-token"}

        response = await test_func(req)
        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch("api.shared.auth.get_auth_manager")
    async def test_require_admin_success(self, mock_get_auth_manager):
        """Test require_admin decorator with admin token."""
        # Mock the auth manager and its methods
        mock_auth_manager = Mock()
        mock_user = Mock()
        mock_user.role = UserRole.ADMIN
        mock_auth_manager.get_user_from_token = AsyncMock(return_value=mock_user)
        mock_auth_manager.check_permission = AsyncMock(return_value=True)
        mock_get_auth_manager.return_value = mock_auth_manager

        @require_admin
        async def test_func(req):
            return func.HttpResponse("Admin Success", status_code=200)

        req = Mock(spec=func.HttpRequest)
        req.headers = {"Authorization": "Bearer mock-admin-token"}

        response = await test_func(req)
        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch("api.shared.auth.get_auth_manager")
    async def test_require_admin_denied(self, mock_get_auth_manager):
        """Test require_admin decorator with non-admin token."""
        # Mock the auth manager with a non-admin user
        mock_auth_manager = Mock()
        mock_user = Mock()
        mock_user.role = UserRole.MEMBER
        mock_auth_manager.get_user_from_token = AsyncMock(return_value=mock_user)
        mock_auth_manager.check_permission = AsyncMock(return_value=False)
        mock_get_auth_manager.return_value = mock_auth_manager

        @require_admin
        async def test_func(req):
            return func.HttpResponse("Admin Success", status_code=200)

        req = Mock(spec=func.HttpRequest)
        req.headers = {"Authorization": "Bearer mock-token"}

        response = await test_func(req)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_current_user(self):
        """Test get_current_user function."""
        req = Mock(spec=func.HttpRequest)
        req.current_user = User(
            id="user-123",
            email="user@test.com",
            name="Test User",
            roles=[UserRole.USER],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        user = await get_current_user(req)
        assert user.id == "user-123"
        assert user.email == "user@test.com"

    @pytest.mark.asyncio
    async def test_get_current_user_none(self):
        """Test get_current_user with no user."""
        req = Mock(spec=func.HttpRequest)

        user = await get_current_user(req)
        assert user is None


class TestPermissionChecks:
    """Test suite for permission checking functions."""

    @patch("api.shared.database.get_database_manager")
    def test_check_user_permissions_owner(self, mock_get_db_manager):
        """Test permission check for resource owner."""
        mock_db_manager = Mock()
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container
        mock_container.read_item.return_value = {"creatorId": "user-123"}
        mock_get_db_manager.return_value = mock_db_manager

        result = check_user_permissions("user-123", "prompt", "prompt-456", "read")
        assert result is True

    @patch("api.shared.database.get_database_manager")
    def test_check_user_permissions_not_owner(self, mock_get_db_manager):
        """Test permission check for non-owner."""
        mock_db_manager = Mock()
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container
        mock_container.read_item.return_value = {"creatorId": "other-user"}
        mock_get_db_manager.return_value = mock_db_manager

        result = check_user_permissions("user-123", "prompt", "prompt-456", "read")
        assert result is False

    @patch("api.shared.database.get_database_manager")
    def test_check_user_permissions_explicit(self, mock_get_db_manager):
        """Test permission check with explicit permissions."""
        mock_db_manager = Mock()
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container
        mock_container.read_item.return_value = {
            "creatorId": "other-user",
            "permissions": {"user-123": ["read", "write"]},
        }
        mock_get_db_manager.return_value = mock_db_manager

        result = check_user_permissions("user-123", "prompt", "prompt-456", "read")
        assert result is True

    @patch("api.shared.database.get_database_manager")
    def test_get_user_role_admin(self, mock_get_db_manager):
        """Test get_user_role for admin user."""
        mock_db_manager = Mock()
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container
        mock_container.read_item.return_value = {"role": "admin"}
        mock_get_db_manager.return_value = mock_db_manager

        role = get_user_role("admin-123")
        assert role == UserRole.ADMIN

    @patch("api.shared.database.get_database_manager")
    def test_get_user_role_default(self, mock_get_db_manager):
        """Test get_user_role with default role."""
        mock_db_manager = Mock()
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container
        mock_container.read_item.side_effect = Exception("User not found")
        mock_get_db_manager.return_value = mock_db_manager

        role = get_user_role("user-123")
        assert role == UserRole.MEMBER
