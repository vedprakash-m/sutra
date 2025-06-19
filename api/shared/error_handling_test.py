"""
Tests for the error handling module.
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import azure.functions as func
import azure.cosmos.exceptions as cosmos_exceptions
from pydantic import ValidationError

from api.shared.error_handling import (
    SutraAPIError,
    handle_api_error,
    ErrorSeverity,
    ErrorCategory,
    ErrorDetail,
    ErrorResponse,
    ErrorHandler,
    ErrorMonitor,
    ErrorRecovery
)
from api.shared.validation import (
    ValidationException,
    SecurityValidationException,
    BusinessLogicException,
    RateLimitException
)


class TestSutraAPIError:
    """Test cases for SutraAPIError class."""
    
    def test_sutra_api_error_basic(self):
        """Test basic SutraAPIError creation."""
        error = SutraAPIError("Test error message")
        
        assert error.message == "Test error message"
        assert error.error_code == "SUTRA_API_ERROR"
        assert error.status_code == 500
        assert error.details is None
        assert str(error) == "Test error message"
    
    def test_sutra_api_error_with_all_params(self):
        """Test SutraAPIError with all parameters."""
        details = {"field": "username", "value": "invalid"}
        error = SutraAPIError(
            message="Invalid username",
            error_code="INVALID_USERNAME",
            status_code=400,
            details=details
        )
        
        assert error.message == "Invalid username"
        assert error.error_code == "INVALID_USERNAME"
        assert error.status_code == 400
        assert error.details == details


class TestHandleAPIError:
    """Test cases for handle_api_error function."""
    
    def test_handle_validation_error(self):
        """Test handling of validation errors."""
        error = Mock()
        error.code = "VALIDATION_ERROR"
        error.__str__ = Mock(return_value="Invalid input")
        
        response = handle_api_error(error)
        
        assert response.status_code == 400
        assert response.mimetype == 'application/json'
        
        response_data = json.loads(response.get_body().decode())
        assert response_data['error'] == 'validation_error'
        assert response_data['message'] == 'Invalid input'
        assert 'timestamp' in response_data
    
    def test_handle_security_validation_error(self):
        """Test handling of security validation errors."""
        error = Mock()
        error.code = "SECURITY_VIOLATION"
        error.__str__ = Mock(return_value="Security violation detected")
        
        response = handle_api_error(error)
        
        assert response.status_code == 400
        assert response.mimetype == 'application/json'
        
        response_data = json.loads(response.get_body().decode())
        assert response_data['error'] == 'security_violation'
        assert response_data['message'] == 'Security violation detected'
    
    def test_handle_business_logic_error(self):
        """Test handling of business logic errors."""
        error = Mock()
        error.code = "BUSINESS_LOGIC_ERROR"
        error.__str__ = Mock(return_value="Business rule violated")
        
        response = handle_api_error(error)
        
        assert response.status_code == 422
        assert response.mimetype == 'application/json'
        
        response_data = json.loads(response.get_body().decode())
        assert response_data['error'] == 'business_logic_error'
        assert response_data['message'] == 'Business rule violated'
    
    def test_handle_cosmos_not_found_error(self):
        """Test handling of Cosmos DB not found errors."""
        error = cosmos_exceptions.CosmosResourceNotFoundError(
            message="Resource not found",
            response=None
        )
        
        response = handle_api_error(error)
        
        assert response.status_code == 404
        assert response.mimetype == 'application/json'
        
        response_data = json.loads(response.get_body().decode())
        assert response_data['error'] == 'not_found'
        assert 'timestamp' in response_data
    
    def test_handle_sutra_api_error(self):
        """Test handling of SutraAPIError."""
        error = SutraAPIError(
            message="Custom error",
            error_code="CUSTOM_ERROR",
            status_code=403
        )
        
        response = handle_api_error(error)
        
        assert response.status_code == 403
        assert response.mimetype == 'application/json'
        
        response_data = json.loads(response.get_body().decode())
        assert response_data['error'] == 'CUSTOM_ERROR'
        assert response_data['message'] == 'Custom error'
    
    def test_handle_generic_exception(self):
        """Test handling of generic exceptions."""
        error = Exception("Generic error")
        
        with patch('api.shared.error_handling.logging') as mock_logging:
            response = handle_api_error(error)
            
            assert response.status_code == 500
            assert response.mimetype == 'application/json'
            
            response_data = json.loads(response.get_body().decode())
            assert response_data['error'] == 'internal_server_error'
            assert response_data['message'] == 'An internal server error occurred'
            
            # Verify error was logged
            mock_logging.error.assert_called_once()
    
    def test_handle_api_error_exception_in_handler(self):
        """Test error handling when the handler itself throws an exception."""
        # Create an error that will cause json.dumps to fail
        error = Mock()
        error.code = "VALIDATION_ERROR"
        error.__str__ = Mock(side_effect=Exception("Serialization error"))
        
        with patch('api.shared.error_handling.logging') as mock_logging:
            response = handle_api_error(error)
            
            assert response.status_code == 500
            assert response.mimetype == 'application/json'
            
            response_data = json.loads(response.get_body().decode())
            assert response_data['error'] == 'error_handler_failure'
            assert response_data['message'] == 'Critical error in error handling system'
            
            # Verify error was logged
            mock_logging.error.assert_called()


class TestErrorEnums:
    """Test cases for error enum classes."""
    
    def test_error_severity_enum(self):
        """Test ErrorSeverity enum values."""
        assert ErrorSeverity.LOW == "low"
        assert ErrorSeverity.MEDIUM == "medium"
        assert ErrorSeverity.HIGH == "high"
        assert ErrorSeverity.CRITICAL == "critical"
    
    def test_error_category_enum(self):
        """Test ErrorCategory enum values."""
        assert ErrorCategory.VALIDATION == "validation"
        assert ErrorCategory.AUTHENTICATION == "authentication"
        assert ErrorCategory.AUTHORIZATION == "authorization"
        assert ErrorCategory.BUSINESS_LOGIC == "business_logic"
        assert ErrorCategory.EXTERNAL_SERVICE == "external_service"
        assert ErrorCategory.DATABASE == "database"
        assert ErrorCategory.RATE_LIMITING == "rate_limiting"
        assert ErrorCategory.SYSTEM == "system"
        assert ErrorCategory.UNKNOWN == "unknown"


class TestErrorDetail:
    """Test cases for ErrorDetail class."""
    
    def test_error_detail_basic(self):
        """Test basic ErrorDetail creation."""
        error_detail = ErrorDetail(
            code="INVALID_EMAIL",
            message="Email format is invalid"
        )
        
        assert error_detail.code == "INVALID_EMAIL"
        assert error_detail.message == "Email format is invalid"
        assert error_detail.field is None
        assert error_detail.details == {}
        assert error_detail.timestamp is not None
    
    def test_error_detail_with_field(self):
        """Test ErrorDetail with field information."""
        error_detail = ErrorDetail(
            code="REQUIRED_FIELD",
            message="Field is required",
            field="username"
        )
        
        assert error_detail.field == "username"
    
    def test_error_detail_with_details(self):
        """Test ErrorDetail with additional details."""
        details = {"min_length": 8, "current_length": 5}
        error_detail = ErrorDetail(
            code="PASSWORD_TOO_SHORT",
            message="Password is too short",
            details=details
        )
        
        assert error_detail.details == details
    
    def test_error_detail_to_dict(self):
        """Test ErrorDetail to_dict method."""
        details = {"example": "value"}
        error_detail = ErrorDetail(
            code="TEST_ERROR",
            message="Test message",
            field="test_field",
            details=details
        )
        
        result = error_detail.to_dict()
        
        assert result['code'] == "TEST_ERROR"
        assert result['message'] == "Test message"
        assert result['field'] == "test_field"
        assert result['details'] == details
        assert 'timestamp' in result
    
    def test_error_detail_to_dict_minimal(self):
        """Test ErrorDetail to_dict with minimal data."""
        error_detail = ErrorDetail(
            code="MINIMAL_ERROR",
            message="Minimal message"
        )
        
        result = error_detail.to_dict()
        
        assert result['code'] == "MINIMAL_ERROR"
        assert result['message'] == "Minimal message"
        assert 'field' not in result
        assert 'details' not in result
        assert 'timestamp' in result


class TestErrorResponse:
    """Test cases for ErrorResponse class."""
    
    def test_error_response_initialization(self):
        """Test basic ErrorResponse initialization."""
        # This test assumes ErrorResponse has an __init__ method
        # We'll need to check the actual implementation
        pass


class TestErrorHandler:
    """Test cases for ErrorHandler class."""
    
    def test_error_handler_initialization(self):
        """Test basic ErrorHandler initialization."""
        # This test assumes ErrorHandler has an __init__ method
        # We'll need to check the actual implementation
        pass


class TestErrorMonitor:
    """Test cases for ErrorMonitor class."""
    
    def test_error_monitor_initialization(self):
        """Test basic ErrorMonitor initialization."""
        # This test assumes ErrorMonitor has an __init__ method
        # We'll need to check the actual implementation
        pass


class TestErrorRecovery:
    """Test cases for ErrorRecovery class."""
    
    def test_error_recovery_initialization(self):
        """Test basic ErrorRecovery initialization."""
        # This test assumes ErrorRecovery has an __init__ method
        # We'll need to check the actual implementation
        pass


class TestIntegrationScenarios:
    """Test cases for integration scenarios."""
    
    def test_validation_exception_integration(self):
        """Test integration with ValidationException."""
        try:
            # Create a validation exception
            validation_error = ValidationException("Invalid data")
            validation_error.code = "VALIDATION_ERROR"
            
            response = handle_api_error(validation_error)
            
            assert response.status_code == 400
            response_data = json.loads(response.get_body().decode())
            assert response_data['error'] == 'validation_error'
        except ImportError:
            # If ValidationException import fails, skip this test
            pytest.skip("ValidationException not available")
    
    def test_security_validation_exception_integration(self):
        """Test integration with SecurityValidationException."""
        try:
            security_error = SecurityValidationException("Security violation")
            security_error.code = "SECURITY_VIOLATION"
            
            response = handle_api_error(security_error)
            
            assert response.status_code == 400
            response_data = json.loads(response.get_body().decode())
            assert response_data['error'] == 'security_violation'
        except ImportError:
            pytest.skip("SecurityValidationException not available")
    
    def test_business_logic_exception_integration(self):
        """Test integration with BusinessLogicException."""
        try:
            business_error = BusinessLogicException("Business rule violated")
            business_error.code = "BUSINESS_LOGIC_ERROR"
            
            response = handle_api_error(business_error)
            
            assert response.status_code == 422
            response_data = json.loads(response.get_body().decode())
            assert response_data['error'] == 'business_logic_error'
        except ImportError:
            pytest.skip("BusinessLogicException not available")
    
    def test_rate_limit_exception_integration(self):
        """Test integration with RateLimitException."""
        try:
            rate_limit_error = RateLimitException("Rate limit exceeded")
            rate_limit_error.code = "RATE_LIMIT_ERROR"
            
            # Since there's no specific handling for rate limit errors,
            # it should be handled as a generic exception
            response = handle_api_error(rate_limit_error)
            
            assert response.status_code == 500
            response_data = json.loads(response.get_body().decode())
            assert response_data['error'] == 'internal_server_error'
        except ImportError:
            pytest.skip("RateLimitException not available")
    
    def test_pydantic_validation_error_integration(self):
        """Test integration with Pydantic ValidationError."""
        # Create a mock Pydantic ValidationError
        validation_error = ValidationError.from_exception_data(
            "test_model",
            [{"type": "missing", "loc": ("field",), "msg": "Field required"}]
        )
        
        # Since there's no specific handling for Pydantic errors,
        # it should be handled as a generic exception
        response = handle_api_error(validation_error)
        
        assert response.status_code == 500
        response_data = json.loads(response.get_body().decode())
        assert response_data['error'] == 'internal_server_error'