"""
Tests for Guest API
"""
import json
import sys
import os
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import azure.functions as func

# Add the API directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from guest_api import main as guest_api_main


class TestGuestAPI:

    def create_request(self, method="GET", url=None, headers=None, body=None, route_params=None, guest_session_id=None):
        """Helper to create mock Azure Function requests."""
        headers = headers or {}
        if guest_session_id:
            headers["x-guest-session-id"] = guest_session_id
        headers.setdefault("x-forwarded-for", "127.0.0.1")
        headers.setdefault("user-agent", "test-agent")

        route_params = route_params or {}

        req = Mock(spec=func.HttpRequest)
        req.method = method
        req.url = url or "http://localhost/api/guest/session"
        req.headers = headers
        req.route_params = route_params
        req.get_body.return_value = body or b""
        return req

    @pytest.fixture
    def mock_guest_manager(self):
        """Mock the GuestUserManager for tests."""
        with patch("api.guest_api.GuestUserManager") as mock_manager_class, \
             patch("api.guest_api.get_database_manager") as mock_db_manager:

            mock_manager = Mock()
            # Make all methods async
            mock_manager.create_guest_session = AsyncMock()
            mock_manager.get_guest_session = AsyncMock()
            mock_manager.update_guest_session = AsyncMock()
            mock_manager.get_or_create_anonymous_session = AsyncMock()
            mock_manager_class.return_value = mock_manager

            mock_db_manager.return_value = Mock()

            yield mock_manager

    @pytest.mark.asyncio
    async def test_get_or_create_session_new(self, mock_guest_manager):
        """Test creating a new guest session when none exists."""
        # Arrange
        mock_session = {
            "id": "guest_123456789",
            "type": "guest_session",
            "ip_address": "127.0.0.1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "active": True
        }

        mock_guest_manager.get_guest_session.return_value = None  # No existing session
        mock_guest_manager.create_guest_session.return_value = mock_session

        # Mock get_guest_usage_stats
        with patch('api.guest_api.get_guest_usage_stats') as mock_stats:
            mock_stats.return_value = {
                "usage": {"llm_calls": 0, "prompts_created": 0},
                "limits": {"llm_calls_per_day": 5, "prompts_per_day": 10},
                "remaining": {"llm_calls": 5, "prompts_created": 10}
            }

            req = self.create_request(
                method="GET",
                url="http://localhost/api/guest/session",
                route_params={"action": "session"}
            )

            # Act
            response = await guest_api_main(req)

            # Assert
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["session"]["id"] == "guest_123456789"
            assert response_data["session"]["active"] is True
            assert response_data["usage"]["llm_calls"] == 0
            assert response_data["remaining"]["llm_calls"] == 5
            mock_guest_manager.create_guest_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_existing_guest_session(self, mock_guest_manager):
        """Test retrieving an existing guest session."""
        # Arrange
        session_id = "guest_987654321"
        mock_session = {
            "id": session_id,
            "type": "guest_session",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat(),
            "active": True
        }

        mock_guest_manager.get_guest_session.return_value = mock_session

        # Mock get_guest_usage_stats
        with patch('api.guest_api.get_guest_usage_stats') as mock_stats:
            mock_stats.return_value = {
                "usage": {"llm_calls": 2, "prompts_created": 1},
                "limits": {"llm_calls_per_day": 5, "prompts_per_day": 10},
                "remaining": {"llm_calls": 3, "prompts_created": 9}
            }

            req = self.create_request(
                method="GET",
                url="http://localhost/api/guest/session",
                route_params={"action": "session"},
                guest_session_id=session_id
            )

            # Act
            response = await guest_api_main(req)

            # Assert
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["session"]["id"] == session_id
            assert response_data["usage"]["llm_calls"] == 2
            assert response_data["remaining"]["llm_calls"] == 3
            mock_guest_manager.get_guest_session.assert_called_once_with(session_id)
            # Should not create a new session since we found an existing one
            mock_guest_manager.create_guest_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_expired_session_creates_new(self, mock_guest_manager):
        """Test handling of expired guest session - should create new one."""
        # Arrange
        session_id = "guest_expired"
        expired_session = {
            "id": session_id,
            "expires_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "active": False
        }

        new_session = {
            "id": "guest_new_123",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "active": True
        }

        mock_guest_manager.get_guest_session.return_value = expired_session
        mock_guest_manager.create_guest_session.return_value = new_session

        # Mock get_guest_usage_stats
        with patch('api.guest_api.get_guest_usage_stats') as mock_stats:
            mock_stats.return_value = {
                "usage": {"llm_calls": 0, "prompts_created": 0},
                "limits": {"llm_calls_per_day": 5, "prompts_per_day": 10},
                "remaining": {"llm_calls": 5, "prompts_created": 10}
            }

            req = self.create_request(
                method="GET",
                url="http://localhost/api/guest/session",
                route_params={"action": "session"},
                guest_session_id=session_id
            )

            # Act
            response = await guest_api_main(req)

            # Assert
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["session"]["id"] == "guest_new_123"
            assert response_data["session"]["active"] is True
            # Should create new session since old one was expired/inactive
            mock_guest_manager.create_guest_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_stats(self, mock_guest_manager):
        """Test retrieving detailed session stats."""
        # Arrange
        session_id = "guest_stats_test"

        with patch('api.guest_api.get_guest_usage_stats') as mock_stats:
            mock_stats.return_value = {
                "usage": {
                    "llm_calls": 3,
                    "prompts_created": 2,
                    "collections_created": 1,
                    "last_activity": datetime.now(timezone.utc).isoformat()
                },
                "limits": {
                    "llm_calls_per_day": 5,
                    "prompts_per_day": 10,
                    "collections_per_session": 3
                },
                "remaining": {
                    "llm_calls": 2,
                    "prompts_created": 8,
                    "collections_created": 2
                }
            }

            req = self.create_request(
                method="GET",
                url=f"http://localhost/api/guest/{session_id}/stats",
                route_params={"action": "stats", "session_id": session_id}
            )

            # Act
            response = await guest_api_main(req)

            # Assert
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["remaining"]["llm_calls"] == 2
            assert response_data["usage"]["llm_calls"] == 3
            mock_stats.assert_called_once_with(session_id, mock_guest_manager.return_value)

    @pytest.mark.asyncio
    async def test_get_session_stats_not_found(self, mock_guest_manager):
        """Test retrieving stats for nonexistent session."""
        # Arrange
        session_id = "guest_nonexistent"

        with patch('api.guest_api.get_guest_usage_stats') as mock_stats:
            mock_stats.return_value = {
                "error": "session_not_found",
                "message": "Guest session not found"
            }

            req = self.create_request(
                method="GET",
                url=f"http://localhost/api/guest/{session_id}/stats",
                route_params={"action": "stats", "session_id": session_id}
            )

            # Act
            response = await guest_api_main(req)

            # Assert
            assert response.status_code == 404
            response_data = json.loads(response.get_body())
            assert response_data["error"] == "session_not_found"

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, mock_guest_manager):
        """Test unsupported HTTP methods."""
        req = self.create_request(
            method="DELETE",
            url="http://localhost/api/guest/session",
            route_params={"action": "session"}
        )

        # Act
        response = await guest_api_main(req)

        # Assert
        assert response.status_code == 405
        response_data = json.loads(response.get_body())
        assert response_data["error"] == "Method not allowed"

    @pytest.mark.asyncio
    async def test_session_creation_error_handling(self, mock_guest_manager):
        """Test error handling during session creation."""
        # Arrange
        mock_guest_manager.get_guest_session.return_value = None
        mock_guest_manager.create_guest_session.side_effect = Exception("Database error")

        req = self.create_request(
            method="GET",
            url="http://localhost/api/guest/session",
            route_params={"action": "session"}
        )

        # Act
        response = await guest_api_main(req)

        # Assert
        assert response.status_code == 500
        response_data = json.loads(response.get_body())
        assert response_data["error"] == "session_error"
        assert "Could not create guest session" in response_data["message"]

    @pytest.mark.asyncio
    async def test_stats_error_handling(self, mock_guest_manager):
        """Test error handling when getting session stats."""
        # Arrange
        session_id = "guest_error_test"

        with patch('api.guest_api.get_guest_usage_stats') as mock_stats:
            mock_stats.side_effect = Exception("Stats calculation error")

            req = self.create_request(
                method="GET",
                url=f"http://localhost/api/guest/{session_id}/stats",
                route_params={"action": "stats", "session_id": session_id}
            )

            # Act
            response = await guest_api_main(req)

            # Assert
            assert response.status_code == 500
            response_data = json.loads(response.get_body())
            assert response_data["error"] == "stats_error"
            assert "Could not retrieve session statistics" in response_data["message"]
