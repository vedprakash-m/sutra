"""
Input Validation and Security Middleware
Comprehensive input validation, sanitization, and security checks
"""

import hashlib
import html
import json
import logging
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

import azure.functions as func
from azure.cosmos import exceptions as cosmos_exceptions

# Set up logging
logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar("T")


class ValidationError(Exception):
    """Custom exception for validation errors"""

    def __init__(self, message: str, field: str = None, code: str = None):
        super().__init__(message)
        self.field = field
        self.code = code
        self.message = message


class SecurityLevel(Enum):
    """Security validation levels"""

    BASIC = "basic"
    MODERATE = "moderate"
    STRICT = "strict"
    PARANOID = "paranoid"


@dataclass
class ValidationRule:
    """Individual validation rule"""

    name: str
    validator: Callable[[Any], bool]
    message: str
    required: bool = False
    sanitizer: Optional[Callable[[Any], Any]] = None


@dataclass
class SecurityConfig:
    """Security configuration"""

    level: SecurityLevel = SecurityLevel.MODERATE
    max_input_length: int = 10000
    allowed_html_tags: List[str] = None
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    csrf_protection: bool = True
    sql_injection_protection: bool = True
    xss_protection: bool = True
    log_all_requests: bool = True


class InputValidator:
    """Comprehensive input validation system"""

    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self.rate_limit_store = {}  # In production, use Redis
        self.csrf_tokens = {}  # In production, use secure storage

        # Common validation patterns
        self.patterns = {
            "email": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
            "alphanumeric": re.compile(r"^[a-zA-Z0-9_-]+$"),
            "uuid": re.compile(r"^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$"),
            "safe_string": re.compile(r'^[a-zA-Z0-9\s\.\-_,;:!?\'"()]+$'),
            "sql_injection": re.compile(
                r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|SCRIPT)\b|--|\'|"|;|\*|%|\\)',
                re.IGNORECASE,
            ),
            "xss_patterns": re.compile(
                r"(<script|<iframe|<object|<embed|javascript:|vbscript:|onload=|onerror=|onclick=)", re.IGNORECASE
            ),
        }

        # Initialize allowed HTML tags
        if self.config.allowed_html_tags is None:
            self.config.allowed_html_tags = ["b", "i", "em", "strong", "p", "br", "ul", "ol", "li"]

    def validate_string(
        self, value: str, min_length: int = 0, max_length: int = None, pattern: str = None, required: bool = False
    ) -> str:
        """Validate and sanitize string input"""
        if value is None:
            if required:
                raise ValidationError("Field is required", code="REQUIRED")
            return ""

        if not isinstance(value, str):
            value = str(value)

        # Check length constraints
        if len(value) < min_length:
            raise ValidationError(f"Minimum length is {min_length}", code="MIN_LENGTH")

        max_len = max_length or self.config.max_input_length
        if len(value) > max_len:
            raise ValidationError(f"Maximum length is {max_len}", code="MAX_LENGTH")

        # Check pattern if provided
        if pattern and pattern in self.patterns:
            if not self.patterns[pattern].match(value):
                raise ValidationError(f"Invalid format for {pattern}", code="INVALID_FORMAT")

        # Security checks
        if self.config.sql_injection_protection:
            self._check_sql_injection(value)

        if self.config.xss_protection:
            value = self._sanitize_xss(value)

        return value.strip()

    def validate_email(self, email: str, required: bool = False) -> str:
        """Validate email address"""
        if not email:
            if required:
                raise ValidationError("Email is required", field="email", code="REQUIRED")
            return ""

        email = email.strip().lower()
        if not self.patterns["email"].match(email):
            raise ValidationError("Invalid email format", field="email", code="INVALID_EMAIL")

        return email

    def validate_integer(self, value: Any, min_val: int = None, max_val: int = None, required: bool = False) -> Optional[int]:
        """Validate integer input"""
        if value is None:
            if required:
                raise ValidationError("Field is required", code="REQUIRED")
            return None

        try:
            int_val = int(value)
        except (ValueError, TypeError):
            raise ValidationError("Must be a valid integer", code="INVALID_INTEGER")

        if min_val is not None and int_val < min_val:
            raise ValidationError(f"Minimum value is {min_val}", code="MIN_VALUE")

        if max_val is not None and int_val > max_val:
            raise ValidationError(f"Maximum value is {max_val}", code="MAX_VALUE")

        return int_val

    def validate_float(
        self, value: Any, min_val: float = None, max_val: float = None, required: bool = False
    ) -> Optional[float]:
        """Validate float input"""
        if value is None:
            if required:
                raise ValidationError("Field is required", code="REQUIRED")
            return None

        try:
            float_val = float(value)
        except (ValueError, TypeError):
            raise ValidationError("Must be a valid number", code="INVALID_FLOAT")

        if min_val is not None and float_val < min_val:
            raise ValidationError(f"Minimum value is {min_val}", code="MIN_VALUE")

        if max_val is not None and float_val > max_val:
            raise ValidationError(f"Maximum value is {max_val}", code="MAX_VALUE")

        return float_val

    def validate_boolean(self, value: Any, required: bool = False) -> Optional[bool]:
        """Validate boolean input"""
        if value is None:
            if required:
                raise ValidationError("Field is required", code="REQUIRED")
            return None

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            value = value.lower()
            if value in ("true", "1", "yes", "on"):
                return True
            elif value in ("false", "0", "no", "off"):
                return False

        if isinstance(value, (int, float)):
            return bool(value)

        raise ValidationError("Must be a valid boolean", code="INVALID_BOOLEAN")

    def validate_uuid(self, value: str, required: bool = False) -> Optional[str]:
        """Validate UUID format"""
        if not value:
            if required:
                raise ValidationError("UUID is required", code="REQUIRED")
            return None

        if not isinstance(value, str):
            value = str(value)

        if not self.patterns["uuid"].match(value):
            raise ValidationError("Invalid UUID format", code="INVALID_UUID")

        return value

    def validate_list(
        self, value: Any, item_validator: Callable = None, min_items: int = 0, max_items: int = None, required: bool = False
    ) -> List[Any]:
        """Validate list input"""
        if value is None:
            if required:
                raise ValidationError("List is required", code="REQUIRED")
            return []

        if not isinstance(value, list):
            raise ValidationError("Must be a list", code="INVALID_LIST")

        if len(value) < min_items:
            raise ValidationError(f"Minimum {min_items} items required", code="MIN_ITEMS")

        if max_items and len(value) > max_items:
            raise ValidationError(f"Maximum {max_items} items allowed", code="MAX_ITEMS")

        # Validate each item if validator provided
        if item_validator:
            validated_items = []
            for i, item in enumerate(value):
                try:
                    validated_items.append(item_validator(item))
                except ValidationError as e:
                    raise ValidationError(f"Item {i}: {e.message}", code="INVALID_ITEM")
            return validated_items

        return value

    def validate_dict(self, value: Any, schema: Dict[str, ValidationRule] = None, required: bool = False) -> Dict[str, Any]:
        """Validate dictionary input against schema"""
        if value is None:
            if required:
                raise ValidationError("Object is required", code="REQUIRED")
            return {}

        if not isinstance(value, dict):
            try:
                value = json.loads(value) if isinstance(value, str) else dict(value)
            except (json.JSONDecodeError, ValueError, TypeError):
                raise ValidationError("Must be a valid object", code="INVALID_DICT")

        if not schema:
            return value

        validated_data = {}

        # Validate each field in schema
        for field_name, rule in schema.items():
            field_value = value.get(field_name)

            try:
                if field_value is None and rule.required:
                    raise ValidationError(f"Field '{field_name}' is required", field=field_name, code="REQUIRED")

                if field_value is not None:
                    # Apply sanitizer if provided
                    if rule.sanitizer:
                        field_value = rule.sanitizer(field_value)

                    # Apply validator
                    if not rule.validator(field_value):
                        raise ValidationError(rule.message, field=field_name, code="VALIDATION_FAILED")

                validated_data[field_name] = field_value
            except ValidationError as e:
                e.field = field_name
                raise e

        # Check for unexpected fields
        unexpected_fields = set(value.keys()) - set(schema.keys())
        if unexpected_fields and self.config.level in [SecurityLevel.STRICT, SecurityLevel.PARANOID]:
            raise ValidationError(f"Unexpected fields: {', '.join(unexpected_fields)}", code="UNEXPECTED_FIELDS")

        return validated_data

    def _check_sql_injection(self, value: str) -> None:
        """Check for SQL injection patterns"""
        if self.patterns["sql_injection"].search(value):
            logger.warning(f"Potential SQL injection attempt detected: {value[:100]}")
            raise ValidationError("Invalid characters detected", code="SECURITY_VIOLATION")

    def _sanitize_xss(self, value: str) -> str:
        """Sanitize potential XSS content"""
        # Check for dangerous patterns
        if self.patterns["xss_patterns"].search(value):
            logger.warning(f"Potential XSS attempt detected: {value[:100]}")

        # HTML escape the content
        value = html.escape(value)

        return value

    def generate_csrf_token(self, user_id: str) -> str:
        """Generate CSRF token for user"""
        if not self.config.csrf_protection:
            return ""

        token = secrets.token_urlsafe(32)
        self.csrf_tokens[user_id] = {
            "token": token,
            "created": datetime.utcnow(),
            "expires": datetime.utcnow() + timedelta(hours=24),
        }
        return token

    def validate_csrf_token(self, user_id: str, token: str) -> bool:
        """Validate CSRF token"""
        if not self.config.csrf_protection:
            return True

        stored_token = self.csrf_tokens.get(user_id)
        if not stored_token:
            return False

        if stored_token["expires"] < datetime.utcnow():
            del self.csrf_tokens[user_id]
            return False

        return secrets.compare_digest(stored_token["token"], token)

    def check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limits"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.config.rate_limit_window)

        if identifier not in self.rate_limit_store:
            self.rate_limit_store[identifier] = []

        # Clean old requests
        self.rate_limit_store[identifier] = [
            req_time for req_time in self.rate_limit_store[identifier] if req_time > window_start
        ]

        # Check if within limit
        if len(self.rate_limit_store[identifier]) >= self.config.rate_limit_requests:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return False

        # Add current request
        self.rate_limit_store[identifier].append(now)
        return True


# Global validator instance
validator = InputValidator()


def validate_request(schema: Dict[str, ValidationRule] = None, csrf_required: bool = False, rate_limit: bool = True):
    """Decorator for validating Azure Function requests"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(req: func.HttpRequest) -> func.HttpResponse:
            try:
                # Get client identifier for rate limiting
                client_ip = req.headers.get("X-Forwarded-For", "unknown")
                user_id = req.headers.get("X-User-ID", client_ip)

                # Rate limiting check
                if rate_limit and not validator.check_rate_limit(user_id):
                    return func.HttpResponse(
                        json.dumps({"error": "Rate limit exceeded", "code": "RATE_LIMIT"}),
                        status_code=429,
                        headers={"Content-Type": "application/json"},
                    )

                # CSRF token validation
                if csrf_required:
                    csrf_token = req.headers.get("X-CSRF-Token")
                    if not validator.validate_csrf_token(user_id, csrf_token):
                        return func.HttpResponse(
                            json.dumps({"error": "Invalid CSRF token", "code": "CSRF_INVALID"}),
                            status_code=403,
                            headers={"Content-Type": "application/json"},
                        )

                # Request body validation
                validated_data = {}
                if schema and req.method in ["POST", "PUT", "PATCH"]:
                    try:
                        body = req.get_json()
                        validated_data = validator.validate_dict(body, schema, required=True)
                    except ValueError:
                        return func.HttpResponse(
                            json.dumps({"error": "Invalid JSON", "code": "INVALID_JSON"}),
                            status_code=400,
                            headers={"Content-Type": "application/json"},
                        )
                    except ValidationError as e:
                        return func.HttpResponse(
                            json.dumps({"error": e.message, "field": e.field, "code": e.code or "VALIDATION_ERROR"}),
                            status_code=400,
                            headers={"Content-Type": "application/json"},
                        )

                # Add validated data to request
                req._validated_data = validated_data

                # Call the original function
                return await func(req)

            except ValidationError as e:
                logger.error(f"Validation error: {e.message}")
                return func.HttpResponse(
                    json.dumps({"error": e.message, "field": e.field, "code": e.code or "VALIDATION_ERROR"}),
                    status_code=400,
                    headers={"Content-Type": "application/json"},
                )
            except Exception as e:
                logger.error(f"Unexpected error in validation: {str(e)}")
                return func.HttpResponse(
                    json.dumps({"error": "Internal server error", "code": "INTERNAL_ERROR"}),
                    status_code=500,
                    headers={"Content-Type": "application/json"},
                )

        return wrapper

    return decorator


# Common validation schemas
PROMPT_SCHEMA = {
    "title": ValidationRule(
        name="title",
        validator=lambda x: isinstance(x, str) and 1 <= len(x.strip()) <= 200,
        message="Title must be 1-200 characters",
        required=True,
        sanitizer=lambda x: validator.validate_string(x, min_length=1, max_length=200),
    ),
    "content": ValidationRule(
        name="content",
        validator=lambda x: isinstance(x, str) and 1 <= len(x.strip()) <= 50000,
        message="Content must be 1-50000 characters",
        required=True,
        sanitizer=lambda x: validator.validate_string(x, min_length=1, max_length=50000),
    ),
    "tags": ValidationRule(
        name="tags",
        validator=lambda x: isinstance(x, list) and all(isinstance(tag, str) for tag in x),
        message="Tags must be a list of strings",
        required=False,
        sanitizer=lambda x: validator.validate_list(
            x, item_validator=lambda tag: validator.validate_string(tag, max_length=50)
        ),
    ),
    "variables": ValidationRule(
        name="variables", validator=lambda x: isinstance(x, dict), message="Variables must be an object", required=False
    ),
}

COLLECTION_SCHEMA = {
    "name": ValidationRule(
        name="name",
        validator=lambda x: isinstance(x, str) and 1 <= len(x.strip()) <= 100,
        message="Name must be 1-100 characters",
        required=True,
        sanitizer=lambda x: validator.validate_string(x, min_length=1, max_length=100),
    ),
    "description": ValidationRule(
        name="description",
        validator=lambda x: isinstance(x, str) and len(x.strip()) <= 1000,
        message="Description must be less than 1000 characters",
        required=False,
        sanitizer=lambda x: validator.validate_string(x, max_length=1000),
    ),
    "is_public": ValidationRule(
        name="is_public",
        validator=lambda x: isinstance(x, bool),
        message="is_public must be a boolean",
        required=False,
        sanitizer=lambda x: validator.validate_boolean(x),
    ),
}
