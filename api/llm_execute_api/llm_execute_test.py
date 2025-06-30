"""
Test file for LLM Execute API.

Comprehensive test coverage for LLM execution and comparison endpoints.
"""

import pytest
import json
import uuid
from unittest.mock import Mock, AsyncMock, patch
import azure.functions as func
from ..conftest import create_auth_request
from . import main as llm_execute_main
from . import (
    execute_llm_prompt,
    compare_llm_outputs,
    get_available_providers,
)


@pytest.fixture
def mock_request():
    """Create a mock HTTP request."""
    mock_req = Mock(spec=func.HttpRequest)
    mock_req.method = "POST"
    mock_req.url = "https://localhost:7071/api/llm/execute"
    mock_req.params = {}
    mock_req.headers = {"Authorization": "Bearer test-token"}
    mock_req.get_json.return_value = {}
    mock_req.route_params = {}
    return mock_req


@pytest.fixture
def sample_execute_data():
    """Sample LLM execution data for testing."""
    return {
        "promptText": "Hello, {{name}}! How are you?",
        "variables": {"name": "World"},
        "llms": ["openai", "anthropic"],
        "temperature": 0.7,
        "maxTokens": 1000,
    }


@pytest.fixture
def valid_user_id():
    """Generate a valid UUID for testing."""
    return str(uuid.uuid4())


class TestLLMExecuteAPI:
    """Test class for LLM execute API endpoints."""

    @pytest.mark.asyncio
    async def test_main_post_compare(self, valid_user_id, auth_test_user):
        """Test main endpoint with POST request for compare."""
        mock_request = create_auth_request(method="POST")
        mock_request.url = "https://localhost:7071/api/llm/compare"

        with patch("llm_execute_api.compare_llm_outputs") as mock_compare:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_compare.return_value = mock_response

            response = await llm_execute_main(mock_request)

            assert response.status_code == 200
            mock_compare.assert_called_once_with(valid_user_id, mock_request)

    @pytest.mark.asyncio
    async def test_main_get_providers(self, valid_user_id, auth_test_user):
        """Test main endpoint with GET request for providers."""
        mock_request = create_auth_request(method="GET")

        with patch("llm_execute_api.get_available_providers") as mock_providers:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_providers.return_value = mock_response

            response = await llm_execute_main(mock_request)

            assert response.status_code == 200
            mock_providers.assert_called_once_with(valid_user_id)

    @pytest.mark.asyncio
    async def test_main_method_not_allowed(self, valid_user_id, auth_test_user):
        """Test main endpoint with unsupported method."""
        mock_request = create_auth_request(method="PATCH")

        response = await llm_execute_main(mock_request)

        assert response.status_code == 405
        response_data = json.loads(response.get_body())
        assert "error" in response_data

    @pytest.mark.asyncio
    @patch("llm_execute_api.get_database_manager")
    @patch("llm_execute_api.get_llm_client")
    async def test_execute_llm_prompt_success(
        self,
        mock_get_llm_client,
        mock_get_db_manager,
        sample_execute_data,
        valid_user_id,
        auth_test_user,
    ):
        """Test successful LLM prompt execution."""
        mock_request = create_auth_request(
            body=sample_execute_data, user_id=valid_user_id
        )

        # Mock database
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container

        # Mock user data with API keys
        mock_user_data = [
            {
                "id": valid_user_id,
                "llmApiKeys": {"openai": "key-ref-1", "anthropic": "key-ref-2"},
            }
        ]
        mock_container.query_items.return_value = mock_user_data

        # Mock LLM client
        mock_llm_client = Mock()
        mock_get_llm_client.return_value = mock_llm_client
        mock_llm_client.execute_prompt = AsyncMock(
            return_value={
                "response": "Hello, World! I'm doing great!",
                "usage": {"input_tokens": 10, "output_tokens": 15},
                "model": "gpt-4",
            }
        )

        response = await execute_llm_prompt(valid_user_id, mock_request)

        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert "llmOutputs" in response_data

    @pytest.mark.asyncio
    async def test_execute_llm_prompt_invalid_json(self, valid_user_id, auth_test_user):
        """Test execution with invalid JSON."""
        mock_request = create_auth_request(user_id=valid_user_id)
        mock_request.get_json.side_effect = ValueError("Invalid JSON")

        response = await execute_llm_prompt(valid_user_id, mock_request)

        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert "error" in response_data

    @pytest.mark.asyncio
    async def test_execute_llm_prompt_missing_prompt(
        self, valid_user_id, auth_test_user
    ):
        """Test execution with missing prompt text."""
        mock_request = create_auth_request(
            body={"llms": ["openai"]}, user_id=valid_user_id
        )

        response = await execute_llm_prompt(valid_user_id, mock_request)

        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert "promptText is required" in response_data["error"]

    @pytest.mark.asyncio
    @patch("llm_execute_api.get_database_manager")
    async def test_execute_llm_prompt_user_not_found(
        self, mock_get_db_manager, sample_execute_data, valid_user_id, auth_test_user
    ):
        """Test execution when user not found."""
        mock_request = create_auth_request(
            body=sample_execute_data, user_id=valid_user_id
        )

        # Mock database
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container
        mock_container.query_items.return_value = []

        response = await execute_llm_prompt(valid_user_id, mock_request)

        assert response.status_code == 404
        response_data = json.loads(response.get_body())
        assert "User not found" in response_data["error"]

    @pytest.mark.asyncio
    @patch("llm_execute_api.get_database_manager")
    async def test_compare_llm_outputs_success(
        self, mock_get_db_manager, valid_user_id, auth_test_user
    ):
        """Test successful LLM output comparison."""
        compare_data = {
            "outputs": {
                "openai": {"text": "Response 1", "metrics": {"tokens": 10}},
                "anthropic": {"text": "Response 2", "metrics": {"tokens": 12}},
            },
            "criteria": ["accuracy", "relevance", "creativity"],
        }
        mock_request = create_auth_request(body=compare_data, user_id=valid_user_id)

        # Mock database
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container

        # Mock user data
        mock_user_data = [{"id": valid_user_id, "llmApiKeys": {"openai": "key-ref"}}]
        mock_container.query_items.return_value = mock_user_data

        response = await compare_llm_outputs(valid_user_id, mock_request)

        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert "comparison" in response_data

    @pytest.mark.asyncio
    async def test_compare_llm_outputs_invalid_json(
        self, valid_user_id, auth_test_user
    ):
        """Test comparison with invalid JSON."""
        mock_request = create_auth_request(user_id=valid_user_id)
        mock_request.get_json.side_effect = ValueError("Invalid JSON")

        response = await compare_llm_outputs(valid_user_id, mock_request)

        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert "error" in response_data

    @pytest.mark.asyncio
    @patch("llm_execute_api.get_provider_models")
    @patch("llm_execute_api.get_database_manager")
    async def test_get_available_providers_success(
        self, mock_get_db_manager, mock_get_provider_models, valid_user_id
    ):
        """Test getting available providers."""
        # Mock provider models function
        mock_get_provider_models.return_value = ["model1", "model2"]

        # Mock database
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_users_container = Mock()
        mock_system_container = Mock()

        def get_container_side_effect(container_name):
            if container_name == "Users":
                return mock_users_container
            elif container_name == "SystemConfig":
                return mock_system_container

        mock_db_manager.get_container.side_effect = get_container_side_effect

        # Mock user data with API keys
        mock_user_data = [
            {
                "id": valid_user_id,
                "llmApiKeys": {"openai": "key-ref-1", "anthropic": "key-ref-2"},
            }
        ]
        mock_users_container.query_items.return_value = mock_user_data

        # Mock system config with proper priority values
        mock_system_config = {
            "providers": {
                "openai": {"enabled": True, "priority": 1, "rateLimits": {}},
                "google_gemini": {"enabled": True, "priority": 2, "rateLimits": {}},
                "anthropic": {"enabled": True, "priority": 3, "rateLimits": {}},
            }
        }
        mock_system_container.read_item.return_value = mock_system_config

        response = await get_available_providers(valid_user_id)

        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert "providers" in response_data
        assert len(response_data["providers"]) > 0

    @pytest.mark.asyncio
    @patch("llm_execute_api.get_provider_models")
    @patch("llm_execute_api.get_database_manager")
    async def test_get_available_providers_user_not_found(
        self, mock_get_db_manager, mock_get_provider_models, valid_user_id
    ):
        """Test getting providers when user not found (should still return providers)."""
        # Mock provider models function
        mock_get_provider_models.return_value = ["model1", "model2"]

        # Mock database
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_users_container = Mock()
        mock_system_container = Mock()

        def get_container_side_effect(container_name):
            if container_name == "Users":
                return mock_users_container
            elif container_name == "SystemConfig":
                return mock_system_container

        mock_db_manager.get_container.side_effect = get_container_side_effect
        mock_users_container.query_items.return_value = []

        # Mock system config
        mock_system_config = {
            "providers": {
                "openai": {"enabled": True, "priority": 1, "rateLimits": {}},
                "google_gemini": {"enabled": True, "priority": 2, "rateLimits": {}},
                "anthropic": {"enabled": True, "priority": 3, "rateLimits": {}},
            }
        }
        mock_system_container.read_item.return_value = mock_system_config

        response = await get_available_providers(valid_user_id)

        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert "providers" in response_data
        # When user not found, providers should still be available but not configured
        assert response_data["totalConfigured"] == 0
        assert len(response_data["providers"]) == 3

    @pytest.mark.asyncio
    async def test_main_exception_handling(self, auth_test_user):
        """Test main endpoint exception handling."""
        mock_request = create_auth_request(user_id="test-user-123")

        # Simulate an exception in the main logic
        with patch("llm_execute_api.execute_llm_prompt") as mock_execute:
            mock_execute.side_effect = Exception("Test exception")

            response = await llm_execute_main(mock_request)

            assert response.status_code == 500
            response_data = json.loads(response.get_body())
            assert "error" in response_data
