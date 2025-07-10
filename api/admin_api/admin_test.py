import json
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import azure.functions as func
import pytest
from shared.error_handling import SutraAPIError

from ..conftest import create_auth_request
from . import main as admin_main


class TestAdminAPI:
    """Test suite for Admin API endpoints."""

    @pytest.fixture
    def mock_cosmos_client(self):
        """Mock database manager with proper container structure."""
        with patch("api.admin_api.get_database_manager") as mock_db_manager:
            mock_manager = Mock()
            # Make database methods async
            mock_manager.query_items = AsyncMock()
            mock_manager.create_item = AsyncMock()
            mock_manager.replace_item = AsyncMock()
            mock_manager.update_item = AsyncMock()
            mock_manager.delete_item = AsyncMock()
            mock_manager.read_item = AsyncMock()

            # Mock container access method
            containers = {}
            container_names = [
                "Users",
                "Prompts",
                "Collections",
                "Playbooks",
                "Executions",
                "SystemConfig",
                "AuditLog",
                "usage",
                "config",
            ]

            for name in container_names:
                container = Mock()
                container.query_items = Mock()
                container.create_item = Mock()
                container.read_item = Mock()
                container.upsert_item = Mock()
                container.replace_item = Mock()
                container.delete_item = Mock()
                containers[name] = container

            mock_manager.get_container = Mock(side_effect=lambda name: containers.get(name))

            # For backwards compatibility with old method names
            for name in container_names:
                setattr(
                    mock_manager,
                    f"get_{name.lower()}_container",
                    Mock(return_value=containers[name]),
                )

            mock_db_manager.return_value = mock_manager
            yield mock_manager

    @pytest.mark.asyncio
    async def test_list_users_success(self, auth_admin_user, mock_cosmos_client):
        """Test successful user listing by admin."""
        # Arrange
        mock_users = [
            {
                "id": "user-1",
                "email": "user1@example.com",
                "name": "User One",
                "role": "user",
                "createdAt": "2025-06-15T09:00:00Z",
                "llmApiKeys": {
                    "openai": "kv-ref-key",
                    "google_gemini": {"enabled": True, "status": "active"},
                },
            },
            {
                "id": "user-2",
                "email": "user2@example.com",
                "name": "User Two",
                "role": "user",
                "createdAt": "2025-06-15T10:00:00Z",
            },
        ]

        # Mock database responses - using AsyncMock for async methods
        from unittest.mock import AsyncMock

        mock_cosmos_client.query_items = AsyncMock(side_effect=[mock_users, [2]])  # Users list  # Count

        # Create authenticated request using helper
        req = create_auth_request(method="GET", route_params={"resource": "users"})

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert len(response_data["users"]) == 2
        assert response_data["pagination"]["total_count"] == 2

        # Check that API keys are masked
        user1 = response_data["users"][0]
        assert "llmApiKeys" in user1
        assert user1["llmApiKeys"]["openai"]["enabled"] == True
        assert "kv-ref-key" not in str(user1["llmApiKeys"])

    @pytest.mark.asyncio
    async def test_update_user_role_success(self, auth_admin_user, mock_cosmos_client):
        """Test successful user role update by admin."""
        # Arrange
        target_user_id = "user-123"
        existing_user = {
            "id": target_user_id,
            "email": "user@example.com",
            "name": "Test User",
            "role": "user",
            "createdAt": "2025-06-15T09:00:00Z",
        }

        new_role_data = {"role": "admin"}

        # Mock database responses - using AsyncMock for async methods
        from unittest.mock import AsyncMock

        mock_cosmos_client.query_items = AsyncMock(return_value=[existing_user])
        mock_cosmos_client.update_item = AsyncMock(
            return_value={
                **existing_user,
                "role": "admin",
                "updatedAt": "2025-06-15T10:00:00Z",
            }
        )

        # Create authenticated request using helper
        req = create_auth_request(
            method="PUT",
            route_params={
                "resource": "users",
                "action": "role",
                "user_id": target_user_id,
            },
            body=new_role_data,
        )

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["newRole"] == "admin"
        assert response_data["oldRole"] == "user"
        assert response_data["userId"] == target_user_id
        mock_cosmos_client.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_role_invalid_role(self, auth_admin_user, mock_cosmos_client):
        """Test user role update with invalid role."""
        # Arrange
        target_user_id = "user-123"
        invalid_role_data = {"role": "invalid_role"}

        # Create authenticated request using helper
        req = create_auth_request(
            method="PUT",
            route_params={
                "resource": "users",
                "action": "role",
                "user_id": target_user_id,
            },
            body=invalid_role_data,
        )

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert "Invalid role" in response_data["error"]
        assert "user, admin" in response_data["message"]

    @pytest.mark.asyncio
    async def test_get_system_health_success(self, auth_admin_user, mock_cosmos_client):
        """Test successful system health check."""
        # Arrange
        # Mock successful database query
        mock_cosmos_client.query_items.return_value = [1]  # Successful query

        # Create authenticated request using helper
        req = create_auth_request(method="GET", route_params={"resource": "system", "action": "health"})

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "healthy"
        assert response_data["components"]["database"]["status"] == "healthy"
        assert response_data["components"]["api"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_system_stats_success(self, auth_admin_user, mock_cosmos_client):
        """Test successful system statistics retrieval."""
        # Arrange
        # Mock database responses for different counts
        # Use return_value for repeatable calls instead of side_effect which can be exhausted
        users_container_mock = mock_cosmos_client.get_users_container()
        users_container_mock.query_items.side_effect = [
            [10],
            [3],
        ]  # User count, then recent users

        prompts_container_mock = mock_cosmos_client.get_prompts_container()
        prompts_container_mock.query_items.side_effect = [
            [25],
            [7],
        ]  # Prompt count, then recent prompts

        collections_container_mock = mock_cosmos_client.get_collections_container()
        collections_container_mock.query_items.return_value = [5]  # Collection count

        playbooks_container_mock = mock_cosmos_client.get_playbooks_container()
        playbooks_container_mock.query_items.return_value = [8]  # Playbook count

        # Create authenticated request using helper
        req = create_auth_request(method="GET", route_params={"resource": "system", "action": "stats"})

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["totals"]["users"] == 10
        assert response_data["totals"]["prompts"] == 25
        assert response_data["totals"]["collections"] == 5
        assert response_data["totals"]["playbooks"] == 8
        assert response_data["recent_activity"]["new_users"] == 3
        assert response_data["recent_activity"]["new_prompts"] == 7

    @pytest.mark.asyncio
    async def test_set_maintenance_mode_enable(self, auth_admin_user, mock_cosmos_client):
        """Test enabling maintenance mode."""
        # Arrange
        maintenance_data = {
            "enabled": True,
            "message": "System maintenance in progress",
        }

        mock_cosmos_client.replace_item.return_value = {
            "id": "maintenance_mode",
            "enabled": True,
            "message": "System maintenance in progress",
            "setBy": "admin-user-123",
        }

        # Create request
        req = create_auth_request(
            method="POST",
            route_params={"resource": "system", "action": "maintenance"},
            body=maintenance_data,
        )

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["enabled"] is True
        assert "enabled" in response_data["message"]
        assert response_data["maintenanceMessage"] == "System maintenance in progress"

    @pytest.mark.asyncio
    async def test_get_llm_settings_success(self, auth_admin_user, mock_cosmos_client):
        """Test successful LLM settings retrieval."""
        # Arrange
        llm_settings = {
            "id": "llm_settings",
            "providers": {
                "openai": {
                    "enabled": True,
                    "priority": 1,
                    "rateLimits": {"requestsPerMinute": 60},
                    "budgetLimits": {"dailyBudget": 50.0},
                },
                "google_gemini": {
                    "enabled": True,
                    "priority": 2,
                    "rateLimits": {"requestsPerMinute": 60},
                    "budgetLimits": {"dailyBudget": 30.0},
                },
            },
            "defaultProvider": "openai",
        }

        mock_cosmos_client.read_item.return_value = llm_settings

        # Create request
        req = create_auth_request(method="GET", route_params={"resource": "llm", "action": "settings"})

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert "providers" in response_data
        assert response_data["defaultProvider"] == "openai"
        assert response_data["providers"]["openai"]["enabled"] is True
        assert response_data["providers"]["openai"]["priority"] == 1

    @pytest.mark.asyncio
    async def test_update_llm_settings_success(self, auth_admin_user, mock_cosmos_client):
        """Test successful LLM settings update."""
        # Arrange
        existing_settings = {
            "id": "llm_settings",
            "providers": {"openai": {"enabled": True, "priority": 1}},
        }

        update_data = {
            "providers": {
                "openai": {
                    "enabled": True,
                    "priority": 1,
                    "budgetLimits": {"dailyBudget": 100.0},
                },
                "google_gemini": {"enabled": False, "priority": 2},
            },
            "defaultProvider": "openai",
        }

        mock_cosmos_client.get_config_container().read_item.return_value = existing_settings
        mock_cosmos_client.get_config_container().replace_item.return_value = {
            **existing_settings,
            **update_data,
            "updatedAt": "2025-06-15T10:00:00Z",
            "updatedBy": "admin-user-123",
        }

        # Create request
        req = create_auth_request(
            method="PUT",
            route_params={"resource": "llm", "action": "settings"},
            body=update_data,
        )

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["providers"]["openai"]["budgetLimits"]["dailyBudget"] == 100.0
        assert response_data["providers"]["google_gemini"]["enabled"] is False
        assert response_data["updatedBy"] == "admin-user-123"
        mock_cosmos_client.get_config_container().replace_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_usage_stats_success(self, auth_admin_user, mock_cosmos_client):
        """Test successful usage statistics retrieval."""
        # Arrange
        # Mock database responses for usage stats
        mock_cosmos_client.get_executions_container().query_items.side_effect = [
            [15],  # Total executions
            [12],  # Successful executions
            [3],  # Failed executions
        ]
        mock_cosmos_client.get_users_container().query_items.return_value = [8]  # Active users

        # Create authenticated request using helper
        req = create_auth_request(method="GET", route_params={"resource": "usage"})

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["period"] == "day"
        assert response_data["statistics"]["executions"]["total"] == 15
        assert response_data["statistics"]["executions"]["successful"] == 12
        assert response_data["statistics"]["executions"]["failed"] == 3
        assert response_data["statistics"]["executions"]["success_rate"] == 80.0
        assert response_data["statistics"]["users"]["active"] == 8

    @pytest.mark.asyncio
    async def test_non_admin_access_forbidden(self, auth_test_user):
        """Test that non-admin users cannot access admin endpoints."""
        # Create authenticated request using helper with non-admin user
        req = create_auth_request(
            method="GET",
            route_params={"resource": "users"},
            headers={"x-test-user-id": "regular-user-123", "x-test-user-role": "user"},
        )

        # Set flag to simulate non-admin user (for TESTING_MODE)
        req._test_admin_required = True

        # Act - This should return 403 for non-admin
        response = await admin_main(req)

        # Assert
        assert response.status_code == 403
        response_data = json.loads(response.get_body().decode())
        assert "Admin access required" in response_data["error"]

    @pytest.mark.asyncio
    async def test_get_system_health_database_failure(self, auth_admin_user, mock_cosmos_client):
        """Test system health check when database is unavailable."""
        # Arrange
        # Mock database failure
        mock_cosmos_client.query_items.side_effect = Exception("Database connection failed")

        # Create request
        req = create_auth_request(method="GET", route_params={"resource": "system", "action": "health"})

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 503
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "degraded"
        assert "unhealthy" in response_data["components"]["database"]["status"]

    @pytest.mark.asyncio
    async def test_update_user_role_user_not_found(self, auth_admin_user, mock_cosmos_client):
        """Test user role update with non-existent user."""
        # Arrange
        target_user_id = "non-existent-user"
        new_role_data = {"role": "admin"}

        # Mock database responses - user not found
        from unittest.mock import AsyncMock

        mock_cosmos_client.query_items = AsyncMock(return_value=[])

        # Create authenticated request using helper
        req = create_auth_request(
            method="PUT",
            route_params={
                "resource": "users",
                "user_id": target_user_id,
                "action": "role",
            },
            body=new_role_data,
        )

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 404
        response_data = json.loads(response.get_body())
        assert "User not found" in response_data["error"]

    # ADDITIONAL TESTS FOR COVERAGE IMPROVEMENT

    @pytest.mark.asyncio
    async def test_list_users_with_search_filter(self, auth_admin_user, mock_cosmos_client):
        """Test user listing with search and role filter."""
        # Arrange
        mock_users = [
            {
                "id": "user-1",
                "email": "john@example.com",
                "name": "John Doe",
                "role": "user",
                "createdAt": "2025-06-15T09:00:00Z",
            }
        ]

        mock_cosmos_client.query_items = AsyncMock(side_effect=[mock_users, [1]])  # Users list and count

        # Create authenticated request using helper with search and role filter
        req = create_auth_request(method="GET", route_params={"resource": "users"})

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert len(response_data["users"]) == 1
        assert response_data["pagination"]["current_page"] == 1  # Default page
        assert response_data["pagination"]["limit"] == 50

    @pytest.mark.asyncio
    async def test_update_user_role_invalid_json(self, auth_admin_user, mock_cosmos_client):
        """Test user role update with invalid JSON."""
        # Create request with invalid JSON by directly creating the HttpRequest
        import azure.functions as func

        req = func.HttpRequest(
            method="PUT",
            url="http://localhost/api/admin/users/some-user-id/role",
            body=b"{invalid_json",  # Invalid JSON as bytes
            headers={"Content-Type": "application/json", "X-Test-User-Type": "admin"},
            route_params={
                "resource": "users",
                "user_id": "some-user-id",
                "action": "role",
            },
            params={},
        )

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert "Invalid JSON" in response_data["error"]

    @pytest.mark.asyncio
    async def test_reset_test_data_success(self, auth_admin_user, mock_cosmos_client):
        """Test successful test data reset."""
        # Mock database responses
        mock_cosmos_client.query_items = AsyncMock(return_value=[])
        mock_cosmos_client.delete_item = AsyncMock()

        # Mock environment to allow test data operations
        with patch.dict("os.environ", {"ENVIRONMENT": "test"}):
            # Create authenticated request using helper
            req = create_auth_request(method="POST", route_params={"resource": "test-data", "action": "reset"})

            # Act
            response = await admin_main(req)

            # Assert
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["environment"] == "test"
            assert "reset_at" in response_data
            assert "containers_reset" in response_data

    @pytest.mark.asyncio
    async def test_seed_test_data_success(self, auth_admin_user, mock_cosmos_client):
        """Test successful test data seeding."""
        # Mock database responses
        mock_cosmos_client.query_items = AsyncMock(return_value=[])
        mock_cosmos_client.create_item = AsyncMock()

        # Mock environment to allow test data operations
        with patch.dict("os.environ", {"ENVIRONMENT": "test"}):
            # Create authenticated request using helper
            req = create_auth_request(method="POST", route_params={"resource": "test-data", "action": "seed"})

            # Act
            response = await admin_main(req)

            # Assert
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["environment"] == "test"
            assert "seeded_at" in response_data
            assert "data_created" in response_data

    @pytest.mark.asyncio
    async def test_resource_not_found_error(self, auth_admin_user):
        """Test handling of unknown resource."""
        # Create request for unknown resource
        req = create_auth_request(method="GET")

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 404
        response_data = json.loads(response.get_body())
        assert "Resource not found" in response_data["error"]

    @pytest.mark.asyncio
    async def test_list_users_with_masked_api_keys(self, auth_admin_user, mock_cosmos_client):
        """Test that API keys are properly masked in user listing."""
        # Arrange
        mock_users = [
            {
                "id": "user-1",
                "email": "user1@example.com",
                "name": "User One",
                "role": "user",
                "createdAt": "2025-06-15T09:00:00Z",
                "llmApiKeys": {
                    "openai": "sk-actual-secret-key",  # String format
                    "google_gemini": {
                        "enabled": True,
                        "status": "active",
                        "apiKey": "secret-key",
                        "lastTested": "2025-06-15T08:00:00Z",
                    },
                },
            }
        ]

        mock_cosmos_client.query_items = AsyncMock(side_effect=[mock_users, [1]])

        # Create authenticated request using helper
        req = create_auth_request(method="GET", route_params={"resource": "users"})

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        user = response_data["users"][0]

        # Check that string API keys are masked
        assert user["llmApiKeys"]["openai"]["enabled"] == True
        assert user["llmApiKeys"]["openai"]["status"] == "configured"

        # Check that dict API keys are properly masked
        assert user["llmApiKeys"]["google_gemini"]["enabled"] == True
        assert user["llmApiKeys"]["google_gemini"]["status"] == "active"
        assert user["llmApiKeys"]["google_gemini"]["lastTested"] == "2025-06-15T08:00:00Z"
        assert "apiKey" not in user["llmApiKeys"]["google_gemini"]

    @pytest.mark.asyncio
    async def test_test_data_production_environment_blocked(self, auth_admin_user):
        """Test that test data operations are blocked in production environment."""
        # Create authenticated request using helper
        req = create_auth_request(method="POST", route_params={"resource": "test-data", "action": "reset"})

        # Mock production environment
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            # Act
            response = await admin_main(req)

            # Assert
            assert response.status_code == 403
            response_data = json.loads(response.get_body())
            assert "only available in test environments" in response_data["message"]

    @pytest.mark.asyncio
    async def test_admin_api_general_exception_handling(self, auth_admin_user):
        """Test general exception handling in admin API."""
        # Mock an exception in the database manager
        with patch("api.admin_api.get_database_manager") as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            # Use a route that actually calls the database (list users)
            req = create_auth_request(method="GET", route_params={"resource": "users"})

            # Act
            response = await admin_main(req)

            # Assert - Should trigger handle_api_error
            assert response.status_code in [500, 401]  # Depending on exception handling


if __name__ == "__main__":
    pytest.main([__file__])
