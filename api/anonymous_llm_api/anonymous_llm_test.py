import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import azure.functions as func
import pytest

from ..conftest import create_auth_request
from . import main as anonymous_llm_main


class TestAnonymousLLMAPI:
    """Test suite for Anonymous LLM API endpoints."""

    def create_anonymous_request(
        self,
        method="GET",
        body=None,
        route_params=None,
        params=None,
        url="http://localhost/api/anonymous/llm",
        ip_address="127.0.0.1",
    ):
        """Helper to create anonymous requests."""
        headers = {"x-forwarded-for": ip_address, "user-agent": "test-browser/1.0"}
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

    @pytest.mark.asyncio
    async def test_anonymous_llm_execute_success(self):
        """Test successful anonymous LLM execution."""
        # Arrange
        prompt_data = {"prompt": "What is artificial intelligence?"}

        # Create anonymous request
        req = self.create_anonymous_request(
            method="POST",
            url="http://localhost/api/anonymous/llm/execute",
            body=prompt_data,
            route_params={"action": "execute"},
            ip_address="192.168.1.100",
        )

        # Act
        response = await anonymous_llm_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["user_type"] == "anonymous"
        assert response_data["model"] == "gpt-3.5-turbo"
        assert "choices" in response_data
        assert "anonymous_info" in response_data
        assert response_data["anonymous_info"]["remaining_calls"] == 4  # 5 - 1
        assert response_data["anonymous_info"]["daily_limit"] == 5

    @pytest.mark.asyncio
    async def test_anonymous_llm_prompt_too_long(self):
        """Test anonymous LLM with prompt exceeding length limit."""
        # Arrange
        long_prompt = "x" * 501  # Exceeds 500 character limit
        prompt_data = {"prompt": long_prompt}

        # Create anonymous request
        req = self.create_anonymous_request(
            method="POST",
            url="http://localhost/api/anonymous/llm/execute",
            body=prompt_data,
            route_params={"action": "execute"},
        )

        # Act
        response = await anonymous_llm_main(req)

        # Assert
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert response_data["error"] == "prompt_too_long"
        assert response_data["max_length"] == 500
        assert response_data["current_length"] == 501

    @pytest.mark.asyncio
    async def test_anonymous_llm_rate_limit_exceeded(self):
        """Test rate limiting for anonymous users."""
        # Arrange
        prompt_data = {"prompt": "Test prompt"}
        ip_address = "192.168.1.200"

        # Simulate user having already made 5 calls
        with patch(
            "api.anonymous_llm_api.ip_usage",
            {ip_address: {"calls": 5, "date": "2025-06-25"}},
        ):
            req = self.create_anonymous_request(
                method="POST",
                url="http://localhost/api/anonymous/llm/execute",
                body=prompt_data,
                route_params={"action": "execute"},
                ip_address=ip_address,
            )

            # Act
            response = await anonymous_llm_main(req)

            # Assert
            assert response.status_code == 429
            response_data = json.loads(response.get_body())
            assert response_data["error"] == "daily_limit_exceeded"
            assert response_data["daily_limit"] == 5
            assert response_data["calls_used"] == 5
            assert response_data["remaining"] == 0

    @pytest.mark.asyncio
    async def test_anonymous_llm_invalid_json(self):
        """Test anonymous LLM with invalid JSON."""
        # Create request with invalid JSON body
        req = func.HttpRequest(
            method="POST",
            url="http://localhost/api/anonymous/llm/execute",
            body=b"invalid json",
            headers={
                "Content-Type": "application/json",
                "x-forwarded-for": "127.0.0.1",
            },
            route_params={"action": "execute"},
            params={},
        )

        # Act
        response = await anonymous_llm_main(req)

        # Assert
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert response_data["error"] == "Invalid JSON in request body"

    @pytest.mark.asyncio
    async def test_anonymous_llm_missing_prompt(self):
        """Test anonymous LLM with missing prompt."""
        # Arrange
        prompt_data = {"model": "gpt-3.5-turbo"}  # Has other fields but no prompt field

        req = self.create_anonymous_request(
            method="POST",
            url="http://localhost/api/anonymous/llm/execute",
            body=prompt_data,
            route_params={"action": "execute"},
        )

        # Act
        response = await anonymous_llm_main(req)

        # Assert
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert response_data["error"] == "Prompt is required"

    @pytest.mark.asyncio
    async def test_list_anonymous_models(self):
        """Test listing available models for anonymous users."""
        # Arrange
        req = self.create_anonymous_request(
            method="GET",
            url="http://localhost/api/anonymous/llm/models",
            route_params={"action": "models"},
        )

        # Act
        response = await anonymous_llm_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["user_type"] == "anonymous"
        assert len(response_data["models"]) == 1
        assert response_data["models"][0]["id"] == "gpt-3.5-turbo"
        assert response_data["models"][0]["available_for_anonymous"] is True
        assert response_data["limitations"]["max_prompt_length"] == 500
        assert response_data["limitations"]["calls_per_day"] == 5

    @pytest.mark.asyncio
    async def test_get_anonymous_usage_new_ip(self):
        """Test getting usage for new IP address."""
        # Arrange
        req = self.create_anonymous_request(
            method="GET",
            url="http://localhost/api/anonymous/llm/usage",
            route_params={"action": "usage"},
            ip_address="192.168.1.300",
        )

        # Act
        response = await anonymous_llm_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["session_type"] == "anonymous"
        assert response_data["ip_based"] is True
        assert response_data["current_usage"]["llm_calls"] == 0
        assert response_data["remaining"]["llm_calls"] == 5
        assert response_data["daily_limits"]["llm_calls"] == 5

    @pytest.mark.asyncio
    async def test_get_anonymous_usage_existing_ip(self):
        """Test getting usage for existing IP with some calls made."""
        # Arrange
        ip_address = "192.168.1.400"

        # Pre-populate usage data
        with patch(
            "api.anonymous_llm_api.ip_usage",
            {ip_address: {"calls": 3, "date": "2025-06-25"}},
        ):
            req = self.create_anonymous_request(
                method="GET",
                url="http://localhost/api/anonymous/llm/usage",
                route_params={"action": "usage"},
                ip_address=ip_address,
            )

            # Act
            response = await anonymous_llm_main(req)

            # Assert
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["current_usage"]["llm_calls"] == 3
            assert response_data["remaining"]["llm_calls"] == 2
            assert "upgrade_benefits" in response_data

    @pytest.mark.asyncio
    async def test_method_not_allowed(self):
        """Test unsupported HTTP method."""
        # Arrange
        req = self.create_anonymous_request(method="PATCH", url="http://localhost/api/anonymous/llm")  # Not supported

        # Act
        response = await anonymous_llm_main(req)

        # Assert
        assert response.status_code == 405
        response_data = json.loads(response.get_body())
        assert "Method not allowed" in response_data["error"]

    @pytest.mark.asyncio
    async def test_admin_configured_limits(self):
        """Test that admin-configured limits are respected."""
        # Mock admin configuration with custom limits
        with patch("api.anonymous_llm_api.get_admin_configured_limits") as mock_limits:
            mock_limits.return_value = {"llm_calls_per_day": 10}  # Custom limit

            prompt_data = {"prompt": "Test with custom limits"}
            req = self.create_anonymous_request(
                method="POST",
                url="http://localhost/api/anonymous/llm/execute",
                body=prompt_data,
                route_params={"action": "execute"},
                ip_address="192.168.1.500",
            )

            # Act
            response = await anonymous_llm_main(req)

            # Assert
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["anonymous_info"]["daily_limit"] == 10
            assert response_data["anonymous_info"]["remaining_calls"] == 9

    @pytest.mark.asyncio
    async def test_multiple_calls_same_ip(self):
        """Test multiple calls from same IP to verify usage tracking."""
        # Arrange
        ip_address = "192.168.1.600"
        prompt_data = {"prompt": "Sequential test"}

        # Clear any existing usage for this IP
        with patch("api.anonymous_llm_api.ip_usage", {}):
            # First call
            req1 = self.create_anonymous_request(
                method="POST",
                url="http://localhost/api/anonymous/llm/execute",
                body=prompt_data,
                route_params={"action": "execute"},
                ip_address=ip_address,
            )

            response1 = await anonymous_llm_main(req1)
            assert response1.status_code == 200
            data1 = json.loads(response1.get_body())
            assert data1["anonymous_info"]["remaining_calls"] == 4

            # Second call
            req2 = self.create_anonymous_request(
                method="POST",
                url="http://localhost/api/anonymous/llm/execute",
                body=prompt_data,
                route_params={"action": "execute"},
                ip_address=ip_address,
            )

            response2 = await anonymous_llm_main(req2)
            assert response2.status_code == 200
            data2 = json.loads(response2.get_body())
            assert data2["anonymous_info"]["remaining_calls"] == 3

    @pytest.mark.asyncio
    async def test_different_ips_separate_limits(self):
        """Test that different IPs have separate rate limits."""
        # Arrange
        prompt_data = {"prompt": "IP separation test"}

        with patch("api.anonymous_llm_api.ip_usage", {}):
            # First IP
            req1 = self.create_anonymous_request(
                method="POST",
                url="http://localhost/api/anonymous/llm/execute",
                body=prompt_data,
                route_params={"action": "execute"},
                ip_address="192.168.1.700",
            )

            response1 = await anonymous_llm_main(req1)
            data1 = json.loads(response1.get_body())
            assert data1["anonymous_info"]["remaining_calls"] == 4

            # Different IP should have full limit
            req2 = self.create_anonymous_request(
                method="POST",
                url="http://localhost/api/anonymous/llm/execute",
                body=prompt_data,
                route_params={"action": "execute"},
                ip_address="192.168.1.800",
            )

            response2 = await anonymous_llm_main(req2)
            data2 = json.loads(response2.get_body())
            assert data2["anonymous_info"]["remaining_calls"] == 4  # Full limit for new IP


if __name__ == "__main__":
    pytest.main([__file__])
