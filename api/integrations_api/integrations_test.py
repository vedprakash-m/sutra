"""
Test file for integrations API.

Comprehensive test coverage for all integrations API endpoints.
"""

import pytest
import json
import uuid
from unittest.mock import Mock, AsyncMock, patch
import azure.functions as func
from api.integrations_api import (
    main,
    list_llm_integrations,
    create_llm_integration,
    update_llm_integration,
    delete_llm_integration,
    validate_llm_connection,
)


@pytest.fixture
def mock_request():
    """Create a mock HTTP request."""
    mock_req = Mock(spec=func.HttpRequest)
    mock_req.method = "GET"
    mock_req.url = "https://localhost:7071/api/integrations"
    mock_req.params = {}
    mock_req.headers = {"Authorization": "Bearer test-token"}
    mock_req.get_json.return_value = {}
    mock_req.route_params = {}
    return mock_req


@pytest.fixture
def sample_integration_data():
    """Sample LLM integration data for testing."""
    return {
        "apiKey": "test_key_123",
        "provider": "openai",
        "url": "https://api.openai.com/v1",
    }


@pytest.fixture
def valid_user_id():
    """Generate a valid UUID for testing."""
    return str(uuid.uuid4())


class TestIntegrationsAPI:
    """Test class for integrations API endpoints."""

    def create_auth_request(self, method="GET", body=None, route_params=None, params=None,
                           user_id="test-user-123", role="user", url="http://localhost/api/integrations"):
        """Helper to create authenticated requests for Azure Static Web Apps."""
        import azure.functions as func
        import base64
        import json

        # Create user principal data
        principal_data = {
            "identityProvider": "azureActiveDirectory",
            "userId": user_id,
            "userDetails": "Test User",
            "userRoles": [role],
            "claims": []
        }

        # Encode as base64
        principal_b64 = base64.b64encode(json.dumps(principal_data).encode('utf-8')).decode('utf-8')

        # Create headers
        headers = {
            "x-ms-client-principal": principal_b64,
            "x-ms-client-principal-id": user_id,
            "x-ms-client-principal-name": "Test User",
            "x-ms-client-principal-idp": "azureActiveDirectory"
        }

        return func.HttpRequest(
            method=method,
            url=url,
            body=json.dumps(body).encode('utf-8') if body else b"",
            headers=headers,
            route_params=route_params or {},
            params=params or {}
        )

    @pytest.mark.asyncio
    async def test_main_unauthorized(self, mock_request):
        """Test main endpoint without authorization."""
        mock_request.headers = {}

        # Set flag to simulate authentication failure
        mock_request._test_auth_fail = True

        response = await main(mock_request)

        assert response.status_code == 401
        response_data = json.loads(response.get_body())
        assert "error" in response_data

    @pytest.mark.asyncio
    async def test_main_get_request(self, mock_request, valid_user_id):
        """Test main endpoint with GET request."""
        # Set the user ID for testing mode
        mock_request._test_user_id = valid_user_id

        with patch(
            "api.integrations_api.list_llm_integrations"
        ) as mock_list:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_list.return_value = mock_response

            response = await main(mock_request)

            assert response.status_code == 200
            mock_list.assert_called_once_with(valid_user_id)

    @pytest.mark.asyncio
    async def test_main_post_request(self, mock_request, valid_user_id):
        """Test main endpoint with POST request."""
        mock_request.method = "POST"
        # Set the user ID for testing mode
        mock_request._test_user_id = valid_user_id

        with patch(
            "api.integrations_api.create_llm_integration"
        ) as mock_create:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_create.return_value = mock_response

            response = await main(mock_request)

            assert response.status_code == 201
            mock_create.assert_called_once_with(valid_user_id, mock_request)

    @pytest.mark.asyncio
    async def test_main_post_test_connection(self, mock_request, valid_user_id):
        """Test main endpoint with POST request for test connection."""
        mock_request.method = "POST"
        mock_request.route_params = {"provider": "openai", "action": "test"}
        # Set the user ID for testing mode
        mock_request._test_user_id = valid_user_id

        with patch(
            "api.integrations_api.validate_llm_connection"
        ) as mock_test:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_test.return_value = mock_response

            response = await main(mock_request)

            assert response.status_code == 200
            mock_test.assert_called_once_with(valid_user_id, "openai", mock_request)

    @pytest.mark.asyncio
    async def test_main_put_request(self, mock_request, valid_user_id):
        """Test main endpoint with PUT request."""
        mock_request.method = "PUT"
        mock_request.route_params = {"provider": "openai"}
        # Set the user ID for testing mode
        mock_request._test_user_id = valid_user_id

        with patch(
            "api.integrations_api.update_llm_integration"
        ) as mock_update:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_update.return_value = mock_response

            response = await main(mock_request)

            assert response.status_code == 200
            mock_update.assert_called_once_with(valid_user_id, "openai", mock_request)

    @pytest.mark.asyncio
    async def test_main_delete_request(self, mock_request, valid_user_id):
        """Test main endpoint with DELETE request."""
        mock_request.method = "DELETE"
        mock_request.route_params = {"provider": "openai"}
        # Set the user ID for testing mode
        mock_request._test_user_id = valid_user_id

        with patch(
            "api.integrations_api.delete_llm_integration"
        ) as mock_delete:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_delete.return_value = mock_response

            response = await main(mock_request)

            assert response.status_code == 200
            mock_delete.assert_called_once_with(valid_user_id, "openai")

    @pytest.mark.asyncio
    async def test_main_method_not_allowed(self, mock_request, valid_user_id):
        """Test main endpoint with unsupported method."""
        mock_request.method = "PATCH"

        with patch("api.integrations_api.verify_jwt_token") as mock_auth, patch(
            "api.integrations_api.get_user_id_from_token"
        ) as mock_get_user:
            mock_auth.return_value = {"valid": True}
            mock_get_user.return_value = valid_user_id

            response = await main(mock_request)

            assert response.status_code == 405
            response_data = json.loads(response.get_body())
            assert "error" in response_data

    @pytest.mark.asyncio
    @patch("api.integrations_api.get_database_manager")
    async def test_list_llm_integrations_success(
        self, mock_get_db_manager, valid_user_id
    ):
        """Test successful listing of LLM integrations."""
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager

        # Mock user data with integrations - note the correct structure
        mock_user_data = [
            {
                "id": valid_user_id,
                "llmApiKeys": {
                    "openai": {
                        "keyRef": "kv-ref-openai-12345",
                        "url": "https://api.openai.com/v1",
                        "enabled": True,
                        "lastTested": "2024-01-01T00:00:00Z",
                        "status": "active",
                    },
                    "anthropic": "kv-ref-anthropic-67890",
                },
            }
        ]
        mock_db_manager.query_items = AsyncMock(return_value=mock_user_data)

        response = await list_llm_integrations(valid_user_id)

        assert response.status_code == 200
        response_data = json.loads(response.get_body())

        # Check that integrations are properly returned
        assert "integrations" in response_data
        assert "openai" in response_data["integrations"]
        assert "anthropic" in response_data["integrations"]

        # Check that keyRef is masked
        assert response_data["integrations"]["openai"]["keyRef"] == "***masked***"
        assert response_data["integrations"]["anthropic"]["keyRef"] == "***masked***"

    @pytest.mark.asyncio
    @patch("api.integrations_api.get_database_manager")
    async def test_list_llm_integrations_user_not_found(
        self, mock_get_db_manager, valid_user_id
    ):
        """Test listing integrations when user not found."""
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_db_manager.query_items = AsyncMock(return_value=[])

        response = await list_llm_integrations(valid_user_id)

        assert response.status_code == 404
        response_data = json.loads(response.get_body())
        assert "error" in response_data

    @pytest.mark.asyncio
    @patch("api.integrations_api.validate_llm_api_key")
    @patch("api.integrations_api.get_database_manager")
    @patch("api.integrations_api.validate_llm_integration_data")
    async def test_create_llm_integration_success(
        self,
        mock_validate,
        mock_get_db_manager,
        mock_validate_api_key,
        mock_request,
        sample_integration_data,
        valid_user_id,
    ):
        """Test successful creation of LLM integration."""
        mock_request.get_json.return_value = sample_integration_data
        mock_validate.return_value = {"valid": True, "errors": []}
        mock_validate_api_key.return_value = {"valid": True}

        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager

        # Create a mock container
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container

        # Mock existing user data
        mock_user_data = [{"id": valid_user_id, "llmApiKeys": {}}]
        mock_container.query_items.return_value = mock_user_data
        mock_container.replace_item.return_value = {"id": valid_user_id}

        response = await create_llm_integration(valid_user_id, mock_request)

        assert response.status_code == 201
        response_data = json.loads(response.get_body())
        assert "message" in response_data

    @pytest.mark.asyncio
    @patch("api.integrations_api.get_database_manager")
    @patch("api.integrations_api.validate_llm_integration_data")
    async def test_create_llm_integration_validation_error(
        self, mock_validate, mock_get_db_manager, mock_request, valid_user_id
    ):
        """Test creation with validation error."""
        mock_request.get_json.return_value = {"invalid": "data"}

        # Mock validation error - return proper format
        mock_validate.return_value = {
            "valid": False,
            "errors": ["Provider is required"],
        }

        response = await create_llm_integration(valid_user_id, mock_request)

        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert "error" in response_data

    @pytest.mark.asyncio
    @patch("api.integrations_api.validate_llm_api_key")
    @patch("api.integrations_api.get_database_manager")
    async def test_update_llm_integration_success(
        self,
        mock_get_db_manager,
        mock_validate_api_key,
        mock_request,
        sample_integration_data,
        valid_user_id,
    ):
        """Test successful update of LLM integration."""
        mock_request.get_json.return_value = sample_integration_data
        mock_validate_api_key.return_value = {"valid": True}

        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager

        # Create a mock container
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container

        # Mock existing user data with integration
        mock_user_data = [
            {
                "id": valid_user_id,
                "llmApiKeys": {
                    "openai": {
                        "keyRef": "old_key_ref",
                        "url": "https://api.openai.com/v1",
                    }
                },
            }
        ]
        mock_container.query_items.return_value = mock_user_data
        mock_container.replace_item.return_value = {"id": valid_user_id}

        response = await update_llm_integration(valid_user_id, "openai", mock_request)

        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert "message" in response_data

    @pytest.mark.asyncio
    @patch("api.integrations_api.get_database_manager")
    async def test_delete_llm_integration_success(
        self, mock_get_db_manager, valid_user_id
    ):
        """Test successful deletion of LLM integration."""
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager

        # Create a mock container
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container

        # Mock existing user data with integration
        mock_user_data = [
            {
                "id": valid_user_id,
                "llmApiKeys": {
                    "openai": {
                        "keyRef": "test_key_ref",
                        "url": "https://api.openai.com/v1",
                    }
                },
            }
        ]
        mock_container.query_items.return_value = mock_user_data
        mock_container.replace_item.return_value = {"id": valid_user_id}

        response = await delete_llm_integration(valid_user_id, "openai")

        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert "message" in response_data

    @pytest.mark.asyncio
    @patch("api.integrations_api.get_database_manager")
    async def test_delete_llm_integration_not_found(
        self, mock_get_db_manager, valid_user_id
    ):
        """Test deletion of non-existent LLM integration."""
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager

        # Create a mock container
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container

        # Mock user data without the integration
        mock_user_data = [{"id": valid_user_id, "llmApiKeys": {}}]
        mock_container.query_items.return_value = mock_user_data

        response = await delete_llm_integration(valid_user_id, "nonexistent")

        assert response.status_code == 404
        response_data = json.loads(response.get_body())
        assert "error" in response_data

    @pytest.mark.asyncio
    @patch("api.integrations_api.validate_llm_api_key")
    async def test_test_llm_connection_success(
        self, mock_validate_api_key, mock_request, valid_user_id
    ):
        """Test successful LLM connection test."""
        # Mock request data
        mock_request.get_json.return_value = {
            "apiKey": "test_key_123",
            "url": "https://api.openai.com/v1",
        }

        # Mock successful validation
        mock_validate_api_key.return_value = {
            "valid": True,
            "model": "gpt-4",
            "response_time_ms": 150,
        }

        response = await validate_llm_connection(valid_user_id, "openai", mock_request)

        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["valid"] is True
        assert "message" in response_data

    @pytest.mark.asyncio
    @patch("api.integrations_api.validate_llm_api_key")
    async def test_test_llm_connection_invalid_api_key(
        self, mock_validate_api_key, mock_request, valid_user_id
    ):
        """Test connection test with invalid API key."""
        # Mock request data
        mock_request.get_json.return_value = {
            "apiKey": "invalid_key",
            "url": "https://api.openai.com/v1",
        }

        # Mock validation failure
        mock_validate_api_key.return_value = {
            "valid": False,
            "error": "Invalid API key",
        }

        response = await validate_llm_connection(valid_user_id, "openai", mock_request)

        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert response_data["valid"] is False
        assert "error" in response_data

    @pytest.mark.asyncio
    async def test_main_exception_handling(self):
        """Test main endpoint exception handling."""
        # Create properly authenticated request
        from . import main

        # Create request with authentication
        req = self.create_auth_request(
            method="GET",
            url="http://localhost/api/integrations/llm",
            route_params={},
            user_id="test-user-123",
            role="user"
        )

        # Mock database to raise exception
        with patch("api.integrations_api.get_database_manager") as mock_db:
            mock_db.side_effect = Exception("Database connection failed")

            response = await main(req)

            # The handle_api_error should handle this gracefully
            assert response.status_code == 500
            response_data = json.loads(response.get_body())
            assert "error" in response_data

    # ADDITIONAL TESTS FOR COVERAGE IMPROVEMENT

    @pytest.mark.asyncio
    async def test_validate_llm_api_key_openai_success(self):
        """Test successful OpenAI API key validation."""
        from api.integrations_api import validate_llm_api_key

        # Mock successful OpenAI API response
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": [{"id": "gpt-3.5-turbo"}]}

            mock_context = AsyncMock()
            mock_context.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context

            # Act
            result = await validate_llm_api_key("openai", "sk-test-key")

            # Assert
            assert result["valid"] == True
            assert result["model"] == "gpt-3.5-turbo"
            assert "response_time_ms" in result

    @pytest.mark.asyncio
    async def test_validate_llm_api_key_google_gemini_success(self):
        """Test successful Google Gemini API key validation."""
        from api.integrations_api import validate_llm_api_key

        # Mock successful Google Gemini API response
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200

            mock_context = AsyncMock()
            mock_context.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context

            # Act
            result = await validate_llm_api_key("google_gemini", "test-api-key")

            # Assert
            assert result["valid"] == True
            assert result["model"] == "gemini-1.5-pro"
            assert "response_time_ms" in result

    @pytest.mark.asyncio
    async def test_validate_llm_api_key_anthropic_success(self):
        """Test successful Anthropic API key validation."""
        from api.integrations_api import validate_llm_api_key

        # Mock successful Anthropic API response
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200

            mock_context = AsyncMock()
            mock_context.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context

            # Act
            result = await validate_llm_api_key("anthropic", "test-api-key")

            # Assert
            assert result["valid"] == True
            assert result["model"] == "claude-3-haiku"
            assert "response_time_ms" in result

    @pytest.mark.asyncio
    async def test_validate_llm_api_key_custom_success(self):
        """Test successful custom API validation."""
        from api.integrations_api import validate_llm_api_key

        # Mock successful custom API response
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200

            mock_context = AsyncMock()
            mock_context.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context

            # Act
            result = await validate_llm_api_key("custom", "test-api-key", "https://custom-api.com")

            # Assert
            assert result["valid"] == True
            assert result["model"] == "custom"
            assert "response_time_ms" in result

    @pytest.mark.asyncio
    async def test_validate_llm_api_key_openai_failure(self):
        """Test failed OpenAI API key validation."""
        from api.integrations_api import validate_llm_api_key

        # Mock failed OpenAI API response
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Invalid API key"

            mock_context = AsyncMock()
            mock_context.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context

            # Act
            result = await validate_llm_api_key("openai", "invalid-key")

            # Assert
            assert result["valid"] == False
            assert "OpenAI API error: 401" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_llm_api_key_google_gemini_failure(self):
        """Test failed Google Gemini API key validation."""
        from api.integrations_api import validate_llm_api_key

        # Mock failed Google Gemini API response
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_response.text = "API key invalid"

            mock_context = AsyncMock()
            mock_context.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context

            # Act
            result = await validate_llm_api_key("google_gemini", "invalid-key")

            # Assert
            assert result["valid"] == False
            assert "Google Gemini API error: 403" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_llm_api_key_anthropic_failure(self):
        """Test failed Anthropic API key validation."""
        from api.integrations_api import validate_llm_api_key

        # Mock failed Anthropic API response
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"

            mock_context = AsyncMock()
            mock_context.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_context

            # Act
            result = await validate_llm_api_key("anthropic", "invalid-key")

            # Assert
            assert result["valid"] == False
            assert "Anthropic API error: 401" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_llm_api_key_timeout(self):
        """Test API key validation with timeout."""
        from api.integrations_api import validate_llm_api_key
        import asyncio

        # Mock timeout error
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value.get = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_client.return_value = mock_context

            # Act
            result = await validate_llm_api_key("openai", "test-key")

            # Assert
            assert result["valid"] == False
            assert "Connection timeout" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_llm_api_key_unsupported_provider(self):
        """Test API key validation for unsupported provider."""
        from api.integrations_api import validate_llm_api_key

        # Act
        result = await validate_llm_api_key("unsupported_provider", "test-key")

        # Assert
        assert result["valid"] == False
        assert "Unsupported provider" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_llm_api_key_connection_error(self):
        """Test API key validation with connection error."""
        from api.integrations_api import validate_llm_api_key

        # Mock connection error
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value.get = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client.return_value = mock_context

            # Act
            result = await validate_llm_api_key("openai", "test-key")

            # Assert
            assert result["valid"] == False
            assert "Connection error" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__])
