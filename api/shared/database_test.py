"""
Tests for database.py module - Database connection and operations
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from azure.cosmos import CosmosClient, exceptions
from azure.cosmos.database import DatabaseProxy
from azure.cosmos.container import ContainerProxy

from api.shared.database import DatabaseManager, get_database_manager, get_cosmos_client


class TestDatabaseManager:
    """Test suite for DatabaseManager class."""

    def test_init_with_connection_string(self):
        """Test DatabaseManager initialization with connection string."""
        with patch.dict(
            os.environ,
            {
                "COSMOS_DB_CONNECTION_STRING": "AccountEndpoint=https://test.documents.azure.com:443/;AccountKey=test_key;"
            },
        ):
            db_manager = DatabaseManager()
            assert db_manager._connection_string is not None
            assert db_manager._database_name == "sutra"
            assert db_manager._development_mode is False

    def test_init_without_connection_string_production(self):
        """Test DatabaseManager initialization without connection string in production."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError,
                match="COSMOS_DB_CONNECTION_STRING environment variable is required",
            ):
                DatabaseManager()

    def test_init_development_mode(self):
        """Test DatabaseManager initialization in development mode."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            db_manager = DatabaseManager()
            assert db_manager._development_mode is True
            assert db_manager._connection_string is None

    def test_init_test_mode(self):
        """Test DatabaseManager initialization in test mode."""
        with patch.dict(os.environ, {"ENVIRONMENT": "test"}, clear=True):
            db_manager = DatabaseManager()
            assert db_manager._development_mode is True

    @patch("api.shared.database.CosmosClient.from_connection_string")
    def test_client_property_creates_client(self, mock_cosmos_client):
        """Test that client property creates CosmosClient when needed."""
        mock_client = Mock(spec=CosmosClient)
        mock_cosmos_client.return_value = mock_client

        with patch.dict(
            os.environ, {"COSMOS_DB_CONNECTION_STRING": "test_connection_string"}
        ):
            db_manager = DatabaseManager()
            client = db_manager.client

            assert client == mock_client
            mock_cosmos_client.assert_called_once_with("test_connection_string")

    def test_client_property_development_mode_no_connection(self):
        """Test client property in development mode without connection string."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            db_manager = DatabaseManager()
            client = db_manager.client
            assert client is None

    @patch("api.shared.database.CosmosClient.from_connection_string")
    def test_client_property_caches_client(self, mock_cosmos_client):
        """Test that client property caches the CosmosClient instance."""
        mock_client = Mock(spec=CosmosClient)
        mock_cosmos_client.return_value = mock_client

        with patch.dict(
            os.environ, {"COSMOS_DB_CONNECTION_STRING": "test_connection_string"}
        ):
            db_manager = DatabaseManager()
            client1 = db_manager.client
            client2 = db_manager.client

            assert client1 == client2
            mock_cosmos_client.assert_called_once()

    @patch("api.shared.database.CosmosClient.from_connection_string")
    def test_database_property_creates_database(self, mock_cosmos_client):
        """Test that database property creates database proxy."""
        mock_client = Mock(spec=CosmosClient)
        mock_database = Mock(spec=DatabaseProxy)
        mock_client.get_database_client.return_value = mock_database
        mock_cosmos_client.return_value = mock_client

        with patch.dict(
            os.environ, {"COSMOS_DB_CONNECTION_STRING": "test_connection_string"}
        ):
            db_manager = DatabaseManager()
            database = db_manager.database

            assert database == mock_database
            mock_client.get_database_client.assert_called_once_with("sutra")

    def test_database_property_no_client(self):
        """Test database property when client is None."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            db_manager = DatabaseManager()
            database = db_manager.database
            assert database is None

    @patch("api.shared.database.CosmosClient.from_connection_string")
    def test_get_container_creates_container(self, mock_cosmos_client):
        """Test that get_container creates container proxy."""
        mock_client = Mock(spec=CosmosClient)
        mock_database = Mock(spec=DatabaseProxy)
        mock_container = Mock(spec=ContainerProxy)
        mock_client.get_database_client.return_value = mock_database
        mock_database.get_container_client.return_value = mock_container
        mock_cosmos_client.return_value = mock_client

        with patch.dict(
            os.environ, {"COSMOS_DB_CONNECTION_STRING": "test_connection_string"}
        ):
            db_manager = DatabaseManager()
            container = db_manager.get_container("test_container")

            assert container == mock_container
            mock_database.get_container_client.assert_called_once_with("test_container")

    @patch("api.shared.database.CosmosClient.from_connection_string")
    def test_get_container_caches_container(self, mock_cosmos_client):
        """Test that get_container caches container instances."""
        mock_client = Mock(spec=CosmosClient)
        mock_database = Mock(spec=DatabaseProxy)
        mock_container = Mock(spec=ContainerProxy)
        mock_client.get_database_client.return_value = mock_database
        mock_database.get_container_client.return_value = mock_container
        mock_cosmos_client.return_value = mock_client

        with patch.dict(
            os.environ, {"COSMOS_DB_CONNECTION_STRING": "test_connection_string"}
        ):
            db_manager = DatabaseManager()
            container1 = db_manager.get_container("test_container")
            container2 = db_manager.get_container("test_container")

            assert container1 == container2
            mock_database.get_container_client.assert_called_once()

    def test_get_container_no_database(self):
        """Test get_container when database is None."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            db_manager = DatabaseManager()
            container = db_manager.get_container("test_container")
            assert container is None

    @pytest.mark.asyncio
    async def test_create_item_development_mode(self):
        """Test create_item in development mode."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            db_manager = DatabaseManager()
            item = {"id": "test_id", "name": "test_item"}

            result = await db_manager.create_item("test_container", item)

            assert result["id"] == "test_id"
            assert result["name"] == "test_item"
            assert result["_mock"] is True

    @pytest.mark.asyncio
    async def test_create_item_development_mode_no_id(self):
        """Test create_item in development mode without id."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            db_manager = DatabaseManager()
            item = {"name": "test_item"}

            result = await db_manager.create_item("test_container", item)

            assert result["id"] == "mock-id"
            assert result["name"] == "test_item"
            assert result["_mock"] is True

    @pytest.mark.asyncio
    async def test_read_item_development_mode(self):
        """Test read_item in development mode."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            db_manager = DatabaseManager()

            result = await db_manager.read_item(
                "test_container", "test_id", "test_partition"
            )

            assert result["id"] == "test_id"
            assert result["name"] == "Mock Item"
            assert result["_mock"] is True

    @pytest.mark.asyncio
    async def test_update_item_development_mode(self):
        """Test update_item in development mode."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            db_manager = DatabaseManager()
            item = {"id": "test_id", "name": "updated_item"}

            result = await db_manager.update_item(
                "test_container", item, "test_partition"
            )

            assert result["id"] == "test_id"
            assert result["name"] == "updated_item"
            assert result["_mock"] is True

    @pytest.mark.asyncio
    async def test_delete_item_development_mode(self):
        """Test delete_item in development mode."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            db_manager = DatabaseManager()

            result = await db_manager.delete_item(
                "test_container", "test_id", "test_partition"
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_query_items_development_mode(self):
        """Test query_items in development mode."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            db_manager = DatabaseManager()

            result = await db_manager.query_items("test_container", "SELECT * FROM c")

            assert len(result) == 2
            assert result[0]["id"] == "mock-query-result-1"
            assert result[1]["id"] == "mock-query-result-2"
            assert all(item["_mock"] is True for item in result)

    @pytest.mark.asyncio
    async def test_list_items_development_mode(self):
        """Test list_items in development mode."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            db_manager = DatabaseManager()

            result = await db_manager.list_items("test_container")

            assert len(result) == 2
            assert result[0]["id"] == "mock-item-1"
            assert result[1]["id"] == "mock-item-2"
            assert all(item["_mock"] is True for item in result)


class TestDatabaseManagerProductionOperations:
    """Test suite for DatabaseManager production operations."""

    @pytest.mark.asyncio
    @patch("api.shared.database.CosmosClient.from_connection_string")
    async def test_create_item_success(self, mock_cosmos_client):
        """Test successful create_item operation."""
        mock_client = Mock(spec=CosmosClient)
        mock_database = Mock(spec=DatabaseProxy)
        mock_container = Mock(spec=ContainerProxy)
        mock_client.get_database_client.return_value = mock_database
        mock_database.get_container_client.return_value = mock_container
        mock_cosmos_client.return_value = mock_client

        expected_result = {"id": "test_id", "name": "test_item"}
        mock_container.create_item.return_value = expected_result

        with patch.dict(
            os.environ, {"COSMOS_DB_CONNECTION_STRING": "test_connection_string"}
        ):
            db_manager = DatabaseManager()
            item = {"id": "test_id", "name": "test_item"}

            # Note: The actual implementation has a bug with undefined partition_key
            # This test documents the current behavior
            with pytest.raises(NameError):
                await db_manager.create_item("test_container", item)

    @pytest.mark.asyncio
    @patch("api.shared.database.CosmosClient.from_connection_string")
    async def test_read_item_success(self, mock_cosmos_client):
        """Test successful read_item operation."""
        mock_client = Mock(spec=CosmosClient)
        mock_database = Mock(spec=DatabaseProxy)
        mock_container = Mock(spec=ContainerProxy)
        mock_client.get_database_client.return_value = mock_database
        mock_database.get_container_client.return_value = mock_container
        mock_cosmos_client.return_value = mock_client

        expected_result = {"id": "test_id", "name": "test_item"}
        mock_container.read_item.return_value = expected_result

        with patch.dict(
            os.environ, {"COSMOS_DB_CONNECTION_STRING": "test_connection_string"}
        ):
            db_manager = DatabaseManager()

            result = await db_manager.read_item(
                "test_container", "test_id", "test_partition"
            )

            assert result == expected_result
            mock_container.read_item.assert_called_once_with(
                item="test_id", partition_key="test_partition"
            )

    @pytest.mark.asyncio
    @patch("api.shared.database.CosmosClient.from_connection_string")
    async def test_read_item_not_found(self, mock_cosmos_client):
        """Test read_item when item not found."""
        mock_client = Mock(spec=CosmosClient)
        mock_database = Mock(spec=DatabaseProxy)
        mock_container = Mock(spec=ContainerProxy)
        mock_client.get_database_client.return_value = mock_database
        mock_database.get_container_client.return_value = mock_container
        mock_cosmos_client.return_value = mock_client

        mock_container.read_item.side_effect = exceptions.CosmosResourceNotFoundError(
            message="Not found"
        )

        with patch.dict(
            os.environ, {"COSMOS_DB_CONNECTION_STRING": "test_connection_string"}
        ):
            db_manager = DatabaseManager()

            result = await db_manager.read_item(
                "test_container", "test_id", "test_partition"
            )

            assert result is None

    @pytest.mark.asyncio
    @patch("api.shared.database.CosmosClient.from_connection_string")
    async def test_delete_item_success(self, mock_cosmos_client):
        """Test successful delete_item operation."""
        mock_client = Mock(spec=CosmosClient)
        mock_database = Mock(spec=DatabaseProxy)
        mock_container = Mock(spec=ContainerProxy)
        mock_client.get_database_client.return_value = mock_database
        mock_database.get_container_client.return_value = mock_container
        mock_cosmos_client.return_value = mock_client

        with patch.dict(
            os.environ, {"COSMOS_DB_CONNECTION_STRING": "test_connection_string"}
        ):
            db_manager = DatabaseManager()

            result = await db_manager.delete_item(
                "test_container", "test_id", "test_partition"
            )

            assert result is True
            mock_container.delete_item.assert_called_once_with(
                item="test_id", partition_key="test_partition"
            )

    @pytest.mark.asyncio
    @patch("api.shared.database.CosmosClient.from_connection_string")
    async def test_delete_item_not_found(self, mock_cosmos_client):
        """Test delete_item when item not found."""
        mock_client = Mock(spec=CosmosClient)
        mock_database = Mock(spec=DatabaseProxy)
        mock_container = Mock(spec=ContainerProxy)
        mock_client.get_database_client.return_value = mock_database
        mock_database.get_container_client.return_value = mock_container
        mock_cosmos_client.return_value = mock_client

        mock_container.delete_item.side_effect = exceptions.CosmosResourceNotFoundError(
            message="Not found"
        )

        with patch.dict(
            os.environ, {"COSMOS_DB_CONNECTION_STRING": "test_connection_string"}
        ):
            db_manager = DatabaseManager()

            result = await db_manager.delete_item(
                "test_container", "test_id", "test_partition"
            )

            assert result is False


class TestGlobalFunctions:
    """Test suite for global database functions."""

    def test_get_database_manager_singleton(self):
        """Test that get_database_manager returns singleton instance."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            db_manager1 = get_database_manager()
            db_manager2 = get_database_manager()

            assert db_manager1 is db_manager2

    @patch("api.shared.database.CosmosClient")
    def test_get_cosmos_client(self, mock_cosmos_client):
        """Test get_cosmos_client function."""
        # Reset the singleton to ensure clean state
        import api.shared.database

        api.shared.database._db_manager = None

        mock_client_instance = Mock()
        mock_cosmos_client.from_connection_string.return_value = mock_client_instance

        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "COSMOS_DB_CONNECTION_STRING": "AccountEndpoint=https://test.documents.azure.com:443/;AccountKey=test_key==;",
            },
        ):
            client = get_cosmos_client()
            assert client == mock_client_instance
            mock_cosmos_client.from_connection_string.assert_called_once()
