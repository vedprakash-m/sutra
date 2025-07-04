import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta

import azure.functions as func
from . import main as guest_api_main


class TestGuestAPI:
    """Test suite for Guest API endpoints."""

    def create_request(
        self,
        method="GET",
        body=None,
        route_params=None,
        params=None,
        url="http://localhost/api/guest",
        guest_session_id=None,
    ):
        """Helper to create requests for guest API."""
        headers = {"x-forwarded-for": "127.0.0.1", "user-agent": "test-browser/1.0"}

        if guest_session_id:
            headers["x-guest-session-id"] = guest_session_id

        if method in ["POST", "PUT"] and body:
            headers["Content-Type"] = "application/json"

        return func.HttpRequest(
            method=method,
            url=url,
            body=json.dumps(body).encode("utf-8") if body else b"",
            headers=headers,
            route_params=route_params or {},
            params=params or {},
        )

    @pytest.fixture
    def mock_guest_manager(self):
        """Mock guest user manager."""
        with patch("api.guest_api.GuestUserManager") as mock_manager_class:
            mock_manager = Mock()
            # Make all methods async
            mock_manager.create_guest_session = AsyncMock()
            mock_manager.get_guest_session = AsyncMock()
            mock_manager.update_guest_session = AsyncMock()
            mock_manager.get_or_create_anonymous_session = AsyncMock()
            mock_manager_class.return_value = mock_manager
            yield mock_manager

    @pytest.mark.asyncio
    async def test_create_guest_session(self, mock_guest_manager):
        """Test creating a new guest session."""
        # Arrange
        mock_session = {
            "id": "guest_123456789",
            "type": "guest_session",
            "ip_address": "127.0.0.1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "usage": {"llm_calls": 0, "prompts_created": 0},
            "limits": {"llm_calls_per_day": 5, "prompts_per_day": 10},
            "active": True,
        }

        mock_guest_manager.create_guest_session.return_value = mock_session

        req = self.create_request(
            method="POST",
            url="http://localhost/api/guest/session",
            route_params={"action": "session"},
        )

        # Act
        response = await guest_api_main(req)

        # Assert
        assert response.status_code == 201
        response_data = json.loads(response.get_body())
        assert response_data["session"]["id"] == "guest_123456789"
        assert response_data["session"]["active"] is True
        assert "usage" in response_data
        assert "limits" in response_data
        mock_guest_manager.create_guest_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_existing_guest_session(self, mock_guest_manager):
        """Test retrieving an existing guest session."""
        # Arrange
        session_id = "guest_987654321"
        mock_session = {
            "id": session_id,
            "type": "guest_session",
            "usage": {"llm_calls": 2, "prompts_created": 1},
            "limits": {"llm_calls_per_day": 5, "prompts_per_day": 10},
            "active": True,
        }

        mock_guest_manager.get_guest_session.return_value = mock_session

        req = self.create_request(
            method="GET",
            url="http://localhost/api/guest/session",
            route_params={"action": "session"},
            guest_session_id=session_id,
        )

        # Act
        response = await guest_api_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["session"]["id"] == session_id
        assert response_data["usage"]["llm_calls"] == 2
        mock_guest_manager.get_guest_session.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_get_nonexistent_guest_session(self, mock_guest_manager):
        """Test retrieving a nonexistent guest session."""
        # Arrange
        session_id = "guest_nonexistent"
        mock_guest_manager.get_guest_session.return_value = None

        req = self.create_request(
            method="GET",
            url="http://localhost/api/guest/session",
            route_params={"action": "session"},
            guest_session_id=session_id,
        )

        # Act
        response = await guest_api_main(req)

        # Assert
        assert response.status_code == 404
        response_data = json.loads(response.get_body())
        assert response_data["error"] == "session_not_found"

    @pytest.mark.asyncio
    async def test_guest_session_expired(self, mock_guest_manager):
        """Test handling of expired guest session."""
        # Arrange
        session_id = "guest_expired"
        expired_time = datetime.now(timezone.utc) - timedelta(hours=25)
        mock_session = {
            "id": session_id,
            "expires_at": expired_time.isoformat(),
            "active": False,
            "usage": {"llm_calls": 3},
            "limits": {"llm_calls_per_day": 5},
        }

        mock_guest_manager.get_guest_session.return_value = mock_session

        req = self.create_request(
            method="GET",
            url="http://localhost/api/guest/session",
            route_params={"action": "session"},
            guest_session_id=session_id,
        )

        # Act
        response = await guest_api_main(req)

        # Assert
        assert response.status_code == 410
        response_data = json.loads(response.get_body())
        assert response_data["error"] == "session_expired"

    @pytest.mark.asyncio
    async def test_method_not_allowed(self):
        """Test unsupported HTTP method."""
        req = self.create_request(
            method="DELETE", url="http://localhost/api/guest/session"  # Not supported
        )

        # Act
        response = await guest_api_main(req)

        # Assert
        assert response.status_code == 405
        response_data = json.loads(response.get_body())
        assert "Method not allowed" in response_data["error"]

    @pytest.mark.asyncio
    async def test_guest_session_usage_stats(self, mock_guest_manager):
        """Test retrieving guest session usage statistics."""
        # Arrange
        session_id = "guest_stats_test"
        mock_session = {
            "id": session_id,
            "usage": {
                "llm_calls": 3,
                "prompts_created": 2,
                "collections_created": 1,
                "last_activity": datetime.now(timezone.utc).isoformat(),
            },
            "limits": {
                "llm_calls_per_day": 5,
                "prompts_per_day": 10,
                "collections_per_session": 3,
            },
            "active": True,
        }

        mock_guest_manager.get_guest_session.return_value = mock_session

        req = self.create_request(
            method="GET",
            url="http://localhost/api/guest/session",
            route_params={"action": "session"},
            guest_session_id=session_id,
        )

        # Act
        response = await guest_api_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["remaining"]["llm_calls"] == 2  # 5 - 3
        assert response_data["remaining"]["prompts_created"] == 8  # 10 - 2
        assert response_data["remaining"]["collections_created"] == 2  # 3 - 1

    @pytest.mark.asyncio
    async def test_create_session_error_handling(self, mock_guest_manager):
        """Test error handling during session creation."""
        # Arrange
        mock_guest_manager.create_guest_session.side_effect = Exception(
            "Database error"
        )

        req = self.create_request(
            method="POST",
            url="http://localhost/api/guest/session",
            route_params={"action": "session"},
        )

        # Act
        response = await guest_api_main(req)

        # Assert
        assert response.status_code == 500
        response_data = json.loads(response.get_body())
        assert "Failed to create guest session" in response_data["message"]


if __name__ == "__main__":
    pytest.main([__file__])
