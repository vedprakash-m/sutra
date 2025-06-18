import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from api.shared.database import (
    DatabaseManager,
    get_database_manager
)
from api.shared.error_handling import (
    SutraAPIError,
    handle_api_error,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError
)
import azure.cosmos.exceptions as cosmos_exceptions


class TestDatabaseManager:
    """Test database manager functionality."""

    @pytest.fixture
    def mock_cosmos_client(self):
        """Mock Cosmos DB client."""
        mock_client = MagicMock()
        mock_database = MagicMock()
        mock_container = MagicMock()
        
        mock_client.get_database_client.return_value = mock_database
        mock_database.get_container_client.return_value = mock_container
        
        return mock_client, mock_database, mock_container

    def test_database_manager_initialization(self, mock_cosmos_client):
        """Test database manager initialization."""
        mock_client, mock_database, mock_container = mock_cosmos_client
        
        with patch('api.shared.database.CosmosClient', return_value=mock_client):
            db_manager = DatabaseManager()
            assert db_manager is not None
            assert hasattr(db_manager, 'client')

    def test_get_container_success(self, mock_cosmos_client):
        """Test successful container retrieval."""
        mock_client, mock_database, mock_container = mock_cosmos_client
        
        with patch('api.shared.database.CosmosClient', return_value=mock_client):
            db_manager = DatabaseManager()
            container = db_manager.get_container("test_container")
            
            mock_client.get_database_client.assert_called_once()
            mock_database.get_container_client.assert_called_with("test_container")
            assert container == mock_container

    def test_get_container_failure(self, mock_cosmos_client):
        """Test container retrieval failure."""
        mock_client, mock_database, mock_container = mock_cosmos_client
        mock_database.get_container_client.side_effect = Exception("Container not found")
        
        with patch('api.shared.database.CosmosClient', return_value=mock_client):
            db_manager = DatabaseManager()
            
            with pytest.raises(Exception, match="Container not found"):
                db_manager.get_container("invalid_container")

    def test_get_database_manager_singleton(self):
        """Test database manager singleton pattern."""
        manager1 = get_database_manager()
        manager2 = get_database_manager()
        
        # Should return the same instance
        assert manager1 is manager2


class TestErrorHandling:
    """Test error handling functionality."""

    def test_sutra_api_error_creation(self):
        """Test SutraAPIError creation and properties."""
        error = SutraAPIError("Test error", 400, {"detail": "validation failed"})
        
        assert str(error) == "Test error"
        assert error.status_code == 400
        assert error.details == {"detail": "validation failed"}

    def test_validation_error_creation(self):
        """Test ValidationError creation."""
        error = ValidationError("Invalid field", "email")
        
        assert str(error) == "Invalid field"
        assert error.field == "email"

    def test_authentication_error_creation(self):
        """Test AuthenticationError creation."""
        error = AuthenticationError("Invalid credentials")
        
        assert str(error) == "Invalid credentials"
        assert error.status_code == 401

    def test_authorization_error_creation(self):
        """Test AuthorizationError creation."""
        error = AuthorizationError("Access denied")
        
        assert str(error) == "Access denied"
        assert error.status_code == 403

    def test_resource_not_found_error_creation(self):
        """Test ResourceNotFoundError creation."""
        error = ResourceNotFoundError("User", "user-123")
        
        assert "User" in str(error)
        assert "user-123" in str(error)
        assert error.status_code == 404

    @pytest.mark.asyncio
    async def test_handle_api_error_with_known_error(self):
        """Test handle_api_error with known error types."""
        error = ValidationError("Invalid email", "email")
        
        response = await handle_api_error(error)
        
        assert response.status_code == 400
        response_body = response.get_body()
        assert b"Invalid email" in response_body

    @pytest.mark.asyncio
    async def test_handle_api_error_with_cosmos_error(self):
        """Test handle_api_error with Cosmos DB error."""
        error = cosmos_exceptions.CosmosResourceNotFoundError("Item not found")
        
        response = await handle_api_error(error)
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_handle_api_error_with_generic_error(self):
        """Test handle_api_error with generic exception."""
        error = Exception("Unexpected error")
        
        response = await handle_api_error(error)
        
        assert response.status_code == 500
        response_body = response.get_body()
        assert b"Internal server error" in response_body

    @pytest.mark.asyncio
    async def test_handle_api_error_with_timeout_error(self):
        """Test handle_api_error with timeout error."""
        error = TimeoutError("Request timeout")
        
        response = await handle_api_error(error)
        
        assert response.status_code == 408

    @pytest.mark.asyncio
    async def test_handle_api_error_with_connection_error(self):
        """Test handle_api_error with connection error."""
        error = ConnectionError("Database connection failed")
        
        response = await handle_api_error(error)
        
        assert response.status_code == 503


class TestErrorHandlingEdgeCases:
    """Test error handling edge cases."""

    @pytest.mark.asyncio
    async def test_handle_api_error_with_none_error(self):
        """Test handle_api_error with None error."""
        response = await handle_api_error(None)
        
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_handle_api_error_with_empty_message(self):
        """Test handle_api_error with empty message."""
        error = SutraAPIError("", 400)
        
        response = await handle_api_error(error)
        
        assert response.status_code == 400

    def test_error_inheritance_chain(self):
        """Test error inheritance chain."""
        auth_error = AuthenticationError("Test")
        assert isinstance(auth_error, SutraAPIError)
        assert isinstance(auth_error, Exception)
        
        validation_error = ValidationError("Test", "field")
        assert isinstance(validation_error, SutraAPIError)
        assert isinstance(validation_error, Exception)
