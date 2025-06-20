"""
Test file for Prompts API.

Comprehensive test coverage for all prompts API endpoints.
"""

import pytest
import json
import uuid
import os
from unittest.mock import Mock, AsyncMock, patch, PropertyMock
import azure.functions as func
from api.prompts import (
    main,
    handle_get_prompts,
    handle_create_prompt,
    handle_update_prompt,
    handle_delete_prompt,
)


@pytest.fixture
def mock_request():
    """Create a mock HTTP request."""
    mock_req = Mock(spec=func.HttpRequest)
    mock_req.method = "GET"
    mock_req.url = "https://localhost:7071/api/prompts"
    mock_req.params = {}
    mock_req.headers = {"Authorization": "Bearer test-token"}
    mock_req.get_json.return_value = {}
    mock_req.route_params = {}
    return mock_req


@pytest.fixture
def sample_prompt_data():
    """Sample prompt data for testing."""
    return {
        "name": "Test Prompt",
        "description": "A test prompt template",
        "promptText": "Hello, {{name}}! How can I help you with {{topic}}?",
        "variables": [
            {"name": "name", "type": "string", "required": True},
            {"name": "topic", "type": "string", "required": False},
        ],
        "tags": ["test", "demo"],
        "category": "general",
    }


@pytest.fixture
def valid_user_id():
    """Generate a valid UUID for testing."""
    return str(uuid.uuid4())


@patch("api.prompts.require_auth", lambda resource, action: lambda func: func)
@patch("api.shared.auth.AuthManager.kv_client", new_callable=PropertyMock)
@patch.dict("os.environ", {"ENVIRONMENT": "test"})
class TestPromptsAPI:
    """Test class for prompts API endpoints."""

    @pytest.mark.asyncio
    async def test_main_get_request(self, mock_kv_client, mock_request):
        """Test main endpoint with GET request."""
        mock_kv_client.return_value = Mock()

        with patch("api.prompts.handle_get_prompts") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            response = await main(mock_request)

            assert response.status_code == 200
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_post_request(self, mock_kv_client, mock_request):
        """Test main endpoint with POST request."""
        mock_kv_client.return_value = Mock()
        mock_request.method = "POST"

        with patch("api.prompts.handle_create_prompt") as mock_create:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_create.return_value = mock_response

            response = await main(mock_request)

            assert response.status_code == 201
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_put_request(self, mock_kv_client, mock_request):
        """Test main endpoint with PUT request."""
        mock_kv_client.return_value = Mock()
        mock_request.method = "PUT"

        with patch("api.prompts.handle_update_prompt") as mock_update:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_update.return_value = mock_response

            response = await main(mock_request)

            assert response.status_code == 200
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_delete_request(self, mock_kv_client, mock_request):
        """Test main endpoint with DELETE request."""
        mock_kv_client.return_value = Mock()
        mock_request.method = "DELETE"

        with patch("api.prompts.handle_delete_prompt") as mock_delete:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_delete.return_value = mock_response

            response = await main(mock_request)

            assert response.status_code == 200
            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_method_not_allowed(self, mock_kv_client, mock_request):
        """Test main endpoint with unsupported method."""
        mock_kv_client.return_value = Mock()
        mock_request.method = "PATCH"

        response = await main(mock_request)

        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("api.prompts.get_current_user")
    @patch("api.prompts.get_database_manager")
    async def test_handle_get_prompts_success(
        self, mock_get_db_manager, mock_get_user, mock_request, valid_user_id
    ):
        """Test successful retrieval of prompts."""
        mock_get_user.return_value = {"id": valid_user_id, "role": "user"}

        # Mock database
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container

        # Mock prompt data
        mock_prompts = [
            {
                "id": str(uuid.uuid4()),
                "name": "Test Prompt",
                "description": "A test prompt",
                "promptText": "Hello {{name}}",
                "userId": valid_user_id,
                "status": "active",
            }
        ]
        mock_container.query_items.return_value = mock_prompts

        response = await handle_get_prompts(mock_request)

        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert "prompts" in response_data

    @pytest.mark.asyncio
    @patch("api.prompts.get_current_user")
    @patch("api.prompts.get_database_manager")
    @patch("api.prompts.PromptTemplateValidator")
    async def test_handle_create_prompt_success(
        self,
        mock_validator,
        mock_get_db_manager,
        mock_get_user,
        mock_request,
        sample_prompt_data,
        valid_user_id,
    ):
        """Test successful creation of prompt."""
        mock_request.get_json.return_value = sample_prompt_data
        mock_get_user.return_value = {"id": valid_user_id, "role": "user"}

        # Mock validator
        mock_validator_instance = Mock()
        mock_validator.return_value = mock_validator_instance
        mock_validator_instance.validate.return_value = True

        # Mock database
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container
        mock_container.create_item.return_value = {"id": str(uuid.uuid4())}

        response = await handle_create_prompt(mock_request)

        assert response.status_code == 201
        response_data = json.loads(response.get_body())
        assert "prompt" in response_data

    @pytest.mark.asyncio
    @patch("api.prompts.get_current_user")
    async def test_handle_create_prompt_invalid_json(
        self, mock_get_user, mock_request, valid_user_id
    ):
        """Test creation with invalid JSON."""
        mock_request.get_json.side_effect = ValueError("Invalid JSON")
        mock_get_user.return_value = {"id": valid_user_id, "role": "user"}

        response = await handle_create_prompt(mock_request)

        assert response.status_code == 400

    @pytest.mark.asyncio
    @patch("api.prompts.get_current_user")
    @patch("api.prompts.get_database_manager")
    async def test_handle_update_prompt_success(
        self,
        mock_get_db_manager,
        mock_get_user,
        mock_request,
        sample_prompt_data,
        valid_user_id,
    ):
        """Test successful prompt update."""
        prompt_id = str(uuid.uuid4())
        mock_request.route_params = {"prompt_id": prompt_id}
        mock_request.get_json.return_value = sample_prompt_data
        mock_get_user.return_value = {"id": valid_user_id, "role": "user"}

        # Mock database
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container

        # Mock existing prompt
        existing_prompt = {
            "id": prompt_id,
            "name": "Old Name",
            "userId": valid_user_id,
            "status": "active",
        }
        mock_container.read_item.return_value = existing_prompt
        mock_container.replace_item.return_value = existing_prompt

        response = await handle_update_prompt(mock_request)

        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert "prompt" in response_data

    @pytest.mark.asyncio
    @patch("api.prompts.get_current_user")
    @patch("api.prompts.get_database_manager")
    async def test_handle_update_prompt_not_found(
        self,
        mock_get_db_manager,
        mock_get_user,
        mock_request,
        sample_prompt_data,
        valid_user_id,
    ):
        """Test update of non-existent prompt."""
        prompt_id = str(uuid.uuid4())
        mock_request.route_params = {"prompt_id": prompt_id}
        mock_request.get_json.return_value = sample_prompt_data
        mock_get_user.return_value = {"id": valid_user_id, "role": "user"}

        # Mock database
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container

        # Mock prompt not found
        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        mock_container.read_item.side_effect = CosmosResourceNotFoundError(
            message="Not found"
        )

        response = await handle_update_prompt(mock_request)

        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("api.prompts.get_current_user")
    @patch("api.prompts.get_database_manager")
    async def test_handle_delete_prompt_success(
        self, mock_get_db_manager, mock_get_user, mock_request, valid_user_id
    ):
        """Test successful prompt deletion."""
        prompt_id = str(uuid.uuid4())
        mock_request.route_params = {"prompt_id": prompt_id}
        mock_get_user.return_value = {"id": valid_user_id, "role": "user"}

        # Mock database
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container

        # Mock existing prompt
        existing_prompt = {
            "id": prompt_id,
            "name": "Test Prompt",
            "userId": valid_user_id,
            "status": "active",
        }
        mock_container.read_item.return_value = existing_prompt
        mock_container.delete_item.return_value = None

        response = await handle_delete_prompt(mock_request)

        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert "message" in response_data

    @pytest.mark.asyncio
    @patch("api.prompts.get_current_user")
    @patch("api.prompts.get_database_manager")
    async def test_handle_delete_prompt_not_found(
        self, mock_get_db_manager, mock_get_user, mock_request, valid_user_id
    ):
        """Test deletion of non-existent prompt."""
        prompt_id = str(uuid.uuid4())
        mock_request.route_params = {"prompt_id": prompt_id}
        mock_get_user.return_value = {"id": valid_user_id, "role": "user"}

        # Mock database
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager
        mock_container = Mock()
        mock_db_manager.get_container.return_value = mock_container

        # Mock prompt not found
        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        mock_container.read_item.side_effect = CosmosResourceNotFoundError(
            message="Not found"
        )

        response = await handle_delete_prompt(mock_request)

        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("api.prompts.get_current_user")
    @patch("api.prompts.validate_pagination_params")
    async def test_handle_get_prompts_with_pagination(
        self, mock_validate_pagination, mock_get_user, mock_request, valid_user_id
    ):
        """Test prompts retrieval with pagination."""
        mock_request.params = {"page": "2", "limit": "10"}
        mock_get_user.return_value = {"id": valid_user_id, "role": "user"}
        mock_validate_pagination.return_value = {"page": 2, "limit": 10, "offset": 10}

        with patch("api.prompts.get_database_manager") as mock_get_db_manager:
            # Mock database
            mock_db_manager = Mock()
            mock_get_db_manager.return_value = mock_db_manager
            mock_container = Mock()
            mock_db_manager.get_container.return_value = mock_container
            mock_container.query_items.return_value = []

            response = await handle_get_prompts(mock_request)

            assert response.status_code == 200
            mock_validate_pagination.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_exception_handling(self, mock_request):
        """Test main endpoint exception handling."""
        with patch("api.prompts.handle_get_prompts") as mock_get:
            mock_get.side_effect = Exception("Test exception")

            response = await main(mock_request)

            # The error should be handled by the @handle_api_errors decorator
            assert response.status_code >= 400
