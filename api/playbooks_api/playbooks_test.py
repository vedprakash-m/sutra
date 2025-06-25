import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

import azure.functions as func
from api.playbooks_api import main as playbooks_main


class TestPlaybooksAPI:
    """Test suite for Playbooks API endpoints."""

    @pytest.fixture
    def mock_auth_success(self):
        """Mock successful authentication."""
        with patch("api.playbooks_api.verify_jwt_token") as mock_verify, patch(
            "api.playbooks_api.get_user_id_from_token"
        ) as mock_user_id:
            mock_verify.return_value = {"valid": True}
            mock_user_id.return_value = "test-user-123"
            yield

    @pytest.fixture
    def mock_cosmos_client(self):
        """Mock database manager."""
        with patch("api.playbooks_api.get_database_manager") as mock_db_manager:
            mock_manager = Mock()
            # Make database methods async
            mock_manager.query_items = AsyncMock()
            mock_manager.create_item = AsyncMock()
            mock_manager.replace_item = AsyncMock()
            mock_manager.update_item = AsyncMock()
            mock_manager.delete_item = AsyncMock()
            mock_manager.read_item = AsyncMock()

            # Mock separate container instances for each container type
            playbooks_container = Mock()
            playbooks_container.query_items = Mock()
            playbooks_container.read_item = Mock()
            playbooks_container.replace_item = Mock()
            playbooks_container.create_item = Mock()

            executions_container = Mock()
            executions_container.query_items = Mock()
            executions_container.read_item = Mock()
            executions_container.replace_item = Mock()
            executions_container.create_item = Mock()

            mock_manager.get_playbooks_container = Mock(
                return_value=playbooks_container
            )
            mock_manager.get_executions_container = Mock(
                return_value=executions_container
            )

            mock_db_manager.return_value = mock_manager
            yield mock_manager

    @pytest.mark.asyncio
    async def test_create_playbook_success(self, mock_auth_success, mock_cosmos_client):
        """Test successful playbook creation."""
        # Arrange
        playbook_data = {
            "name": "Test Playbook",
            "description": "A test playbook for automation",
            "visibility": "private",
            "initialInputVariables": {
                "customer_name": {
                    "type": "string",
                    "label": "Customer Name",
                    "required": True,
                }
            },
            "steps": [
                {
                    "stepId": "step1",
                    "type": "prompt",
                    "promptText": "Hello {{customer_name}}",
                    "config": {"llm": "gpt-4", "temperature": 0.7},
                }
            ],
        }

        mock_cosmos_client.create_item.return_value = {
            "id": "test-playbook-id",
            **playbook_data,
            "creatorId": "test-user-123",
            "createdAt": "2025-06-15T10:00:00Z",
            "updatedAt": "2025-06-15T10:00:00Z",
        }

        # Mock validation
        with patch("api.shared.validation.validate_playbook_data") as mock_validate:
            mock_validate.return_value = {"valid": True, "errors": []}

            # Create request
            req = func.HttpRequest(
                method="POST",
                url="http://localhost/api/playbooks",
                body=json.dumps(playbook_data).encode(),
                headers={"Content-Type": "application/json"},
                route_params={},
            )

            # Act
            response = await playbooks_main(req)

            # Assert
            assert response.status_code == 201
            response_data = json.loads(response.get_body())
            assert response_data["name"] == "Test Playbook"
            assert response_data["creatorId"] == "test-user-123"
            assert len(response_data["steps"]) == 1
            mock_cosmos_client.create_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_playbooks_success(self, mock_auth_success, mock_cosmos_client):
        """Test successful playbook listing."""
        # Arrange
        mock_playbooks = [
            {
                "id": "playbook-1",
                "name": "Playbook 1",
                "creatorId": "test-user-123",
                "visibility": "private",
                "createdAt": "2025-06-15T09:00:00Z",
            },
            {
                "id": "playbook-2",
                "name": "Playbook 2",
                "creatorId": "test-user-123",
                "visibility": "shared",
                "createdAt": "2025-06-15T10:00:00Z",
            },
        ]

        # Mock database responses
        mock_cosmos_client.query_items.side_effect = [
            mock_playbooks,  # First call for items
            [2],  # Second call for count
        ]

        # Create request
        req = self.create_auth_request(
            method="GET",
            url="http://localhost/api/playbooks?page=1&limit=20",
            route_params={},
            params={"page": "1", "limit": "20"},
            user_id="test-user-123",
            role="user"
        )

        # Act
        response = await playbooks_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert len(response_data["playbooks"]) == 2
        assert response_data["pagination"]["total_count"] == 2

    @pytest.mark.asyncio
    async def test_run_playbook_success(self, mock_auth_success, mock_cosmos_client):
        """Test successful playbook execution."""
        # Arrange
        playbook_id = "test-playbook-123"
        playbook = {
            "id": playbook_id,
            "name": "Test Playbook",
            "creatorId": "test-user-123",
            "initialInputVariables": {
                "customer_name": {"type": "string", "required": True}
            },
            "steps": [
                {
                    "stepId": "step1",
                    "type": "prompt",
                    "promptText": "Hello {{customer_name}}",
                }
            ],
        }

        execution_input = {"initialInputs": {"customer_name": "John Doe"}}

        # Mock database responses
        mock_cosmos_client.get_playbooks_container().query_items.return_value = [
            playbook
        ]
        mock_cosmos_client.get_executions_container().create_item.return_value = {
            "id": "execution-123",
            "playbookId": playbook_id,
            "userId": "test-user-123",
            "status": "running",
            "initialInputs": execution_input["initialInputs"],
        }

        # Mock async execution
        with patch("asyncio.create_task") as mock_task:
            # Create request
            req = func.HttpRequest(
                method="POST",
                url=f"http://localhost/api/playbooks/{playbook_id}/run",
                body=json.dumps(execution_input).encode(),
                headers={"Content-Type": "application/json"},
                route_params={"id": playbook_id},
            )

            # Act
            response = await playbooks_main(req)

            # Assert
            assert response.status_code == 202
            response_data = json.loads(response.get_body())
            assert response_data["status"] == "running"
            assert "executionId" in response_data
            mock_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_playbook_missing_inputs(
        self, mock_auth_success, mock_cosmos_client
    ):
        """Test playbook execution with missing required inputs."""
        # Arrange
        playbook_id = "test-playbook-123"
        playbook = {
            "id": playbook_id,
            "name": "Test Playbook",
            "creatorId": "test-user-123",
            "initialInputVariables": {
                "customer_name": {"type": "string", "required": True},
                "product_name": {"type": "string", "required": True},
            },
        }

        execution_input = {
            "initialInputs": {
                "customer_name": "John Doe"
                # Missing required product_name
            }
        }

        mock_cosmos_client.get_playbooks_container().query_items.return_value = [
            playbook
        ]

        # Create request
        req = func.HttpRequest(
            method="POST",
            url=f"http://localhost/api/playbooks/{playbook_id}/run",
            body=json.dumps(execution_input).encode(),
            headers={"Content-Type": "application/json"},
            route_params={"id": playbook_id},
        )

        # Act
        response = await playbooks_main(req)

        # Assert
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert "Missing required input" in response_data["error"]
        assert "product_name" in response_data["message"]

    @pytest.mark.asyncio
    async def test_get_execution_status_success(
        self, mock_auth_success, mock_cosmos_client
    ):
        """Test successful execution status retrieval."""
        # Arrange
        execution_id = "execution-123"
        execution = {
            "id": execution_id,
            "playbookId": "playbook-123",
            "userId": "test-user-123",
            "status": "completed",
            "startTime": "2025-06-15T10:00:00Z",
            "endTime": "2025-06-15T10:05:00Z",
            "stepLogs": [
                {
                    "stepId": "step1",
                    "status": "completed",
                    "outputPreview": {"text": "Generated output", "llm": "gpt-4"},
                }
            ],
        }

        mock_cosmos_client.get_executions_container().query_items.return_value = [
            execution
        ]

        # Create request - simulating executions route
        req = func.HttpRequest(
            method="GET",
            url=f"http://localhost/api/playbooks/executions/{execution_id}",
            body=b"",
            headers={},
            route_params={"execution_id": execution_id},
        )

        # Act
        response = await playbooks_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["id"] == execution_id
        assert response_data["status"] == "completed"
        assert len(response_data["stepLogs"]) == 1

    @pytest.mark.asyncio
    async def test_continue_execution_success(
        self, mock_auth_success, mock_cosmos_client
    ):
        """Test successful execution continuation after manual review."""
        # Arrange
        execution_id = "execution-123"
        execution = {
            "id": execution_id,
            "playbookId": "playbook-123",
            "userId": "test-user-123",
            "status": "paused_for_review",
            "stepLogs": [
                {
                    "stepId": "step1",
                    "status": "paused",
                    "outputPreview": {"text": "Generated output"},
                }
            ],
            "auditTrail": [],
        }

        playbook = {"id": "playbook-123", "steps": []}

        continue_data = {"editedOutput": "Manual edited output"}

        # Mock database responses
        mock_cosmos_client.get_executions_container().query_items.side_effect = [
            [execution],  # Get execution
        ]
        mock_cosmos_client.get_playbooks_container().query_items.return_value = [
            playbook
        ]  # Get playbook for resumption
        mock_cosmos_client.get_executions_container().replace_item.return_value = (
            execution
        )

        # Mock async resumption
        with patch(
            "asyncio.create_task"
        ) as mock_task:  # Create request - simulating continue route
            req = func.HttpRequest(
                method="POST",
                url=f"http://localhost/api/playbooks/executions/{execution_id}/continue",
                body=json.dumps(continue_data).encode(),
                headers={"Content-Type": "application/json"},
                route_params={"execution_id": execution_id},
            )

            # Act
            response = await playbooks_main(req)

            # Assert
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["status"] == "running"
            assert "continued" in response_data["message"].lower()
            mock_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_continue_execution_invalid_status(
        self, mock_auth_success, mock_cosmos_client
    ):
        """Test execution continuation with invalid status."""
        # Arrange
        execution_id = "execution-123"
        execution = {
            "id": execution_id,
            "playbookId": "playbook-123",
            "userId": "test-user-123",
            "status": "completed",  # Not paused for review
            "stepLogs": [],
            "auditTrail": [],
        }

        mock_cosmos_client.get_executions_container().query_items.return_value = [
            execution
        ]

        # Create request
        req = func.HttpRequest(
            method="POST",
            url=f"http://localhost/api/playbooks/executions/{execution_id}/continue",
            body=json.dumps({}).encode(),
            headers={"Content-Type": "application/json"},
            route_params={"execution_id": execution_id},
        )

        # Act
        response = await playbooks_main(req)

        # Assert
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert "Invalid status" in response_data["error"]
        assert "not paused for review" in response_data["message"]

    @pytest.mark.asyncio
    async def test_delete_playbook_with_active_executions(
        self, mock_auth_success, mock_cosmos_client
    ):
        """Test playbook deletion when there are active executions."""
        # Arrange
        playbook_id = "test-playbook-123"
        playbook = {
            "id": playbook_id,
            "name": "Test Playbook",
            "creatorId": "test-user-123",
        }

        # Mock database responses
        mock_cosmos_client.get_playbooks_container().query_items.side_effect = [
            [playbook],  # Playbook exists
        ]
        mock_cosmos_client.get_executions_container().query_items.return_value = [
            2
        ]  # 2 active executions

        # Create request
        req = func.HttpRequest(
            method="DELETE",
            url=f"http://localhost/api/playbooks/{playbook_id}",
            body=b"",
            headers={},
            route_params={"id": playbook_id},
        )

        # Act
        response = await playbooks_main(req)

        # Assert
        assert response.status_code == 409
        response_data = json.loads(response.get_body())
        assert "Cannot delete playbook" in response_data["error"]
        assert "2 active executions" in response_data["message"]
        mock_cosmos_client.delete_item.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_playbook_success(self, mock_auth_success, mock_cosmos_client):
        """Test successful playbook update."""
        # Arrange
        playbook_id = "test-playbook-123"
        existing_playbook = {
            "id": playbook_id,
            "name": "Old Name",
            "creatorId": "test-user-123",
            "visibility": "private",
            "steps": [],
            "createdAt": "2025-06-15T09:00:00Z",
            "updatedAt": "2025-06-15T09:00:00Z",
        }

        update_data = {
            "name": "Updated Playbook Name",
            "description": "Updated description",
            "steps": [
                {
                    "stepId": "new_step",
                    "type": "prompt",
                    "promptText": "New step content",
                }
            ],
        }

        mock_cosmos_client.get_playbooks_container().query_items.return_value = [
            existing_playbook
        ]
        mock_cosmos_client.get_playbooks_container().replace_item.return_value = {
            **existing_playbook,
            **update_data,
            "updatedAt": "2025-06-15T10:00:00Z",
        }

        # Mock validation
        with patch("api.shared.validation.validate_playbook_data") as mock_validate:
            mock_validate.return_value = {"valid": True, "errors": []}

            # Create request
            req = func.HttpRequest(
                method="PUT",
                url=f"http://localhost/api/playbooks/{playbook_id}",
                body=json.dumps(update_data).encode(),
                headers={"Content-Type": "application/json"},
                route_params={"id": playbook_id},
            )

            # Act
            response = await playbooks_main(req)

            # Assert
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["name"] == "Updated Playbook Name"
            assert response_data["description"] == "Updated description"
            assert len(response_data["steps"]) == 1
            mock_cosmos_client.get_playbooks_container().replace_item.assert_called_once()

    # ADDITIONAL TESTS FOR COVERAGE IMPROVEMENT

    @pytest.mark.asyncio
    async def test_get_playbook_success(self, mock_auth_success, mock_cosmos_client):
        """Test successful playbook retrieval."""
        # Arrange
        playbook_id = "test-playbook-123"
        playbook = {
            "id": playbook_id,
            "name": "Test Playbook",
            "creatorId": "test-user-123",
            "description": "A test playbook",
            "steps": [{"stepId": "step1", "type": "prompt"}],
        }

        mock_cosmos_client.get_playbooks_container().query_items.return_value = [
            playbook
        ]

        # Create request
        req = func.HttpRequest(
            method="GET",
            url=f"http://localhost/api/playbooks/{playbook_id}",
            body=b"",
            headers={},
            route_params={"id": playbook_id},
        )

        # Act
        response = await playbooks_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["id"] == playbook_id
        assert response_data["name"] == "Test Playbook"
        assert len(response_data["steps"]) == 1

    @pytest.mark.asyncio
    async def test_get_playbook_not_found(self, mock_auth_success, mock_cosmos_client):
        """Test playbook retrieval when playbook doesn't exist."""
        # Arrange
        playbook_id = "non-existent-playbook"

        mock_cosmos_client.get_playbooks_container().query_items.return_value = []

        # Create request
        req = func.HttpRequest(
            method="GET",
            url=f"http://localhost/api/playbooks/{playbook_id}",
            body=b"",
            headers={},
            route_params={"id": playbook_id},
        )

        # Act
        response = await playbooks_main(req)

        # Assert
        assert response.status_code == 404
        response_data = json.loads(response.get_body())
        assert "Playbook not found" in response_data["error"]

    @pytest.mark.asyncio
    async def test_delete_playbook_success(self, mock_auth_success, mock_cosmos_client):
        """Test successful playbook deletion."""
        # Arrange
        playbook_id = "test-playbook-123"
        playbook = {
            "id": playbook_id,
            "name": "Test Playbook",
            "creatorId": "test-user-123",
        }

        # Mock database responses
        mock_cosmos_client.get_playbooks_container().query_items.return_value = [
            playbook
        ]
        mock_cosmos_client.get_executions_container().query_items.return_value = [
            0
        ]  # No active executions

        # Create request
        req = func.HttpRequest(
            method="DELETE",
            url=f"http://localhost/api/playbooks/{playbook_id}",
            body=b"",
            headers={},
            route_params={"id": playbook_id},
        )

        # Act
        response = await playbooks_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert "deleted successfully" in response_data["message"]
        mock_cosmos_client.get_playbooks_container().delete_item.assert_called_once_with(
            item=playbook_id, partition_key=playbook_id
        )

    @pytest.mark.asyncio
    async def test_delete_playbook_not_found(self, mock_auth_success, mock_cosmos_client):
        """Test playbook deletion when playbook doesn't exist."""
        # Arrange
        playbook_id = "non-existent-playbook"

        mock_cosmos_client.get_playbooks_container().query_items.return_value = []

        # Create request
        req = func.HttpRequest(
            method="DELETE",
            url=f"http://localhost/api/playbooks/{playbook_id}",
            body=b"",
            headers={},
            route_params={"id": playbook_id},
        )

        # Act
        response = await playbooks_main(req)

        # Assert
        assert response.status_code == 404
        response_data = json.loads(response.get_body())
        assert "Playbook not found" in response_data["error"]

    @pytest.mark.asyncio
    async def test_update_playbook_not_found(self, mock_auth_success, mock_cosmos_client):
        """Test playbook update when playbook doesn't exist."""
        # Arrange
        playbook_id = "non-existent-playbook"
        update_data = {"name": "Updated Name"}

        mock_cosmos_client.get_playbooks_container().query_items.return_value = []

        # Create request
        req = func.HttpRequest(
            method="PUT",
            url=f"http://localhost/api/playbooks/{playbook_id}",
            body=json.dumps(update_data).encode(),
            headers={"Content-Type": "application/json"},
            route_params={"id": playbook_id},
        )

        # Act
        response = await playbooks_main(req)

        # Assert
        assert response.status_code == 404
        response_data = json.loads(response.get_body())
        assert "Playbook not found" in response_data["error"]

    @pytest.mark.asyncio
    async def test_update_playbook_invalid_json(self, mock_auth_success, mock_cosmos_client):
        """Test playbook update with invalid JSON."""
        # Arrange
        playbook_id = "test-playbook-123"

        # Create request with invalid JSON
        req = func.HttpRequest(
            method="PUT",
            url=f"http://localhost/api/playbooks/{playbook_id}",
            body=b"{invalid json}",
            headers={"Content-Type": "application/json"},
            route_params={"id": playbook_id},
        )

        # Act
        response = await playbooks_main(req)

        # Assert
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert "Invalid JSON" in response_data["error"]

    @pytest.mark.asyncio
    async def test_update_playbook_validation_error(self, mock_auth_success, mock_cosmos_client):
        """Test playbook update with validation errors."""
        # Arrange
        playbook_id = "test-playbook-123"
        existing_playbook = {
            "id": playbook_id,
            "name": "Old Name",
            "creatorId": "test-user-123",
            "steps": [],
        }

        update_data = {"name": ""}  # Invalid empty name

        mock_cosmos_client.get_playbooks_container().query_items.return_value = [
            existing_playbook
        ]

        # Mock validation failure
        with patch("api.shared.validation.validate_playbook_data") as mock_validate:
            mock_validate.return_value = {
                "valid": False,
                "errors": ["Playbook name is required"],
            }

            # Create request
            req = func.HttpRequest(
                method="PUT",
                url=f"http://localhost/api/playbooks/{playbook_id}",
                body=json.dumps(update_data).encode(),
                headers={"Content-Type": "application/json"},
                route_params={"id": playbook_id},
            )

            # Act
            response = await playbooks_main(req)

            # Assert
            assert response.status_code == 400
            response_data = json.loads(response.get_body())
            assert "Validation failed" in response_data["error"]
            assert len(response_data["details"]) >= 1  # Could be multiple validation errors

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, mock_auth_success):
        """Test unsupported HTTP method."""
        # Create request with unsupported method
        req = func.HttpRequest(
            method="PATCH",  # Not supported
            url="http://localhost/api/playbooks",
            body=b"",
            headers={},
            route_params={},
        )

        # Act
        response = await playbooks_main(req)

        # Assert
        assert response.status_code == 405
        response_data = json.loads(response.get_body())
        assert "Method not allowed" in response_data["error"]

    @pytest.mark.asyncio
    async def test_continue_execution_not_found(self, mock_auth_success, mock_cosmos_client):
        """Test execution continuation when execution doesn't exist."""
        # Arrange
        execution_id = "non-existent-execution"

        mock_cosmos_client.get_executions_container().query_items.return_value = []

        # Create request
        req = func.HttpRequest(
            method="POST",
            url=f"http://localhost/api/playbooks/executions/{execution_id}/continue",
            body=json.dumps({}).encode(),
            headers={"Content-Type": "application/json"},
            route_params={"execution_id": execution_id},
        )

        # Act
        response = await playbooks_main(req)

        # Assert
        assert response.status_code == 404
        response_data = json.loads(response.get_body())
        assert "Execution not found" in response_data["error"]

    @pytest.mark.asyncio
    async def test_get_execution_status_not_found(self, mock_auth_success, mock_cosmos_client):
        """Test execution status retrieval when execution doesn't exist."""
        # Arrange
        execution_id = "non-existent-execution"

        mock_cosmos_client.get_executions_container().query_items.return_value = []

        # Create request
        req = func.HttpRequest(
            method="GET",
            url=f"http://localhost/api/playbooks/executions/{execution_id}",
            body=b"",
            headers={},
            route_params={"execution_id": execution_id},
        )

        # Act
        response = await playbooks_main(req)

        # Assert
        assert response.status_code == 404
        response_data = json.loads(response.get_body())
        assert "Execution not found" in response_data["error"]

    @pytest.mark.asyncio
    async def test_execute_playbook_steps_prompt_step(self):
        """Test execution of playbook with prompt step."""
        from api.playbooks_api import execute_playbook_steps

        # Arrange
        execution_id = "test-execution-123"
        playbook = {
            "id": "playbook-123",
            "steps": [
                {
                    "stepId": "step1",
                    "type": "prompt",
                    "name": "Test Prompt Step",
                    "promptText": "Test prompt",
                    "config": {"llm": "gpt-4"},
                    "variableMappings": {"output_var": "response"},
                }
            ],
        }
        initial_inputs = {"input_var": "test_value"}

        # Mock database operations
        with patch("api.playbooks_api.get_database_manager") as mock_db_manager:
            mock_container = Mock()
            mock_db_manager.return_value.get_container.return_value = mock_container

            # Mock execution data
            mock_execution = {
                "id": execution_id,
                "status": "running",
                "stepLogs": [],
            }
            mock_container.read_item.return_value = mock_execution
            mock_container.replace_item.return_value = mock_execution

            # Act
            await execute_playbook_steps(execution_id, playbook, initial_inputs)

            # Assert
            # Verify database operations were called
            mock_container.read_item.assert_called_with(
                item=execution_id, partition_key=execution_id
            )
            assert mock_container.replace_item.call_count >= 1

    @pytest.mark.asyncio
    async def test_execute_playbook_steps_manual_review_step(self):
        """Test execution of playbook with manual review step."""
        from api.playbooks_api import execute_playbook_steps

        # Arrange
        execution_id = "test-execution-123"
        playbook = {
            "id": "playbook-123",
            "steps": [
                {
                    "stepId": "review_step",
                    "type": "manual_review",
                    "name": "Manual Review Step",
                }
            ],
        }
        initial_inputs = {}

        # Mock database operations
        with patch("api.playbooks_api.get_database_manager") as mock_db_manager:
            mock_container = Mock()
            mock_db_manager.return_value.get_container.return_value = mock_container

            # Mock execution data
            mock_execution = {
                "id": execution_id,
                "status": "running",
                "stepLogs": [],
            }
            mock_container.read_item.return_value = mock_execution
            mock_container.replace_item.return_value = mock_execution

            # Act
            await execute_playbook_steps(execution_id, playbook, initial_inputs)

            # Assert - Should pause for manual review
            # Verify execution was updated to paused status
            update_calls = mock_container.replace_item.call_args_list
            paused_call = None
            for call in update_calls:
                # Check both positional and keyword arguments
                args, kwargs = call
                if 'body' in kwargs:
                    execution_data = kwargs['body']
                elif len(args) >= 2:
                    execution_data = args[1]  # body is second positional argument
                else:
                    continue

                if execution_data.get('status') == 'paused_for_review':
                    paused_call = call
                    break

            assert paused_call is not None, "Execution should be paused for manual review"

    @pytest.mark.asyncio
    async def test_execute_playbook_steps_step_failure(self):
        """Test execution with step failure handling."""
        from api.playbooks_api import execute_playbook_steps

        # Arrange
        execution_id = "test-execution-123"
        playbook = {
            "id": "playbook-123",
            "steps": [
                {
                    "stepId": "failing_step",
                    "type": "prompt",
                    "name": "Failing Step",
                }
            ],
        }
        initial_inputs = {}

        # Mock database operations with failure
        with patch("api.playbooks_api.get_database_manager") as mock_db_manager:
            mock_container = Mock()
            mock_db_manager.return_value.get_container.return_value = mock_container

            # Mock execution data
            mock_execution = {
                "id": execution_id,
                "status": "running",
                "stepLogs": [],
            }
            mock_container.read_item.return_value = mock_execution

            # Mock a failure during step execution by making replace_item raise exception on second call
            call_count = 0
            def side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 2:  # Fail on second update (during step execution)
                    raise Exception("Step execution failed")
                return mock_execution

            mock_container.replace_item.side_effect = side_effect

            # Act
            await execute_playbook_steps(execution_id, playbook, initial_inputs)

            # Assert - Should handle the failure gracefully
            assert mock_container.replace_item.call_count >= 1

    @pytest.mark.asyncio
    async def test_execute_playbook_steps_completion(self):
        """Test execution completion."""
        from api.playbooks_api import execute_playbook_steps

        # Arrange
        execution_id = "test-execution-123"
        playbook = {
            "id": "playbook-123",
            "steps": [
                {
                    "stepId": "final_step",
                    "type": "prompt",
                    "name": "Final Step",
                    "promptText": "Final prompt",
                }
            ],
        }
        initial_inputs = {}

        # Mock database operations
        with patch("api.playbooks_api.get_database_manager") as mock_db_manager:
            mock_container = Mock()
            mock_db_manager.return_value.get_container.return_value = mock_container

            # Mock execution data
            mock_execution = {
                "id": execution_id,
                "status": "running",
                "stepLogs": [],
            }
            mock_container.read_item.return_value = mock_execution
            mock_container.replace_item.return_value = mock_execution

            # Act
            await execute_playbook_steps(execution_id, playbook, initial_inputs)

            # Assert - Should complete execution
            final_call = mock_container.replace_item.call_args_list[-1]
            # Check both positional and keyword arguments
            args, kwargs = final_call
            if 'body' in kwargs:
                final_execution = kwargs['body']
            elif len(args) >= 2:
                final_execution = args[1]  # body is second positional argument
            else:
                # Fallback - check if it's a different call pattern
                final_execution = mock_execution

            assert final_execution['status'] == 'completed'
            assert 'endTime' in final_execution

    @pytest.mark.asyncio
    async def test_resume_playbook_execution(self):
        """Test resuming playbook execution after manual review."""
        from api.playbooks_api import resume_playbook_execution

        # Arrange
        execution_id = "test-execution-123"
        playbook = {
            "id": "playbook-123",
            "steps": [
                {
                    "stepId": "step1",
                    "type": "prompt",
                    "name": "Resume Step",
                }
            ],
        }
        execution = {
            "id": execution_id,
            "status": "paused_for_review",
            "stepLogs": [
                {
                    "stepId": "previous_step",
                    "status": "completed",
                }
            ],
            "initialInputs": {"var": "value"},
        }

        # Mock the execute_playbook_steps function
        with patch("api.playbooks_api.execute_playbook_steps") as mock_execute:
            # Act
            await resume_playbook_execution(execution_id, playbook, execution)

            # Assert
            mock_execute.assert_called_once_with(
                execution_id, playbook, execution["initialInputs"]
            )

    @pytest.mark.asyncio
    async def test_execute_playbook_steps_database_failure_recovery(self):
        """Test execution with database failure and recovery."""
        from api.playbooks_api import execute_playbook_steps

        # Arrange
        execution_id = "test-execution-123"
        playbook = {"id": "playbook-123", "steps": []}
        initial_inputs = {}

        # Mock database failure
        with patch("api.playbooks_api.get_database_manager") as mock_db_manager:
            mock_container = Mock()
            mock_db_manager.return_value.get_container.return_value = mock_container

            # Mock read_item to fail
            mock_container.read_item.side_effect = Exception("Database connection failed")

            # Act - should handle the exception gracefully
            await execute_playbook_steps(execution_id, playbook, initial_inputs)

            # Assert - should attempt to read the execution
            assert mock_container.read_item.call_count >= 1


if __name__ == "__main__":
    pytest.main([__file__])
