"""
Comprehensive tests for error handling module to achieve 75% coverage.
Focuses on missing coverage areas: ErrorHandler methods, ErrorMonitor, ErrorRecovery, and utility functions.
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import azure.functions as func
from ..conftest import create_auth_request
import azure.cosmos.exceptions as cosmos_exceptions
from pydantic import ValidationError, BaseModel

from api.shared.error_handling import (
    SutraAPIError,
    handle_api_error,
    ErrorSeverity,
    ErrorCategory,
    ErrorDetail,
    ErrorResponse,
    ErrorHandler,
    ErrorMonitor,
    ErrorRecovery,
    handle_api_errors,
    extract_request_id,
    add_correlation_id,
    is_retriable_error,
    sanitize_error_message,
)
from api.shared.validation import (
    ValidationException,
    SecurityValidationException,
    BusinessLogicException,
    RateLimitException,
)


class TestErrorHandlerComprehensive:
    """Comprehensive tests for ErrorHandler static methods."""

    def test_handle_validation_error_with_validation_exception(self):
        """Test handling ValidationException."""
        exc = ValidationException("Invalid email format", "email", "VALIDATION_ERROR")
        request_id = "req-123"

        result = ErrorHandler.handle_validation_error(exc, request_id)

        assert isinstance(result, ErrorResponse)
        assert result.status_code == 400
        assert result.error.code == "VALIDATION_ERROR"
        assert result.error.message == "Invalid email format"
        assert result.error.field == "email"
        assert result.request_id == request_id

    def test_handle_validation_error_with_security_validation_exception(self):
        """Test handling SecurityValidationException."""
        exc = SecurityValidationException("XSS attempt detected", "content")
        request_id = "req-456"

        with patch("api.shared.error_handling.logger") as mock_logger:
            result = ErrorHandler.handle_validation_error(exc, request_id)

            assert isinstance(result, ErrorResponse)
            assert result.status_code == 400
            assert result.error.code == "SECURITY_VIOLATION"
            assert result.error.message == "XSS attempt detected"
            assert result.error.field == "content"

            # Verify security violation was logged with warning level
            mock_logger.warning.assert_called_once()

    def test_handle_validation_error_with_pydantic_validation_error(self):
        """Test handling Pydantic ValidationError."""

        # Create a simple Pydantic model for testing
        class TestModel(BaseModel):
            name: str
            age: int

        try:
            TestModel(name="John", age="not_a_number")
        except ValidationError as exc:
            request_id = "req-789"

            with patch("api.shared.error_handling.logger") as mock_logger:
                result = ErrorHandler.handle_validation_error(exc, request_id)

                assert isinstance(result, ErrorResponse)
                assert result.status_code == 400
                assert result.error.code == "PYDANTIC_VALIDATION_ERROR"
                assert "age" in result.error.field
                assert result.request_id == request_id

                # Verify logging
                mock_logger.info.assert_called_once()

    def test_handle_validation_error_with_multiple_pydantic_errors(self):
        """Test handling Pydantic ValidationError with multiple errors."""

        class TestModel(BaseModel):
            name: str
            age: int
            email: str

        try:
            TestModel(name="", age="not_a_number", email="invalid_email")
        except ValidationError as exc:
            result = ErrorHandler.handle_validation_error(exc)

            assert isinstance(result, ErrorResponse)
            assert result.status_code == 400
            assert result.error.code == "PYDANTIC_VALIDATION_ERROR"
            # Note: depending on validation order, might have 0 or more additional errors

    def test_handle_validation_error_with_value_error(self):
        """Test handling generic ValueError."""
        exc = ValueError("Invalid date format")
        request_id = "req-999"

        with patch("api.shared.error_handling.logger") as mock_logger:
            result = ErrorHandler.handle_validation_error(exc, request_id)

            assert isinstance(result, ErrorResponse)
            assert result.status_code == 400
            assert result.error.code == "INVALID_INPUT"
            assert result.error.message == "Invalid date format"
            assert result.request_id == request_id

            # Verify logging
            mock_logger.info.assert_called_once()

    def test_handle_authentication_error_default(self):
        """Test handling authentication error with default message."""
        request_id = "req-auth-1"

        with patch("api.shared.error_handling.logger") as mock_logger:
            result = ErrorHandler.handle_authentication_error(request_id=request_id)

            assert isinstance(result, ErrorResponse)
            assert result.status_code == 401
            assert result.error.code == "AUTHENTICATION_REQUIRED"
            assert result.error.message == "Authentication required"
            assert result.request_id == request_id

            # Verify logging
            mock_logger.warning.assert_called_once()

    def test_handle_authentication_error_custom_message(self):
        """Test handling authentication error with custom message."""
        message = "Invalid API key"
        request_id = "req-auth-2"

        with patch("api.shared.error_handling.logger") as mock_logger:
            result = ErrorHandler.handle_authentication_error(message, request_id)

            assert isinstance(result, ErrorResponse)
            assert result.status_code == 401
            assert result.error.code == "AUTHENTICATION_REQUIRED"
            assert result.error.message == message
            assert result.request_id == request_id

    def test_handle_authorization_error_default(self):
        """Test handling authorization error with default message."""
        request_id = "req-authz-1"

        with patch("api.shared.error_handling.logger") as mock_logger:
            result = ErrorHandler.handle_authorization_error(request_id=request_id)

            assert isinstance(result, ErrorResponse)
            assert result.status_code == 403
            assert result.error.code == "INSUFFICIENT_PERMISSIONS"
            assert result.error.message == "Insufficient permissions"
            assert result.request_id == request_id

            # Verify logging
            mock_logger.warning.assert_called_once()

    def test_handle_authorization_error_custom_message(self):
        """Test handling authorization error with custom message."""
        message = "Admin access required"
        request_id = "req-authz-2"

        result = ErrorHandler.handle_authorization_error(message, request_id)

        assert isinstance(result, ErrorResponse)
        assert result.status_code == 403
        assert result.error.code == "INSUFFICIENT_PERMISSIONS"
        assert result.error.message == message
        assert result.request_id == request_id

    def test_handle_not_found_error_basic(self):
        """Test handling not found error with basic parameters."""
        request_id = "req-notfound-1"

        with patch("api.shared.error_handling.logger") as mock_logger:
            result = ErrorHandler.handle_not_found_error(request_id=request_id)

            assert isinstance(result, ErrorResponse)
            assert result.status_code == 404
            assert result.error.code == "RESOURCE_NOT_FOUND"
            assert result.error.message == "Resource not found"
            assert result.request_id == request_id
            assert result.error.details["resource_type"] == "resource"
            assert result.error.details["resource_id"] is None

            # Verify logging
            mock_logger.info.assert_called_once()

    def test_handle_not_found_error_with_resource_info(self):
        """Test handling not found error with resource information."""
        resource_type = "prompt"
        resource_id = "prompt-123"
        request_id = "req-notfound-2"

        result = ErrorHandler.handle_not_found_error(
            resource_type, resource_id, request_id
        )

        assert isinstance(result, ErrorResponse)
        assert result.status_code == 404
        assert result.error.code == "RESOURCE_NOT_FOUND"
        assert result.error.message == "Prompt not found (ID: prompt-123)"
        assert result.error.details["resource_type"] == resource_type
        assert result.error.details["resource_id"] == resource_id

    def test_handle_rate_limit_error(self):
        """Test handling rate limit error."""
        exc = RateLimitException("Rate limit exceeded for API calls")
        request_id = "req-rate-1"

        with patch("api.shared.error_handling.logger") as mock_logger:
            result = ErrorHandler.handle_rate_limit_error(exc, request_id)

            assert isinstance(result, ErrorResponse)
            assert result.status_code == 429
            assert result.error.code == "RATE_LIMIT_EXCEEDED"
            assert result.error.message == "Rate limit exceeded for API calls"
            assert result.error.details["retry_after"] == 3600
            assert result.request_id == request_id

            # Verify logging
            mock_logger.warning.assert_called_once()

    def test_handle_business_logic_error(self):
        """Test handling business logic error."""
        exc = BusinessLogicException(
            "Cannot delete collection with prompts", "collection_id"
        )
        request_id = "req-business-1"

        with patch("api.shared.error_handling.logger") as mock_logger:
            result = ErrorHandler.handle_business_logic_error(exc, request_id)

            assert isinstance(result, ErrorResponse)
            assert result.status_code == 422
            assert result.error.code == "BUSINESS_LOGIC_ERROR"
            assert result.error.message == "Cannot delete collection with prompts"
            assert result.error.field == "collection_id"
            assert result.request_id == request_id

            # Verify logging
            mock_logger.info.assert_called_once()

    def test_handle_external_service_error_basic(self):
        """Test handling external service error."""
        service_name = "OpenAI"
        error_message = "API quota exceeded"
        request_id = "req-ext-1"

        with patch("api.shared.error_handling.logger") as mock_logger:
            result = ErrorHandler.handle_external_service_error(
                service_name, error_message, request_id=request_id
            )

            assert isinstance(result, ErrorResponse)
            assert result.status_code == 502
            assert result.error.code == "EXTERNAL_SERVICE_ERROR"
            assert service_name in result.error.message
            assert error_message in result.error.message
            assert result.error.details["service"] == service_name
            assert result.error.details["original_error"] == error_message
            assert result.error.details["status_code"] is None

            # Verify logging
            mock_logger.error.assert_called_once()

    def test_handle_external_service_error_with_status_code(self):
        """Test handling external service error with status code."""
        service_name = "Anthropic"
        error_message = "Service unavailable"
        status_code = 503
        request_id = "req-ext-2"

        result = ErrorHandler.handle_external_service_error(
            service_name, error_message, status_code, request_id
        )

        assert isinstance(result, ErrorResponse)
        assert result.status_code == 502
        assert result.error.details["status_code"] == status_code

    def test_handle_database_error(self):
        """Test handling database error."""
        operation = "create_prompt"
        error_message = "Connection timeout"
        request_id = "req-db-1"

        with patch("api.shared.error_handling.logger") as mock_logger:
            result = ErrorHandler.handle_database_error(
                operation, error_message, request_id
            )

            assert isinstance(result, ErrorResponse)
            assert result.status_code == 500
            assert result.error.code == "DATABASE_ERROR"
            assert (
                result.error.message
                == "A database error occurred. Please try again later."
            )
            assert result.error.details["operation"] == operation
            assert result.request_id == request_id

            # Verify logging
            mock_logger.error.assert_called_once()

    def test_handle_system_error_basic(self):
        """Test handling system error without traceback."""
        exc = Exception("Out of memory")
        request_id = "req-sys-1"

        with patch("api.shared.error_handling.logger") as mock_logger:
            result = ErrorHandler.handle_system_error(
                exc, request_id, include_traceback=False
            )

            assert isinstance(result, ErrorResponse)
            assert result.status_code == 500
            assert result.error.code == "INTERNAL_SERVER_ERROR"
            assert (
                result.error.message
                == "An unexpected error occurred. Please try again later."
            )
            assert result.error.details["error_type"] == "Exception"
            assert result.error.details["error_message"] == str(exc)
            assert "traceback" not in result.error.details

            # Verify logging
            mock_logger.error.assert_called_once()

    def test_handle_system_error_with_traceback(self):
        """Test handling system error with traceback."""
        exc = Exception("Critical failure")
        request_id = "req-sys-2"

        with patch("api.shared.error_handling.logger") as mock_logger, patch(
            "api.shared.error_handling.traceback.format_exc"
        ) as mock_traceback:
            mock_traceback.return_value = "Traceback line 1\nTraceback line 2"

            result = ErrorHandler.handle_system_error(
                exc, request_id, include_traceback=True
            )

            assert isinstance(result, ErrorResponse)
            assert result.status_code == 500
            assert result.error.code == "INTERNAL_SERVER_ERROR"
            assert (
                result.error.details["traceback"]
                == "Traceback line 1\nTraceback line 2"
            )


class TestErrorDecorator:
    """Tests for handle_api_errors decorator."""

    def test_handle_api_errors_decorator_success(self):
        """Test decorator with successful function execution."""

        @handle_api_errors
        def successful_function(req):
            return func.HttpResponse("Success", status_code=200)

        req = Mock(spec=func.HttpRequest)
        result = successful_function(req)

        assert isinstance(result, func.HttpResponse)
        assert result.status_code == 200

    def test_handle_api_errors_decorator_with_validation_error(self):
        """Test decorator handling ValidationException."""

        @handle_api_errors
        def failing_function(req):
            raise ValidationException("Invalid input", "field1")

        req = Mock(spec=func.HttpRequest)
        req.headers = {"x-request-id": "req-decorator-1"}

        with patch("api.shared.error_handling.extract_request_id") as mock_extract:
            mock_extract.return_value = "req-decorator-1"

            result = failing_function(req)

            assert isinstance(result, func.HttpResponse)
            response_data = json.loads(result.get_body().decode())
            assert response_data["error"]["code"] == "VALIDATION_ERROR"

    def test_handle_api_errors_decorator_with_generic_exception(self):
        """Test decorator handling generic exception."""

        @handle_api_errors
        def failing_function(req):
            raise Exception("Unexpected error")

        req = Mock(spec=func.HttpRequest)

        result = failing_function(req)

        assert isinstance(result, func.HttpResponse)
        response_data = json.loads(result.get_body().decode())
        assert response_data["error"]["code"] == "INTERNAL_SERVER_ERROR"


class TestErrorMonitor:
    """Tests for ErrorMonitor class."""

    def test_record_error_basic(self):
        """Test recording basic error information."""
        with patch("api.shared.error_handling.logger") as mock_logger:
            ErrorMonitor.record_error(
                ErrorCategory.VALIDATION,
                ErrorSeverity.LOW,
                "INVALID_EMAIL",
                "Email format is invalid",
            )

            # Verify logging
            mock_logger.info.assert_called_once()

    def test_record_error_with_all_parameters(self):
        """Test recording error with all parameters."""
        additional_context = {"field": "email", "value": "invalid@"}

        with patch("api.shared.error_handling.logger") as mock_logger:
            ErrorMonitor.record_error(
                ErrorCategory.AUTHENTICATION,
                ErrorSeverity.HIGH,
                "XSS_ATTEMPT",
                "XSS script detected",
                user_id="user123",
                request_id="req456",
                additional_context=additional_context,
            )

            # Verify logging with appropriate level for HIGH severity
            mock_logger.warning.assert_called_once()

    def test_record_error_critical_severity(self):
        """Test recording critical error."""
        with patch("api.shared.error_handling.logger") as mock_logger:
            ErrorMonitor.record_error(
                ErrorCategory.SYSTEM,
                ErrorSeverity.CRITICAL,
                "DATABASE_FAILURE",
                "Database connection lost",
            )

            # Verify critical logging
            mock_logger.critical.assert_called_once()

    def test_should_alert_true_cases(self):
        """Test cases where alerts should be triggered."""
        # Critical errors always trigger alerts
        assert (
            ErrorMonitor.should_alert(ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL)
            is True
        )
        assert (
            ErrorMonitor.should_alert(ErrorCategory.DATABASE, ErrorSeverity.CRITICAL)
            is True
        )

        # High severity errors in security and authentication trigger alerts
        assert (
            ErrorMonitor.should_alert(ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH)
            is True
        )
        assert (
            ErrorMonitor.should_alert(ErrorCategory.AUTHORIZATION, ErrorSeverity.HIGH)
            is True
        )

        # External service high severity errors trigger alerts
        assert (
            ErrorMonitor.should_alert(
                ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.HIGH
            )
            is True
        )

    def test_should_alert_false_cases(self):
        """Test cases where alerts should not be triggered."""
        # Low severity errors generally don't trigger alerts
        assert (
            ErrorMonitor.should_alert(ErrorCategory.VALIDATION, ErrorSeverity.LOW)
            is False
        )
        assert (
            ErrorMonitor.should_alert(ErrorCategory.BUSINESS_LOGIC, ErrorSeverity.LOW)
            is False
        )

        # Medium severity in most categories don't trigger alerts
        assert (
            ErrorMonitor.should_alert(ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM)
            is False
        )
        assert (
            ErrorMonitor.should_alert(ErrorCategory.RATE_LIMITING, ErrorSeverity.MEDIUM)
            is False
        )


class TestErrorRecovery:
    """Tests for ErrorRecovery class."""

    def test_should_retry_true_cases(self):
        """Test cases where retry should be attempted."""
        # External service errors are retriable
        assert ErrorRecovery.should_retry(ErrorCategory.EXTERNAL_SERVICE, 1) is True
        assert ErrorRecovery.should_retry(ErrorCategory.EXTERNAL_SERVICE, 2) is True

        # Database errors are retriable for low attempt counts
        assert ErrorRecovery.should_retry(ErrorCategory.DATABASE, 1) is True
        assert ErrorRecovery.should_retry(ErrorCategory.DATABASE, 2) is True

        # System errors are retriable for low attempt counts
        assert ErrorRecovery.should_retry(ErrorCategory.SYSTEM, 1) is True

    def test_should_retry_false_cases(self):
        """Test cases where retry should not be attempted."""
        # Validation errors are not retriable
        assert ErrorRecovery.should_retry(ErrorCategory.VALIDATION, 1) is False
        assert ErrorRecovery.should_retry(ErrorCategory.AUTHENTICATION, 1) is False
        assert ErrorRecovery.should_retry(ErrorCategory.AUTHORIZATION, 1) is False
        assert ErrorRecovery.should_retry(ErrorCategory.BUSINESS_LOGIC, 1) is False

        # High attempt counts should not retry
        assert ErrorRecovery.should_retry(ErrorCategory.EXTERNAL_SERVICE, 4) is False
        assert ErrorRecovery.should_retry(ErrorCategory.DATABASE, 4) is False

    def test_get_retry_delay(self):
        """Test retry delay calculation."""
        # First attempt
        delay1 = ErrorRecovery.get_retry_delay(1)
        assert delay1 == 1.0

        # Second attempt (exponential backoff)
        delay2 = ErrorRecovery.get_retry_delay(2)
        assert delay2 == 2.0

        # Third attempt
        delay3 = ErrorRecovery.get_retry_delay(3)
        assert delay3 == 4.0

        # High attempt count should be capped
        delay_high = ErrorRecovery.get_retry_delay(10)
        assert delay_high == 60.0  # Maximum delay

    def test_get_fallback_response_available(self):
        """Test fallback responses for available categories."""
        # External service fallback
        fallback = ErrorRecovery.get_fallback_response(ErrorCategory.EXTERNAL_SERVICE)
        assert fallback is not None
        assert fallback["message"] == "External service temporarily unavailable"
        assert fallback["fallback"] is True

        # Database fallback
        fallback = ErrorRecovery.get_fallback_response(ErrorCategory.DATABASE)
        assert fallback is not None
        assert fallback["message"] == "Data temporarily unavailable"
        assert fallback["fallback"] is True

    def test_get_fallback_response_unavailable(self):
        """Test fallback responses for categories without fallbacks."""
        # Categories that shouldn't have fallbacks
        assert ErrorRecovery.get_fallback_response(ErrorCategory.VALIDATION) is None
        assert ErrorRecovery.get_fallback_response(ErrorCategory.AUTHENTICATION) is None
        assert ErrorRecovery.get_fallback_response(ErrorCategory.AUTHORIZATION) is None
        assert ErrorRecovery.get_fallback_response(ErrorCategory.BUSINESS_LOGIC) is None


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_extract_request_id_from_headers(self):
        """Test extracting request ID from headers."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"x-request-id": "req-header-123"}

        request_id = extract_request_id(req)
        assert request_id == "req-header-123"

    def test_extract_request_id_from_query_params(self):
        """Test extracting request ID from query parameters."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {}
        req.params = {"request_id": "req-query-456"}

        request_id = extract_request_id(req)
        assert request_id == "req-query-456"

    def test_extract_request_id_none(self):
        """Test extracting request ID when none present."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {}
        req.params = {}

        request_id = extract_request_id(req)
        assert request_id is None

    def test_add_correlation_id_with_id(self):
        """Test adding correlation ID to response."""
        response_dict = {"error": "test_error", "message": "Test message"}
        request_id = "corr-123"

        result = add_correlation_id(response_dict, request_id)

        assert result["request_id"] == request_id
        assert result["error"] == "test_error"
        assert result["message"] == "Test message"

    def test_add_correlation_id_without_id(self):
        """Test adding correlation ID when ID is None."""
        response_dict = {"error": "test_error", "message": "Test message"}

        result = add_correlation_id(response_dict, None)

        assert "request_id" not in result
        assert result["error"] == "test_error"
        assert result["message"] == "Test message"

    def test_is_retriable_error_true_cases(self):
        """Test errors that should be retried."""
        # Connection errors
        conn_error = Exception("Connection timeout")
        assert is_retriable_error(conn_error) is True

        # Timeout errors
        timeout_error = Exception("Request timeout")
        assert is_retriable_error(timeout_error) is True

        # Temporary errors
        temp_error = Exception("Temporary failure")
        assert is_retriable_error(temp_error) is True

        # Service unavailable
        service_error = Exception("Service unavailable")
        assert is_retriable_error(service_error) is True

    def test_is_retriable_error_false_cases(self):
        """Test errors that should not be retried."""
        # Validation errors
        validation_error = ValidationException("Invalid input")
        assert is_retriable_error(validation_error) is False

        # Business logic errors
        business_error = BusinessLogicException("Business rule violated")
        assert is_retriable_error(business_error) is False

        # Generic errors without retriable keywords
        generic_error = Exception("Unknown error")
        assert is_retriable_error(generic_error) is False

    def test_sanitize_error_message_with_sensitive_data(self):
        """Test sanitizing error messages with sensitive information."""
        message = "Authentication failed for user password123 with API key sk-1234567890abcdef"

        sanitized = sanitize_error_message(message)

        assert "password123" not in sanitized
        assert "sk-1234567890abcdef" not in sanitized
        assert "[REDACTED]" in sanitized

    def test_sanitize_error_message_clean(self):
        """Test sanitizing clean error messages."""
        message = "Invalid email format"

        sanitized = sanitize_error_message(message)

        assert sanitized == message  # Should remain unchanged

    def test_sanitize_error_message_with_various_sensitive_patterns(self):
        """Test sanitizing various sensitive patterns."""
        messages = [
            "Token abc123def456 is invalid",
            "Password: secret123 is wrong",
            "API_KEY=sk-proj-abcdef123456 failed",
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature authentication failed",
        ]

        for message in messages:
            sanitized = sanitize_error_message(message)
            assert "[REDACTED]" in sanitized
            # Verify sensitive parts are removed
            assert "abc123def456" not in sanitized
            assert "secret123" not in sanitized
            assert "sk-proj-abcdef123456" not in sanitized
            assert (
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature"
                not in sanitized
            )


class TestErrorResponseIntegration:
    """Integration tests for ErrorResponse class."""

    def test_error_response_to_dict_comprehensive(self):
        """Test comprehensive ErrorResponse to_dict conversion."""
        error = ErrorDetail(
            code="VALIDATION_ERROR",
            message="Invalid input data",
            field="email",
            details={"pattern": "email", "value": "invalid"},
        )
        additional_error = ErrorDetail(
            code="REQUIRED_FIELD", message="Name is required", field="name"
        )

        response = ErrorResponse(
            status_code=400,
            error=error,
            request_id="integration-test-123",
            additional_errors=[additional_error],
        )

        result = response.to_dict()

        assert result["status_code"] == 400
        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert result["error"]["message"] == "Invalid input data"
        assert result["error"]["field"] == "email"
        assert result["error"]["details"]["pattern"] == "email"
        assert result["request_id"] == "integration-test-123"
        assert len(result["additional_errors"]) == 1
        assert result["additional_errors"][0]["code"] == "REQUIRED_FIELD"

    def test_error_response_to_azure_response(self):
        """Test ErrorResponse to Azure Functions HTTP response conversion."""
        error = ErrorDetail(code="NOT_FOUND", message="Resource not found")
        response = ErrorResponse(status_code=404, error=error)

        azure_response = response.to_azure_response()

        assert isinstance(azure_response, func.HttpResponse)
        assert azure_response.status_code == 404
        assert azure_response.headers["Content-Type"] == "application/json"

        body_data = json.loads(azure_response.get_body().decode())
        assert body_data["error"]["code"] == "NOT_FOUND"
        assert body_data["error"]["message"] == "Resource not found"
