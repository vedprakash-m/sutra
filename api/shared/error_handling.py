"""
Error handling utilities for the Sutra API.

This module provides standardized error handling including:
- HTTP error responses
- Logging and monitoring
- Error classification
- Recovery strategies
"""

import logging
import traceback
import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union, List
from functools import wraps
import azure.functions as func
from datetime import datetime
from enum import Enum
import azure.cosmos.exceptions as cosmos_exceptions

import azure.functions as func
from pydantic import ValidationError

from .validation import (
    ValidationException,
    SecurityValidationException,
    BusinessLogicException,
    RateLimitException,
)


logger = logging.getLogger(__name__)


# =============================================================================
# CORE API ERROR CLASSES
# =============================================================================


class SutraAPIError(Exception):
    """Base API error for Sutra platform."""

    def __init__(
        self,
        message: str,
        error_code: str = "SUTRA_API_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


def handle_api_error(error: Exception) -> func.HttpResponse:
    """Handle API errors and return appropriate HTTP response."""
    try:
        # Handle validation errors
        if hasattr(error, "code") and error.code == "VALIDATION_ERROR":
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "validation_error",
                        "message": str(error),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        # Handle security validation errors
        if hasattr(error, "code") and error.code == "SECURITY_VIOLATION":
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "security_violation",
                        "message": str(error),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        # Handle business logic errors
        if hasattr(error, "code") and error.code == "BUSINESS_LOGIC_ERROR":
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "business_logic_error",
                        "message": str(error),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                status_code=422,
                mimetype="application/json",
            )

        # Handle Cosmos DB errors
        if isinstance(error, cosmos_exceptions.CosmosResourceNotFoundError):
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "not_found",
                        "message": str(error),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                status_code=404,
                mimetype="application/json",
            )

        # Handle SutraAPIError
        if isinstance(error, SutraAPIError):
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": error.error_code,
                        "message": error.message,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                status_code=error.status_code,
                mimetype="application/json",
            )

        # Handle generic exceptions
        logging.error(f"Unhandled error: {error}", exc_info=True)
        return func.HttpResponse(
            json.dumps(
                {
                    "error": "internal_server_error",
                    "message": "An internal server error occurred",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            status_code=500,
            mimetype="application/json",
        )

    except Exception as handler_error:
        # Fallback error handling
        logging.error(f"Error in error handler: {handler_error}", exc_info=True)
        return func.HttpResponse(
            json.dumps(
                {
                    "error": "error_handler_failure",
                    "message": "Critical error in error handling system",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            status_code=500,
            mimetype="application/json",
        )


# =============================================================================
# ERROR CLASSIFICATION
# =============================================================================


class ErrorSeverity(str, Enum):
    """Error severity levels for monitoring and alerting."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification and handling."""

    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    RATE_LIMITING = "rate_limiting"
    SYSTEM = "system"
    UNKNOWN = "unknown"


# =============================================================================
# ERROR RESPONSE MODELS
# =============================================================================


class ErrorDetail:
    """Detailed error information."""

    def __init__(
        self,
        code: str,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.field = field
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "code": self.code,
            "message": self.message,
            "timestamp": self.timestamp,
        }

        if self.field:
            result["field"] = self.field

        if self.details:
            result["details"] = self.details

        return result


class ErrorResponse:
    """Standardized error response."""

    def __init__(
        self,
        status_code: int,
        error: ErrorDetail,
        request_id: Optional[str] = None,
        additional_errors: Optional[List[ErrorDetail]] = None,
    ):
        self.status_code = status_code
        self.error = error
        self.request_id = request_id
        self.additional_errors = additional_errors or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"error": self.error.to_dict(), "status_code": self.status_code}

        if self.request_id:
            result["request_id"] = self.request_id

        if self.additional_errors:
            result["additional_errors"] = [
                err.to_dict() for err in self.additional_errors
            ]

        return result

    def to_azure_response(self) -> func.HttpResponse:
        """Convert to Azure Functions HTTP response."""
        return func.HttpResponse(
            body=json.dumps(self.to_dict()),
            status_code=self.status_code,
            headers={"Content-Type": "application/json"},
        )


# =============================================================================
# ERROR HANDLERS
# =============================================================================


class ErrorHandler:
    """Centralized error handling for the Sutra API."""

    @staticmethod
    def handle_validation_error(
        exc: Union[ValidationException, ValidationError, ValueError],
        request_id: Optional[str] = None,
    ) -> ErrorResponse:
        """Handle validation errors."""
        if isinstance(exc, ValidationException):
            error = ErrorDetail(code=exc.code, message=exc.message, field=exc.field)

            # Log based on severity
            if isinstance(exc, SecurityValidationException):
                logger.warning(
                    f"Security validation failed: {exc.message}",
                    extra={"request_id": request_id, "field": exc.field},
                )
                severity = ErrorSeverity.HIGH
            else:
                logger.info(
                    f"Validation failed: {exc.message}",
                    extra={"request_id": request_id, "field": exc.field},
                )
                severity = ErrorSeverity.LOW

            status_code = 400

        elif isinstance(exc, ValidationError):
            # Handle Pydantic validation errors
            errors = []
            for error_detail in exc.errors():
                field = ".".join(str(loc) for loc in error_detail["loc"])
                message = error_detail["msg"]
                errors.append(
                    ErrorDetail(
                        code="PYDANTIC_VALIDATION_ERROR", message=message, field=field
                    )
                )

            main_error = (
                errors[0]
                if errors
                else ErrorDetail(code="VALIDATION_ERROR", message="Validation failed")
            )

            logger.info(
                f"Pydantic validation failed: {str(exc)}",
                extra={"request_id": request_id},
            )

            return ErrorResponse(
                status_code=400,
                error=main_error,
                request_id=request_id,
                additional_errors=errors[1:] if len(errors) > 1 else None,
            )

        else:
            # Handle generic ValueError
            error = ErrorDetail(code="INVALID_INPUT", message=str(exc))

            logger.info(
                f"Input validation failed: {str(exc)}", extra={"request_id": request_id}
            )

            status_code = 400

        return ErrorResponse(
            status_code=status_code, error=error, request_id=request_id
        )

    @staticmethod
    def handle_authentication_error(
        message: str = "Authentication required", request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Handle authentication errors."""
        error = ErrorDetail(code="AUTHENTICATION_REQUIRED", message=message)

        logger.warning(
            f"Authentication failed: {message}", extra={"request_id": request_id}
        )

        return ErrorResponse(status_code=401, error=error, request_id=request_id)

    @staticmethod
    def handle_authorization_error(
        message: str = "Insufficient permissions", request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Handle authorization errors."""
        error = ErrorDetail(code="INSUFFICIENT_PERMISSIONS", message=message)

        logger.warning(
            f"Authorization failed: {message}", extra={"request_id": request_id}
        )

        return ErrorResponse(status_code=403, error=error, request_id=request_id)

    @staticmethod
    def handle_not_found_error(
        resource_type: str = "resource",
        resource_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> ErrorResponse:
        """Handle resource not found errors."""
        message = f"{resource_type.title()} not found"
        if resource_id:
            message += f" (ID: {resource_id})"

        error = ErrorDetail(
            code="RESOURCE_NOT_FOUND",
            message=message,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )

        logger.info(f"Resource not found: {message}", extra={"request_id": request_id})

        return ErrorResponse(status_code=404, error=error, request_id=request_id)

    @staticmethod
    def handle_rate_limit_error(
        exc: RateLimitException, request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Handle rate limiting errors."""
        error = ErrorDetail(
            code="RATE_LIMIT_EXCEEDED",
            message=exc.message,
            details={"retry_after": 3600},  # 1 hour
        )

        logger.warning(
            f"Rate limit exceeded: {exc.message}", extra={"request_id": request_id}
        )

        return ErrorResponse(status_code=429, error=error, request_id=request_id)

    @staticmethod
    def handle_business_logic_error(
        exc: BusinessLogicException, request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Handle business logic errors."""
        error = ErrorDetail(code=exc.code, message=exc.message, field=exc.field)

        logger.info(
            f"Business logic error: {exc.message}",
            extra={"request_id": request_id, "field": exc.field},
        )

        return ErrorResponse(
            status_code=422, error=error, request_id=request_id  # Unprocessable Entity
        )

    @staticmethod
    def handle_external_service_error(
        service_name: str,
        error_message: str,
        status_code: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> ErrorResponse:
        """Handle external service errors."""
        error = ErrorDetail(
            code="EXTERNAL_SERVICE_ERROR",
            message=f"External service error from {service_name}: {error_message}",
            details={
                "service": service_name,
                "original_error": error_message,
                "status_code": status_code,
            },
        )

        logger.error(
            f"External service error from {service_name}: {error_message}",
            extra={"request_id": request_id, "service": service_name},
        )

        return ErrorResponse(
            status_code=502, error=error, request_id=request_id  # Bad Gateway
        )

    @staticmethod
    def handle_database_error(
        operation: str, error_message: str, request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Handle database errors."""
        error = ErrorDetail(
            code="DATABASE_ERROR",
            message="A database error occurred. Please try again later.",
            details={"operation": operation},
        )

        logger.error(
            f"Database error during {operation}: {error_message}",
            extra={"request_id": request_id, "operation": operation},
        )

        return ErrorResponse(status_code=500, error=error, request_id=request_id)

    @staticmethod
    def handle_system_error(
        exc: Exception,
        request_id: Optional[str] = None,
        include_traceback: bool = False,
    ) -> ErrorResponse:
        """Handle unexpected system errors."""
        error_message = "An unexpected error occurred. Please try again later."

        error_details = {"error_type": type(exc).__name__, "error_message": str(exc)}

        if include_traceback:
            error_details["traceback"] = traceback.format_exc()

        error = ErrorDetail(
            code="INTERNAL_SERVER_ERROR", message=error_message, details=error_details
        )

        logger.error(
            f"Unexpected error: {str(exc)}",
            extra={"request_id": request_id, "traceback": traceback.format_exc()},
        )

        return ErrorResponse(status_code=500, error=error, request_id=request_id)


# =============================================================================
# ERROR HANDLING DECORATORS
# =============================================================================


def handle_api_errors(func):
    """Decorator to handle common API errors."""

    def wrapper(*args, **kwargs):
        request_id = kwargs.get("request_id")

        try:
            return func(*args, **kwargs)

        except ValidationException as e:
            return ErrorHandler.handle_validation_error(
                e, request_id
            ).to_azure_response()

        except RateLimitException as e:
            return ErrorHandler.handle_rate_limit_error(
                e, request_id
            ).to_azure_response()

        except BusinessLogicException as e:
            return ErrorHandler.handle_business_logic_error(
                e, request_id
            ).to_azure_response()

        except ValidationError as e:
            return ErrorHandler.handle_validation_error(
                e, request_id
            ).to_azure_response()

        except Exception as e:
            return ErrorHandler.handle_system_error(e, request_id).to_azure_response()

    return wrapper


# =============================================================================
# MONITORING AND ALERTING
# =============================================================================


class ErrorMonitor:
    """Monitor errors for alerting and metrics."""

    @staticmethod
    def record_error(
        error_category: ErrorCategory,
        error_severity: ErrorSeverity,
        error_code: str,
        error_message: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record error for monitoring and alerting."""
        error_data = {
            "category": error_category.value,
            "severity": error_severity.value,
            "code": error_code,
            "message": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "request_id": request_id,
            "context": additional_context or {},
        }

        # Log with appropriate level based on severity
        if error_severity == ErrorSeverity.CRITICAL:
            logger.critical("Critical error occurred", extra=error_data)
        elif error_severity == ErrorSeverity.HIGH:
            logger.warning("High severity error occurred", extra=error_data)
        elif error_severity == ErrorSeverity.MEDIUM:
            logger.warning("Medium severity error occurred", extra=error_data)
        else:
            logger.info("Low severity error occurred", extra=error_data)

        # TODO: In production, send to monitoring service (Application Insights, etc.)
        # This could include:
        # - Custom metrics
        # - Alerts for critical/high severity errors
        # - Error rate monitoring
        # - Performance impact tracking

    @staticmethod
    def should_alert(
        error_category: ErrorCategory, error_severity: ErrorSeverity
    ) -> bool:
        """Determine if error should trigger an alert."""
        # Alert on critical errors or high severity security/auth issues
        if error_severity == ErrorSeverity.CRITICAL:
            return True

        if error_severity == ErrorSeverity.HIGH and error_category in [
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.AUTHORIZATION,
            ErrorCategory.VALIDATION,
            ErrorCategory.EXTERNAL_SERVICE,
        ]:
            return True

        return False


# =============================================================================
# RECOVERY STRATEGIES
# =============================================================================


class ErrorRecovery:
    """Error recovery and retry strategies."""

    @staticmethod
    def should_retry(error_category: ErrorCategory, attempt_count: int) -> bool:
        """Determine if operation should be retried."""
        max_retries = 3

        # Don't retry validation or auth errors
        if error_category in [
            ErrorCategory.VALIDATION,
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.AUTHORIZATION,
            ErrorCategory.BUSINESS_LOGIC,
        ]:
            return False

        # Retry external service and database errors
        if (
            error_category
            in [
                ErrorCategory.EXTERNAL_SERVICE,
                ErrorCategory.DATABASE,
                ErrorCategory.SYSTEM,
            ]
            and attempt_count < max_retries
        ):
            return True

        return False

    @staticmethod
    def get_retry_delay(attempt_count: int) -> float:
        """Get retry delay in seconds with exponential backoff."""
        base_delay = 1.0
        max_delay = 60.0

        delay = min(base_delay * (2**(attempt_count-1)), max_delay)
        return delay

    @staticmethod
    def get_fallback_response(
        error_category: ErrorCategory,
    ) -> Optional[Dict[str, Any]]:
        """Get fallback response for certain error types."""
        if error_category == ErrorCategory.EXTERNAL_SERVICE:
            return {
                "message": "External service temporarily unavailable",
                "fallback": True,
            }

        if error_category == ErrorCategory.DATABASE:
            return {
                "message": "Data temporarily unavailable",
                "fallback": True,
            }

        return None


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def extract_request_id(req: func.HttpRequest) -> Optional[str]:
    """Extract request ID from HTTP request headers or query parameters."""
    # First check headers (preferred)
    request_id = req.headers.get("X-Request-ID") or req.headers.get("x-request-id")
    if request_id:
        return request_id

    # Fallback to query parameters
    return req.params.get("request_id")


def add_correlation_id(
    response_dict: Dict[str, Any], request_id: Optional[str]
) -> Dict[str, Any]:
    """Add correlation ID to response for tracking."""
    if request_id:
        response_dict["request_id"] = request_id
    return response_dict


def is_retriable_error(exc: Exception) -> bool:
    """Check if an exception represents a retriable error."""
    error_message = str(exc).lower()

    # Don't retry validation or business logic errors
    if isinstance(exc, (ValidationException, BusinessLogicException)):
        return False

    # Database connection errors
    if "connection" in error_message:
        return True

    # Timeout errors
    if "timeout" in error_message:
        return True

    # Temporary errors
    if "temporary" in error_message:
        return True

    # Service unavailable
    if "service unavailable" in error_message or "unavailable" in error_message:
        return True

    # HTTP 5xx errors from external services
    if hasattr(exc, "status_code") and 500 <= exc.status_code < 600:
        return True

    return False


def sanitize_error_message(message: str) -> str:
    """Sanitize error message to remove sensitive information."""
    # Remove potential passwords, tokens, keys
    sensitive_patterns = [
        r"password[=:\s]*\S+",
        r"token[=:\s]*\S+",
        r"key[=:\s]*\S+",
        r"secret[=:\s]*\S+",
        r"Bearer\s+\S+",
        r"API_KEY[=:]\S+",
        r"sk-[a-zA-Z0-9\-]+",  # OpenAI style keys
        r"eyJ[a-zA-Z0-9\-_.]+",  # JWT tokens
        r"\b[a-zA-Z0-9]{8,}\b",  # General alphanumeric sequences that could be keys/tokens
    ]

    sanitized = message
    for pattern in sensitive_patterns:
        sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)

    return sanitized
