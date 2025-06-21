import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

import azure.functions as func
from api.admin_api import main as admin_main


class TestAdminAPI:
    """Test suite for Admin API endpoints."""

    @pytest.fixture
    def mock_admin_auth(self):
        """Mock successful admin authentication."""
        with patch("api.admin_api.verify_jwt_token") as mock_verify, patch(
            "api.admin_api.get_user_id_from_token"
        ) as mock_user_id, patch("api.admin_api.check_admin_role") as mock_admin:
            mock_verify.return_value = {"valid": True}
            mock_user_id.return_value = "admin-user-123"
            mock_admin.return_value = True
            yield

    @pytest.fixture
    def mock_non_admin_auth(self):
        """Mock successful authentication but non-admin user."""
        with patch("api.admin_api.verify_jwt_token") as mock_verify, patch(
            "api.admin_api.get_user_id_from_token"
        ) as mock_user_id, patch("api.admin_api.check_admin_role") as mock_admin:
            mock_verify.return_value = {"valid": True}
            mock_user_id.return_value = "regular-user-123"
            mock_admin.return_value = False
            yield

    @pytest.fixture
    def mock_cosmos_client(self):
        """Mock database manager."""
        with patch("api.admin_api.get_database_manager") as mock_db_manager:
            mock_manager = Mock()
            # Make database methods async
            mock_manager.query_items = AsyncMock()
            mock_manager.create_item = AsyncMock()
            mock_manager.replace_item = AsyncMock()
            mock_manager.update_item = AsyncMock()
            mock_manager.delete_item = AsyncMock()
            mock_manager.read_item = AsyncMock()

            # Mock separate container instances for each container type
            users_container = Mock()
            users_container.query_items = Mock()
            users_container.read_item = Mock()
            users_container.replace_item = Mock()

            prompts_container = Mock()
            prompts_container.query_items = Mock()
            prompts_container.read_item = Mock()
            prompts_container.replace_item = Mock()

            collections_container = Mock()
            collections_container.query_items = Mock()
            collections_container.read_item = Mock()
            collections_container.replace_item = Mock()

            playbooks_container = Mock()
            playbooks_container.query_items = Mock()
            playbooks_container.read_item = Mock()
            playbooks_container.replace_item = Mock()

            config_container = Mock()
            config_container.query_items = Mock()
            config_container.read_item = Mock()  # Sync, not async
            config_container.replace_item = Mock()  # Sync, not async
            config_container.create_item = Mock()  # Sync, not async

            executions_container = Mock()
            executions_container.query_items = Mock()
            executions_container.read_item = Mock()
            executions_container.replace_item = Mock()

            mock_manager.get_users_container = Mock(return_value=users_container)
            mock_manager.get_prompts_container = Mock(return_value=prompts_container)
            mock_manager.get_collections_container = Mock(
                return_value=collections_container
            )
            mock_manager.get_playbooks_container = Mock(
                return_value=playbooks_container
            )
            mock_manager.get_settings_container = Mock(return_value=config_container)
            mock_manager.get_config_container = Mock(return_value=config_container)
            mock_manager.get_executions_container = Mock(
                return_value=executions_container
            )

            mock_db_manager.return_value = mock_manager
            yield mock_manager

    @pytest.mark.asyncio
    async def test_list_users_success(self, mock_admin_auth, mock_cosmos_client):
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

        mock_cosmos_client.query_items = AsyncMock(
            side_effect=[mock_users, [2]]  # Users list  # Count
        )

        # Create request
        req = func.HttpRequest(
            method="GET",
            url="http://localhost/api/admin/users?page=1&limit=50",
            body=b"",
            headers={},
            route_params={"resource": "users"},
            params={"page": "1", "limit": "50"},
        )

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
    async def test_update_user_role_success(self, mock_admin_auth, mock_cosmos_client):
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

        # Create request
        req = func.HttpRequest(
            method="PUT",
            url=f"http://localhost/api/admin/users/{target_user_id}/role",
            body=json.dumps(new_role_data).encode(),
            headers={"Content-Type": "application/json"},
            route_params={
                "resource": "users",
                "user_id": target_user_id,
                "action": "role",
            },
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
    async def test_update_user_role_invalid_role(
        self, mock_admin_auth, mock_cosmos_client
    ):
        """Test user role update with invalid role."""
        # Arrange
        target_user_id = "user-123"
        invalid_role_data = {"role": "invalid_role"}

        # Create request
        req = func.HttpRequest(
            method="PUT",
            url=f"http://localhost/api/admin/users/{target_user_id}/role",
            body=json.dumps(invalid_role_data).encode(),
            headers={"Content-Type": "application/json"},
            route_params={
                "resource": "users",
                "user_id": target_user_id,
                "action": "role",
            },
        )

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert "Invalid role" in response_data["error"]
        assert "user, admin" in response_data["message"]

    @pytest.mark.asyncio
    async def test_get_system_health_success(self, mock_admin_auth, mock_cosmos_client):
        """Test successful system health check."""
        # Arrange
        # Mock successful database query
        mock_cosmos_client.query_items.return_value = [1]  # Successful query

        # Create request
        req = func.HttpRequest(
            method="GET",
            url="http://localhost/api/admin/system/health",
            body=b"",
            headers={},
            route_params={"resource": "system", "action": "health"},
        )

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "healthy"
        assert response_data["components"]["database"]["status"] == "healthy"
        assert response_data["components"]["api"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_system_stats_success(self, mock_admin_auth, mock_cosmos_client):
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

        # Create request
        req = func.HttpRequest(
            method="GET",
            url="http://localhost/api/admin/system/stats",
            body=b"",
            headers={},
            route_params={"resource": "system", "action": "stats"},
        )

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
    async def test_set_maintenance_mode_enable(
        self, mock_admin_auth, mock_cosmos_client
    ):
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
        req = func.HttpRequest(
            method="POST",
            url="http://localhost/api/admin/system/maintenance",
            body=json.dumps(maintenance_data).encode(),
            headers={"Content-Type": "application/json"},
            route_params={"resource": "system", "action": "maintenance"},
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
    async def test_get_llm_settings_success(self, mock_admin_auth, mock_cosmos_client):
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
        req = func.HttpRequest(
            method="GET",
            url="http://localhost/api/admin/llm/settings",
            body=b"",
            headers={},
            route_params={"resource": "llm", "action": "settings"},
        )

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
    async def test_update_llm_settings_success(
        self, mock_admin_auth, mock_cosmos_client
    ):
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

        mock_cosmos_client.get_config_container().read_item.return_value = (
            existing_settings
        )
        mock_cosmos_client.get_config_container().replace_item.return_value = {
            **existing_settings,
            **update_data,
            "updatedAt": "2025-06-15T10:00:00Z",
            "updatedBy": "admin-user-123",
        }

        # Create request
        req = func.HttpRequest(
            method="PUT",
            url="http://localhost/api/admin/llm/settings",
            body=json.dumps(update_data).encode(),
            headers={"Content-Type": "application/json"},
            route_params={"resource": "llm", "action": "settings"},
        )

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert (
            response_data["providers"]["openai"]["budgetLimits"]["dailyBudget"] == 100.0
        )
        assert response_data["providers"]["google_gemini"]["enabled"] is False
        assert response_data["updatedBy"] == "admin-user-123"
        mock_cosmos_client.get_config_container().replace_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_usage_stats_success(self, mock_admin_auth, mock_cosmos_client):
        """Test successful usage statistics retrieval."""
        # Arrange
        # Mock database responses for usage stats
        mock_cosmos_client.get_executions_container().query_items.side_effect = [
            [15],  # Total executions
            [12],  # Successful executions
            [3],  # Failed executions
        ]
        mock_cosmos_client.get_users_container().query_items.return_value = [
            8
        ]  # Active users

        # Create request
        req = func.HttpRequest(
            method="GET",
            url="http://localhost/api/admin/usage?period=day",
            body=b"",
            headers={},
            route_params={"resource": "usage"},
            params={"period": "day"},
        )

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
    async def test_non_admin_access_forbidden(self, mock_non_admin_auth):
        """Test that non-admin users cannot access admin endpoints."""
        # Create request
        req = func.HttpRequest(
            method="GET",
            url="http://localhost/api/admin/users",
            body=b"",
            headers={},
            route_params={"resource": "users"},
        )

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 403
        response_data = json.loads(response.get_body())
        assert response_data["error"] == "Forbidden"
        assert "Admin privileges required" in response_data["message"]

    @pytest.mark.asyncio
    async def test_get_system_health_database_failure(
        self, mock_admin_auth, mock_cosmos_client
    ):
        """Test system health check when database is unavailable."""
        # Arrange
        # Mock database failure
        mock_cosmos_client.query_items.side_effect = Exception(
            "Database connection failed"
        )

        # Create request
        req = func.HttpRequest(
            method="GET",
            url="http://localhost/api/admin/system/health",
            body=b"",
            headers={},
            route_params={"resource": "system", "action": "health"},
        )

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 503
        response_data = json.loads(response.get_body())
        assert response_data["status"] == "degraded"
        assert "unhealthy" in response_data["components"]["database"]["status"]

    @pytest.mark.asyncio
    async def test_update_user_role_user_not_found(
        self, mock_admin_auth, mock_cosmos_client
    ):
        """Test user role update with non-existent user."""
        # Arrange
        target_user_id = "non-existent-user"
        new_role_data = {"role": "admin"}

        # Mock database responses - user not found
        from unittest.mock import AsyncMock

        mock_cosmos_client.query_items = AsyncMock(return_value=[])

        # Create request
        req = func.HttpRequest(
            method="PUT",
            url=f"http://localhost/api/admin/users/{target_user_id}/role",
            body=json.dumps(new_role_data).encode(),
            headers={"Content-Type": "application/json"},
            route_params={
                "resource": "users",
                "user_id": target_user_id,
                "action": "role",
            },
        )

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 404
        response_data = json.loads(response.get_body())
        assert "User not found" in response_data["error"]

    # ADDITIONAL TESTS FOR COVERAGE IMPROVEMENT

    @pytest.mark.asyncio
    async def test_list_users_with_search_filter(self, mock_admin_auth, mock_cosmos_client):
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

        mock_cosmos_client.query_items = AsyncMock(
            side_effect=[mock_users, [1]]  # Users list and count
        )

        # Create request with search and role filter
        req = func.HttpRequest(
            method="GET",
            url="http://localhost/api/admin/users?search=john&role=user&page=2&limit=25",
            body=b"",
            headers={},
            route_params={"resource": "users"},
            params={"search": "john", "role": "user", "page": "2", "limit": "25"},
        )

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert len(response_data["users"]) == 1
        assert response_data["pagination"]["current_page"] == 2
        assert response_data["pagination"]["limit"] == 25

    @pytest.mark.asyncio
    async def test_update_user_role_invalid_json(self, mock_admin_auth, mock_cosmos_client):
        """Test user role update with invalid JSON."""
        # Create request with invalid JSON
        req = func.HttpRequest(
            method="PUT",
            url="http://localhost/api/admin/users/user-123/role",
            body=b"{invalid json}",
            headers={"Content-Type": "application/json"},
            route_params={
                "resource": "users",
                "user_id": "user-123",
                "action": "role",
            },
        )

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert "Invalid JSON" in response_data["error"]

    @pytest.mark.asyncio
    async def test_reset_test_data_success(self, mock_admin_auth, mock_cosmos_client):
        """Test successful test data reset."""
        # Mock database responses
        mock_cosmos_client.query_items = AsyncMock(return_value=[])
        mock_cosmos_client.delete_item = AsyncMock()

        # Mock environment to allow test data operations
        with patch.dict("os.environ", {"ENVIRONMENT": "test"}):
            # Create request with proper authentication headers
            req = func.HttpRequest(
                method="POST",
                url="http://localhost/api/admin/test-data/reset",
                body=b"{}",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer admin-token",
                },
                route_params={"resource": "test-data", "action": "reset"},
            )

            # Act
            response = await admin_main(req)

            # Assert
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["environment"] == "test"
            assert "reset_at" in response_data
            assert "containers_reset" in response_data

    @pytest.mark.asyncio
    async def test_seed_test_data_success(self, mock_admin_auth, mock_cosmos_client):
        """Test successful test data seeding."""
        # Mock database responses
        mock_cosmos_client.query_items = AsyncMock(return_value=[])
        mock_cosmos_client.create_item = AsyncMock()

        # Mock environment to allow test data operations
        with patch.dict("os.environ", {"ENVIRONMENT": "test"}):
            # Create request with proper authentication headers
            req = func.HttpRequest(
                method="POST",
                url="http://localhost/api/admin/test-data/seed",
                body=b"{}",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer admin-token",
                },
                route_params={"resource": "test-data", "action": "seed"},
            )

            # Act
            response = await admin_main(req)

            # Assert
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["environment"] == "test"
            assert "seeded_at" in response_data
            assert "data_created" in response_data

    @pytest.mark.asyncio
    async def test_resource_not_found_error(self, mock_admin_auth):
        """Test handling of unknown resource."""
        # Create request for unknown resource
        req = func.HttpRequest(
            method="GET",
            url="http://localhost/api/admin/unknown-resource",
            body=b"",
            headers={},
            route_params={"resource": "unknown-resource"},
        )

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 404
        response_data = json.loads(response.get_body())
        assert "Resource not found" in response_data["error"]

    @pytest.mark.asyncio
    async def test_list_users_with_masked_api_keys(self, mock_admin_auth, mock_cosmos_client):
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
                        "lastTested": "2025-06-15T08:00:00Z"
                    }
                },
            }
        ]

        mock_cosmos_client.query_items = AsyncMock(
            side_effect=[mock_users, [1]]
        )

        # Create request
        req = func.HttpRequest(
            method="GET",
            url="http://localhost/api/admin/users",
            body=b"",
            headers={},
            route_params={"resource": "users"},
            params={},
        )

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
    async def test_test_data_production_environment_blocked(self, mock_admin_auth):
        """Test that test data operations are blocked in production environment."""
        # Create request without mocking environment (defaults to production)
        req = func.HttpRequest(
            method="POST",
            url="http://localhost/api/admin/test-data/reset",
            body=b"{}",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer admin-token",
            },
            route_params={"resource": "test-data", "action": "reset"},
        )

        # Act
        response = await admin_main(req)

        # Assert
        assert response.status_code == 403
        response_data = json.loads(response.get_body())
        assert "only available in test environments" in response_data["message"]

    @pytest.mark.asyncio
    async def test_admin_api_general_exception_handling(self, mock_admin_auth):
        """Test general exception handling in admin API."""
        # Mock an exception in the authentication check
        with patch("api.admin_api.verify_jwt_token", side_effect=Exception("Database connection failed")):
            req = func.HttpRequest(
                method="GET",
                url="http://localhost/api/admin/users",
                body=b"",
                headers={"Authorization": "Bearer test-token"},
                route_params={"resource": "users"},
            )

            # Act
            response = await admin_main(req)

            # Assert - Should trigger handle_api_error
            assert response.status_code in [500, 401]  # Depending on exception handling


if __name__ == "__main__":
    pytest.main([__file__])
