import pytest
from unittest.mock import MagicMock, patch
from api.shared.database import (
    DatabaseManager,
    get_database_manager
)
from api.shared.error_handling import (
    SutraAPIError,
    handle_api_error
)
from pydantic import ValidationError
import azure.cosmos.exceptions as cosmos_exceptions
import azure.functions as func
import os


class TestDatabaseManager:
    """Test database manager functionality."""

    @pytest.fixture
    def mock_cosmos_client(self):
        """Mock Cosmos DB client."""
        with patch.dict(os.environ, {"COSMOS_DB_CONNECTION_STRING": "test_connection_string"}):
            mock_client = MagicMock()
            mock_database = MagicMock()
            mock_container = MagicMock()
            
            mock_client.get_database_client.return_value = mock_database
            mock_database.get_container_client.return_value = mock_container
            
            yield mock_client, mock_database, mock_container

    def test_database_manager_initialization(self, mock_cosmos_client):
        """Test database manager initialization."""
        mock_client, mock_database, mock_container = mock_cosmos_client
        
        with patch('api.shared.database.CosmosClient.from_connection_string', return_value=mock_client):
            db_manager = DatabaseManager()
            assert db_manager is not None
            assert hasattr(db_manager, 'client')

    def test_get_container_success(self, mock_cosmos_client):
        """Test successful container retrieval."""
        mock_client, mock_database, mock_container = mock_cosmos_client
        
        with patch('api.shared.database.CosmosClient.from_connection_string', return_value=mock_client):
            db_manager = DatabaseManager()
            container = db_manager.get_container("test_container")
            
            db_manager.client.get_database_client.assert_called_once()
            mock_database.get_container_client.assert_called_with("test_container")
            assert container == mock_container

    def test_get_container_failure(self, mock_cosmos_client):
        """Test container retrieval failure."""
        mock_client, mock_database, mock_container = mock_cosmos_client
        mock_database.get_container_client.side_effect = Exception("Container not found")
        
        with patch('api.shared.database.CosmosClient.from_connection_string', return_value=mock_client):
            db_manager = DatabaseManager()
            
            with pytest.raises(Exception, match="Container not found"):
                db_manager.get_container("invalid_container")

    def test_get_database_manager_singleton(self):
        """Test database manager singleton pattern."""
        with patch.dict(os.environ, {"COSMOS_DB_CONNECTION_STRING": "test_connection_string"}):
            manager1 = get_database_manager()
            manager2 = get_database_manager()
            
            assert manager1 is manager2


class TestErrorHandling:
    """Test error handling functionality."""

    def test_sutra_api_error_creation(self):
        """Test SutraAPIError creation and properties."""
        error = SutraAPIError("Test error", status_code=400, details={"detail": "validation failed"})
        
        assert str(error) == "Test error"
        assert error.status_code == 400
        assert error.details == {"detail": "validation failed"}

    def test_handle_api_error_with_cosmos_error(self):
        """Test handle_api_error with Cosmos DB error."""
        error = cosmos_exceptions.CosmosResourceNotFoundError(status_code=404, message="Item not found")
        
        response = handle_api_error(error)
        
        assert response.status_code == 404

    def test_handle_api_error_with_generic_error(self):
        """Test handle_api_error with generic exception."""
        error = Exception("Unexpected error")
        
        response = handle_api_error(error)
        
        assert response.status_code == 500
        response_body = response.get_body()
        assert b"internal_server_error" in response_body

    def test_handle_api_error_with_timeout_error(self):
        """Test handle_api_error with timeout error."""
        error = TimeoutError("Request timeout")
        
        response = handle_api_error(error)
        
        assert response.status_code == 500

    def test_handle_api_error_with_connection_error(self):
        """Test handle_api_error with connection error."""
        error = ConnectionError("Database connection failed")
        
        response = handle_api_error(error)
        
        assert response.status_code == 500


class TestErrorHandlingEdgeCases:
    """Test error handling edge cases."""

    def test_handle_api_error_with_none_error(self):
        """Test handle_api_error with None error."""
        response = handle_api_error(None)
        
        assert response.status_code == 500

    def test_handle_api_error_with_empty_message(self):
        """Test handle_api_error with empty message."""
        error = SutraAPIError("", status_code=400)
        
        response = handle_api_error(error)
        
        assert response.status_code == 400
