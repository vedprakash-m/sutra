"""
Tests for Guest API - Fixed version with proper mocking
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

# Import after setting path
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

    @pytest.mark.asyncio
    async def test_get_or_create_session_new(self):
        """Test creating a new guest session when none exists."""
        mock_session = {
            "id": "guest_123456789",
            "type": "guest_session",
            "ip_address": "127.0.0.1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "active": True
        }

        mock_stats = {
            "usage": {"llm_calls": 0, "prompts_created": 0},
            "limits": {"llm_calls_per_day": 5, "prompts_per_day": 10},
            "remaining": {"llm_calls": 5, "prompts_created": 10}
        }

        with patch('guest_api.get_database_manager') as mock_db, \
             patch('guest_api.GuestUserManager') as mock_manager_class, \
             patch('guest_api.get_guest_usage_stats') as mock_usage_stats:

            # Set up mocks
            mock_db.return_value = Mock()
            mock_manager = Mock()
            mock_manager.get_guest_session = AsyncMock(return_value=None)
            mock_manager.create_guest_session = AsyncMock(return_value=mock_session)
            mock_manager_class.return_value = mock_manager
            mock_usage_stats.return_value = mock_stats

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
            mock_manager.create_guest_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_existing_guest_session(self):
        """Test retrieving an existing guest session."""
        session_id = "guest_987654321"
        mock_session = {
            "id": session_id,
            "type": "guest_session",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat(),
            "active": True
        }

        mock_stats = {
            "usage": {"llm_calls": 2, "prompts_created": 1},
            "limits": {"llm_calls_per_day": 5, "prompts_per_day": 10},
            "remaining": {"llm_calls": 3, "prompts_created": 9}
        }

        with patch('guest_api.get_database_manager') as mock_db, \
             patch('guest_api.GuestUserManager') as mock_manager_class, \
             patch('guest_api.get_guest_usage_stats') as mock_usage_stats:

            # Set up mocks
            mock_db.return_value = Mock()
            mock_manager = Mock()
            mock_manager.get_guest_session = AsyncMock(return_value=mock_session)
            mock_manager.create_guest_session = AsyncMock()
            mock_manager_class.return_value = mock_manager
            mock_usage_stats.return_value = mock_stats

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
            mock_manager.get_guest_session.assert_called_once_with(session_id)
            # Should not create a new session since we found an existing one
            mock_manager.create_guest_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_expired_session_creates_new(self):
        """Test handling of expired guest session - should create new one."""
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

        mock_stats = {
            "usage": {"llm_calls": 0, "prompts_created": 0},
            "limits": {"llm_calls_per_day": 5, "prompts_per_day": 10},
            "remaining": {"llm_calls": 5, "prompts_created": 10}
        }

        with patch('guest_api.get_database_manager') as mock_db, \
             patch('guest_api.GuestUserManager') as mock_manager_class, \
             patch('guest_api.get_guest_usage_stats') as mock_usage_stats:

            # Set up mocks
            mock_db.return_value = Mock()
            mock_manager = Mock()
            mock_manager.get_guest_session = AsyncMock(return_value=expired_session)
            mock_manager.create_guest_session = AsyncMock(return_value=new_session)
            mock_manager_class.return_value = mock_manager
            mock_usage_stats.return_value = mock_stats

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
            mock_manager.create_guest_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_stats(self):
        """Test retrieving detailed session stats."""
        session_id = "guest_stats_test"
        mock_stats = {
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

        with patch('guest_api.get_database_manager') as mock_db, \
             patch('guest_api.get_guest_usage_stats') as mock_usage_stats:

            mock_db.return_value = Mock()
            mock_usage_stats.return_value = mock_stats

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
            mock_usage_stats.assert_called_once_with(session_id, mock_db.return_value)

    @pytest.mark.asyncio
    async def test_get_session_stats_not_found(self):
        """Test retrieving stats for nonexistent session."""
        session_id = "guest_nonexistent"
        mock_stats = {
            "error": "session_not_found",
            "message": "Guest session not found"
        }

        with patch('guest_api.get_database_manager') as mock_db, \
             patch('guest_api.get_guest_usage_stats') as mock_usage_stats:

            mock_db.return_value = Mock()
            mock_usage_stats.return_value = mock_stats

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
    async def test_method_not_allowed(self):
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
    async def test_session_creation_error_handling(self):
        """Test error handling during session creation."""
        with patch('guest_api.get_database_manager') as mock_db, \
             patch('guest_api.GuestUserManager') as mock_manager_class:

            # Set up mocks
            mock_db.return_value = Mock()
            mock_manager = Mock()
            mock_manager.get_guest_session = AsyncMock(return_value=None)
            mock_manager.create_guest_session = AsyncMock(side_effect=Exception("Database error"))
            mock_manager_class.return_value = mock_manager

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
    async def test_stats_error_handling(self):
        """Test error handling when getting session stats."""
        session_id = "guest_error_test"

        with patch('guest_api.get_database_manager') as mock_db, \
             patch('guest_api.get_guest_usage_stats') as mock_usage_stats:

            mock_db.return_value = Mock()
            mock_usage_stats.side_effect = Exception("Stats calculation error")

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
