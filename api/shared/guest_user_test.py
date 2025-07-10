import asyncio
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch

import azure.functions as func
import pytest
from shared.guest_user import (
    GuestUserManager,
    allow_guest_access,
    get_guest_usage_stats,
)

from ..conftest import create_auth_request


class TestGuestUserManager:
    """Test suite for GuestUserManager class."""

    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager."""
        mock_db = Mock()
        mock_db._development_mode = True
        mock_db.create_item = AsyncMock()
        mock_db.read_item = AsyncMock()
        mock_db.update_item = AsyncMock()
        return mock_db

    @pytest.fixture
    def guest_manager(self, mock_db_manager):
        """Create GuestUserManager instance with mocked database."""
        return GuestUserManager(mock_db_manager)

    @pytest.mark.asyncio
    async def test_get_guest_limits_default(self, guest_manager):
        """Test getting default guest limits when no config exists."""
        # Arrange
        guest_manager.db_manager.read_item.side_effect = Exception("Not found")

        # Act
        limits = await guest_manager.get_guest_limits()

        # Assert
        assert limits["llm_calls_per_day"] == 5
        assert limits["prompts_per_day"] == 10
        assert limits["collections_per_session"] == 3
        assert limits["session_duration_hours"] == 24

    @pytest.mark.asyncio
    async def test_get_guest_limits_from_config(self, guest_manager):
        """Test getting guest limits from admin configuration."""
        # Arrange
        config_data = {"limits": {"llm_calls_per_day": 10, "prompts_per_day": 20}}
        guest_manager.db_manager.read_item.return_value = config_data

        # Act
        limits = await guest_manager.get_guest_limits()

        # Assert
        assert limits["llm_calls_per_day"] == 10
        assert limits["prompts_per_day"] == 20
        assert limits["collections_per_session"] == 3  # Default merged

    @pytest.mark.asyncio
    async def test_create_guest_session(self, guest_manager):
        """Test creating a new guest session."""
        # Arrange
        ip_address = "192.168.1.100"
        user_agent = "Mozilla/5.0"

        # Act
        session = await guest_manager.create_guest_session(ip_address, user_agent)

        # Assert
        assert session["type"] == "guest_session"
        assert session["ip_address"] == ip_address
        assert session["user_agent"] == user_agent
        assert session["active"] is True
        assert session["usage"]["llm_calls"] == 0
        assert "id" in session
        assert "created_at" in session
        assert "expires_at" in session

    @pytest.mark.asyncio
    async def test_get_or_create_anonymous_session_new(self, guest_manager):
        """Test creating new anonymous session based on IP."""
        # Arrange
        ip_address = "10.0.0.1"
        guest_manager.get_guest_session = AsyncMock(return_value=None)

        # Act
        session = await guest_manager.get_or_create_anonymous_session(ip_address)

        # Assert
        assert session["type"] == "anonymous_session"
        assert session["ip_address"] == ip_address
        assert session["anonymous"] is True
        assert "anon_" in session["id"]

    @pytest.mark.asyncio
    async def test_get_or_create_anonymous_session_existing(self, guest_manager):
        """Test getting existing anonymous session."""
        # Arrange
        ip_address = "10.0.0.2"
        existing_session = {
            "id": "anon_123456",
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "usage": {"llm_calls": 2},
        }
        guest_manager.get_guest_session = AsyncMock(return_value=existing_session)

        # Act
        session = await guest_manager.get_or_create_anonymous_session(ip_address)

        # Assert
        assert session["id"] == "anon_123456"
        assert session["usage"]["llm_calls"] == 2

    @pytest.mark.asyncio
    async def test_check_usage_limit_within_limit(self, guest_manager):
        """Test usage limit check when within limits."""
        # Arrange
        session = {"usage": {"llm_calls": 3}, "limits": {"llm_calls_per_day": 5}}

        # Act
        result = await guest_manager.check_usage_limit(session, "llm_calls")

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_check_usage_limit_exceeded(self, guest_manager):
        """Test usage limit check when limit is exceeded."""
        # Arrange
        session = {"usage": {"llm_calls": 5}, "limits": {"llm_calls_per_day": 5}}

        # Act
        result = await guest_manager.check_usage_limit(session, "llm_calls")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_increment_usage(self, guest_manager):
        """Test incrementing usage counter."""
        # Arrange
        session = {"id": "test_session", "usage": {"llm_calls": 2}}

        # Act
        updated_session = await guest_manager.increment_usage(session, "llm_calls")

        # Assert
        assert updated_session["usage"]["llm_calls"] == 3

    @pytest.mark.asyncio
    async def test_update_guest_session(self, guest_manager):
        """Test updating guest session."""
        # Arrange
        session = {"id": "test_session", "usage": {"llm_calls": 1}}

        # Act
        updated_session = await guest_manager.update_guest_session(session)

        # Assert
        assert "last_activity" in updated_session["usage"]

    @pytest.mark.asyncio
    async def test_get_guest_session_development_mode(self, guest_manager):
        """Test getting guest session in development mode."""
        # Arrange
        session_id = "test_dev_session"

        # Act
        session = await guest_manager.get_guest_session(session_id)

        # Assert
        assert session["id"] == session_id
        assert session["_mock"] is True


class TestAllowGuestAccessDecorator:
    """Test suite for allow_guest_access decorator."""

    def create_mock_request(self, auth_header=None, guest_session_id=None, ip_address="127.0.0.1"):
        """Create mock HTTP request."""
        headers = {"x-forwarded-for": ip_address}
        if auth_header:
            headers["x-ms-client-principal"] = auth_header
        if guest_session_id:
            headers["x-guest-session-id"] = guest_session_id

        mock_req = Mock(spec=func.HttpRequest)
        mock_req.headers = headers
        return mock_req

    @pytest.mark.asyncio
    async def test_authenticated_user_bypass(self):
        """Test that authenticated users bypass guest logic."""

        # Arrange
        @allow_guest_access(usage_type="llm_calls")
        async def test_function(req):
            return func.HttpResponse("authenticated", status_code=200)

        req = self.create_mock_request(auth_header="valid_auth_token")

        # Act
        response = await test_function(req)

        # Assert
        assert response.status_code == 200
        assert response.get_body() == b"authenticated"

    @pytest.mark.asyncio
    async def test_anonymous_user_within_limits(self):
        """Test anonymous user within usage limits."""

        # Arrange
        @allow_guest_access(usage_type="llm_calls", allow_anonymous=True)
        async def test_function(req):
            return func.HttpResponse("anonymous_success", status_code=200)

        req = self.create_mock_request()

        with patch("shared.database.get_database_manager") as mock_db:
            mock_db.return_value._development_mode = True

            # Act
            response = await test_function(req)

            # Assert
            assert response.status_code == 200
            assert hasattr(req, "current_user")
            assert req.current_user.role in ["guest", "anonymous"]

    @pytest.mark.asyncio
    async def test_anonymous_user_limit_exceeded(self):
        """Test anonymous user with exceeded limits."""

        # Arrange
        @allow_guest_access(usage_type="llm_calls", allow_anonymous=True)
        async def test_function(req):
            return func.HttpResponse("should_not_reach", status_code=200)

        req = self.create_mock_request()

        with patch("shared.database.get_database_manager") as mock_db, patch(
            "shared.guest_user.GuestUserManager"
        ) as mock_manager_class:
            mock_db.return_value._development_mode = True
            mock_manager = Mock()
            mock_manager.get_or_create_anonymous_session = AsyncMock(
                return_value={
                    "id": "test_session",
                    "usage": {"llm_calls": 5},
                    "limits": {"llm_calls_per_day": 5},
                }
            )
            mock_manager.check_usage_limit = AsyncMock(return_value=False)
            mock_manager_class.return_value = mock_manager

            # Act
            response = await test_function(req)

            # Assert
            assert response.status_code == 429
            response_data = json.loads(response.get_body())
            assert response_data["error"] == "guest_limit_exceeded"

    @pytest.mark.asyncio
    async def test_guest_session_creation(self):
        """Test guest session creation during decorator execution."""

        # Arrange
        @allow_guest_access(usage_type="llm_calls", allow_anonymous=True)
        async def test_function(req):
            return func.HttpResponse("session_created", status_code=200)

        req = self.create_mock_request()

        with patch("shared.database.get_database_manager") as mock_db, patch(
            "shared.guest_user.GuestUserManager"
        ) as mock_manager_class:
            mock_db.return_value._development_mode = True
            mock_manager = Mock()
            mock_session = {
                "id": "new_session",
                "usage": {"llm_calls": 0},
                "limits": {"llm_calls_per_day": 5},
                "active": True,
            }
            mock_manager.get_or_create_anonymous_session = AsyncMock(return_value=mock_session)
            mock_manager.check_usage_limit = AsyncMock(return_value=True)
            mock_manager.increment_usage = AsyncMock(return_value=mock_session)
            mock_manager_class.return_value = mock_manager

            # Act
            response = await test_function(req)

            # Assert
            assert response.status_code == 200
            assert hasattr(req, "guest_session")
            assert req.guest_session["id"] == "new_session"


class TestGuestUsageStats:
    """Test suite for guest usage statistics."""

    @pytest.mark.asyncio
    async def test_get_guest_usage_stats_success(self):
        """Test getting guest usage statistics successfully."""
        # Arrange
        session_id = "test_stats_session"
        mock_db = Mock()

        with patch("shared.guest_user.GuestUserManager") as mock_manager_class:
            mock_manager = Mock()
            mock_session = {
                "id": session_id,
                "active": True,
                "created_at": "2025-06-24T10:00:00Z",
                "expires_at": "2025-06-25T10:00:00Z",
                "usage": {"llm_calls": 3, "prompts_created": 2},
                "limits": {"llm_calls_per_day": 5, "prompts_per_day": 10},
            }
            mock_manager.get_guest_session = AsyncMock(return_value=mock_session)
            mock_manager_class.return_value = mock_manager

            # Act
            stats = await get_guest_usage_stats(session_id, mock_db)

            # Assert
            assert stats["session_id"] == session_id
            assert stats["active"] is True
            assert stats["usage"]["llm_calls"] == 3
            assert stats["remaining"]["llm_calls"] == 2

    @pytest.mark.asyncio
    async def test_get_guest_usage_stats_not_found(self):
        """Test getting stats for nonexistent session."""
        # Arrange
        session_id = "nonexistent_session"
        mock_db = Mock()

        with patch("shared.guest_user.GuestUserManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager.get_guest_session = AsyncMock(return_value=None)
            mock_manager_class.return_value = mock_manager

            # Act
            stats = await get_guest_usage_stats(session_id, mock_db)

            # Assert
            assert stats["error"] == "Session not found"


if __name__ == "__main__":
    pytest.main([__file__])
