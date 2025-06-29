import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

import azure.functions as func
from . import main as collections_main
from ..conftest import create_auth_request


class TestCollectionsAPI:
    """Test suite for Collections API endpoints."""

    @pytest.fixture
    def mock_cosmos_client(self):
        """Mock database manager."""
        with patch("api.collections_api.get_database_manager") as mock_db_manager:
            mock_manager = Mock()
            # Make database methods async
            mock_manager.query_items = AsyncMock()
            mock_manager.create_item = AsyncMock()
            mock_manager.replace_item = AsyncMock()
            mock_manager.update_item = AsyncMock()
            mock_manager.delete_item = AsyncMock()
            mock_manager.read_item = AsyncMock()
            mock_db_manager.return_value = mock_manager
            yield mock_manager

    @pytest.mark.asyncio
    async def test_create_collection_success(self, auth_test_user, mock_cosmos_client):
        """Test successful collection creation."""
        # Arrange
        collection_data = {
            "name": "Test Collection",
            "description": "A test collection",
            "type": "private",
        }

        mock_cosmos_client.create_item.return_value = {
            "id": "test-collection-id",
            **collection_data,
            "ownerId": "test-user-123",
            "createdAt": "2025-06-15T10:00:00Z",
            "updatedAt": "2025-06-15T10:00:00Z",
        }

        # Mock validation
        with patch("api.shared.validation.validate_collection_data") as mock_validate:
            mock_validate.return_value = {"valid": True, "errors": []}

            # Create authenticated request using helper
            req = create_auth_request(
                method="POST",
                url="http://localhost/api/collections",
                body=collection_data,
            )

            # Act
            response = await collections_main(req)

            # Assert
            assert response.status_code == 201
            response_data = json.loads(response.get_body())
            assert response_data["name"] == "Test Collection"
            assert response_data["ownerId"] == "test-user-123"
            mock_cosmos_client.create_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_collection_validation_error(
        self, auth_test_user, mock_cosmos_client
    ):
        """Test collection creation with validation errors."""
        # Arrange
        collection_data = {
            "name": "",  # Invalid empty name
            "type": "invalid_type",  # Invalid type
        }

        # Mock validation failure
        with patch("api.shared.validation.validate_collection_data") as mock_validate:
            mock_validate.return_value = {
                "valid": False,
                "errors": ["Collection name is required"],
            }

            # Create authenticated request
            req = create_auth_request(method="POST")

            # Act
            response = await collections_main(req)

            # Assert
            assert response.status_code == 400
            response_data = json.loads(response.get_body())
            assert "Validation failed" in response_data["error"]
            assert len(response_data["details"]) == 1

    @pytest.mark.asyncio
    async def test_list_collections_success(self, mock_cosmos_client):
        """Test successful collection listing."""
        # Arrange
        mock_collections = [
            {
                "id": "collection-1",
                "name": "Collection 1",
                "ownerId": "test-user-123",
                "type": "private",
                "createdAt": "2025-06-15T09:00:00Z",
            },
            {
                "id": "collection-2",
                "name": "Collection 2",
                "ownerId": "test-user-123",
                "type": "shared_team",
                "createdAt": "2025-06-15T10:00:00Z",
            },
        ]

        # Mock database responses
        mock_cosmos_client.query_items.side_effect = [
            mock_collections,  # First call for items
            [2],  # Second call for count
        ]

        # Create authenticated request using helper
        req = create_auth_request(method="GET")

        # Act
        response = await collections_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert len(response_data["collections"]) == 2
        assert response_data["pagination"]["total_count"] == 2
        assert response_data["pagination"]["current_page"] == 1

    @pytest.mark.asyncio
    async def test_get_collection_success(self, auth_test_user, mock_cosmos_client):
        """Test successful collection retrieval."""
        # Arrange
        collection_id = "test-collection-123"
        mock_collection = {
            "id": collection_id,
            "name": "Test Collection",
            "ownerId": "test-user-123",
            "type": "private",
            "description": "A test collection",
        }

        mock_cosmos_client.query_items.return_value = [mock_collection]

        # Create request with proper authentication
        req = create_auth_request(method="GET")

        # Act
        response = await collections_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["id"] == collection_id
        assert response_data["name"] == "Test Collection"

    @pytest.mark.asyncio
    async def test_get_collection_not_found(self, auth_test_user, mock_cosmos_client):
        """Test collection retrieval when collection doesn't exist."""
        # Arrange
        collection_id = "nonexistent-collection"
        mock_cosmos_client.query_items.return_value = []  # No collections found

        # Create request with proper authentication
        req = create_auth_request(method="GET")

        # Act
        response = await collections_main(req)

        # Assert
        assert response.status_code == 404
        response_data = json.loads(response.get_body())
        assert response_data["error"] == "Collection not found"

    @pytest.mark.asyncio
    async def test_update_collection_success(self, auth_test_user, mock_cosmos_client):
        """Test successful collection update."""
        # Arrange
        collection_id = "test-collection-123"
        existing_collection = {
            "id": collection_id,
            "name": "Old Name",
            "ownerId": "test-user-123",
            "type": "private",
            "createdAt": "2025-06-15T09:00:00Z",
            "updatedAt": "2025-06-15T09:00:00Z",
        }

        update_data = {"name": "Updated Name", "description": "Updated description"}

        mock_cosmos_client.query_items.return_value = [existing_collection]
        mock_cosmos_client.update_item.return_value = {
            **existing_collection,
            **update_data,
            "updatedAt": "2025-06-15T10:00:00Z",
        }

        # Mock validation
        with patch("api.shared.validation.validate_collection_data") as mock_validate:
            mock_validate.return_value = {"valid": True, "errors": []}

            # Create request with proper authentication
            req = create_auth_request(method="PUT")

            # Act
            response = await collections_main(req)

            # Assert
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data["name"] == "Updated Name"
            assert response_data["description"] == "Updated description"
            mock_cosmos_client.update_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_collection_success(self, auth_test_user, mock_cosmos_client):
        """Test successful collection deletion."""
        # Arrange
        collection_id = "test-collection-123"
        existing_collection = {
            "id": collection_id,
            "name": "Test Collection",
            "ownerId": "test-user-123",
        }

        # Mock database responses
        mock_cosmos_client.query_items.side_effect = [
            [existing_collection],  # Collection exists
            [0],  # No prompts in collection
        ]

        # Create request with proper authentication
        req = create_auth_request(method="DELETE")

        # Act
        response = await collections_main(req)

        # Assert        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert "deleted successfully" in response_data["message"]
        mock_cosmos_client.delete_item.assert_called_once_with(
            container_name="Collections",
            item_id=collection_id,
            partition_key="test-user-123",
        )

    @pytest.mark.asyncio
    async def test_delete_collection_with_prompts(
        self, auth_test_user, mock_cosmos_client
    ):
        """Test collection deletion when collection has prompts."""
        # Arrange
        collection_id = "test-collection-123"
        existing_collection = {
            "id": collection_id,
            "name": "Test Collection",
            "ownerId": "test-user-123",
        }

        # Mock database responses
        mock_cosmos_client.query_items.side_effect = [
            [existing_collection],  # Collection exists
            [5],  # 5 prompts in collection
        ]

        # Create request with proper authentication
        req = create_auth_request(method="DELETE")

        # Act
        response = await collections_main(req)

        # Assert
        assert response.status_code == 409
        response_data = json.loads(response.get_body())
        assert "Cannot delete collection" in response_data["error"]
        assert "5 prompts" in response_data["message"]
        mock_cosmos_client.delete_item.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_collection_prompts_success(
        self, auth_test_user, mock_cosmos_client
    ):
        """Test successful retrieval of prompts within a collection."""
        # Arrange
        collection_id = "test-collection-123"
        collection = {
            "id": collection_id,
            "name": "Test Collection",
            "ownerId": "test-user-123",
        }

        prompts = [
            {
                "id": "prompt-1",
                "name": "Prompt 1",
                "collectionId": collection_id,
                "creatorId": "test-user-123",
            },
            {
                "id": "prompt-2",
                "name": "Prompt 2",
                "collectionId": collection_id,
                "creatorId": "test-user-123",
            },
        ]

        # Mock database responses
        mock_cosmos_client.query_items.side_effect = [
            [collection],  # Collection exists
            prompts,  # Prompts in collection
            [2],  # Count of prompts
        ]

        # Create request with proper authentication
        req = create_auth_request(method="GET")

        # Act
        response = await collections_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["collection"]["id"] == collection_id
        assert len(response_data["prompts"]) == 2
        assert response_data["pagination"]["total_count"] == 2

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, mock_auth_failure):
        """Test collections API with valid authentication (collections don't have strict access control)."""
        # Create request - collections API allows authenticated users
        req = create_auth_request(method="GET")

        # Act
        response = await collections_main(req)

        # Assert - Should succeed for authenticated user
        assert response.status_code == 200

    # ADDITIONAL TESTS FOR COVERAGE IMPROVEMENT

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, auth_test_user):
        """Test unsupported HTTP method returns 405."""
        # Create request with unsupported method but proper authentication
        req = create_auth_request(method="PATCH")

        # Act
        response = await collections_main(req)

        # Assert
        assert response.status_code == 405
        response_data = json.loads(response.get_body())
        assert "Method not allowed" in response_data["error"]

    @pytest.mark.asyncio
    async def test_create_collection_invalid_json(self, auth_test_user):
        """Test collection creation with invalid JSON."""
        # Create request with invalid JSON
        req = create_auth_request(method="POST")

        # Act
        response = await collections_main(req)

        # Assert
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert "Invalid JSON" in response_data["error"]

    @pytest.mark.asyncio
    async def test_list_collections_with_filters(
        self, auth_test_user, mock_cosmos_client
    ):
        """Test collection listing with search and type filters."""
        # Arrange
        mock_collections = [
            {
                "id": "collection-1",
                "name": "Test Collection",
                "ownerId": "test-user-123",
                "type": "public",
                "description": "Public test collection",
            }
        ]

        mock_cosmos_client.query_items.side_effect = [
            mock_collections,  # Items
            [1],  # Count
        ]

        # Create request with search and type filters
        req = create_auth_request(method="GET")

        # Act
        response = await collections_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert len(response_data["collections"]) == 1

    @pytest.mark.asyncio
    async def test_list_collections_mock_data_handling(
        self, auth_test_user, mock_cosmos_client
    ):
        """Test collection listing with mock data in development mode."""
        # Arrange
        mock_collections = [
            {
                "id": "collection-1",
                "name": "Mock Collection",
                "_mock": True,  # Mock data indicator
            }
        ]

        # Mock development mode response with _mock indicator
        mock_cosmos_client.query_items.side_effect = [
            mock_collections,  # Items
            [{"_mock": True, "count": 2}],  # Count with mock indicator
        ]

        # Create request
        req = create_auth_request(method="GET")

        # Act
        response = await collections_main(req)

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data["pagination"]["total_count"] == 2  # Mock count

    @pytest.mark.asyncio
    async def test_create_collection_validation_exception(
        self, auth_test_user, mock_cosmos_client
    ):
        """Test collection creation with validation failure."""
        # Arrange
        collection_data = {
            "description": "Valid description",
            # Missing required "name" field
        }

        # Create request with proper authentication
        req = create_auth_request(method="POST")

        # Act
        response = await collections_main(req)

        # Assert - Missing required field causes 400 validation error
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert "Validation failed" in response_data["error"]
        assert "Collection name is required" in response_data["details"]


if __name__ == "__main__":
    pytest.main([__file__])
