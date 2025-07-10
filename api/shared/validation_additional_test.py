"""
Additional comprehensive tests for validation utilities.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from api.shared.models import User, UserRole
from api.shared.validation import (
    EMAIL_PATTERN,
    IDENTIFIER_PATTERN,
    MAX_CONTENT_LENGTH,
    MAX_STRING_LENGTH,
    MAX_TAG_LENGTH,
    MAX_TAGS_COUNT,
    SAFE_STRING_PATTERN,
    BusinessLogicException,
    SecurityValidationException,
    ValidationException,
    validate_content,
    validate_json_field,
    validate_pagination_params,
    validate_pydantic_model,
    validate_resource_ownership,
    validate_safe_string,
    validate_search_query,
    validate_user_permissions,
)


class TestBasicValidationFunctions:
    """Test cases for basic validation functions."""

    def test_validate_safe_string_valid(self):
        """Test safe string validation with valid input."""
        test_string = "This is a safe string with numbers 123 and symbols!?"
        result = validate_safe_string(test_string)
        assert result == test_string

    def test_validate_safe_string_too_long(self):
        """Test safe string validation with too long input."""
        long_string = "a" * (MAX_STRING_LENGTH + 1)
        with pytest.raises(ValidationException, match="text too long"):
            validate_safe_string(long_string)

    def test_validate_safe_string_unsafe_characters(self):
        """Test safe string validation with unsafe characters."""
        unsafe_string = "This contains <script>alert('xss')</script>"
        with pytest.raises(SecurityValidationException, match="Potentially dangerous content detected"):
            validate_safe_string(unsafe_string)

    def test_validate_safe_string_custom_max_length(self):
        """Test safe string validation with custom max length."""
        test_string = "a" * 100
        result = validate_safe_string(test_string, max_length=150)
        assert result == test_string

        with pytest.raises(ValidationException):
            validate_safe_string(test_string, max_length=50)

    def test_validate_content_valid(self):
        """Test content validation with valid input."""
        valid_content = "This is valid content with newlines\nand various characters!"
        result = validate_content(valid_content)
        assert result == valid_content

    def test_validate_content_too_long(self):
        """Test content validation with too long input."""
        long_content = "a" * (MAX_CONTENT_LENGTH + 1)
        with pytest.raises(ValidationException, match="content too long"):
            validate_content(long_content)

    def test_validate_content_empty(self):
        """Test content validation with empty input."""
        with pytest.raises(ValidationException, match="content cannot be empty"):
            validate_content("")

        # For whitespace-only content, the function strips it and returns empty string
        result = validate_content("   ")
        assert result == ""  # Whitespace gets stripped

    def test_validate_json_field_valid(self):
        """Test JSON field validation with valid input."""
        valid_json_data = {"key": "value", "number": 123, "array": [1, 2, 3]}
        result = validate_json_field(valid_json_data)
        assert result == valid_json_data

    def test_validate_json_field_none(self):
        """Test JSON field validation with None input."""
        result = validate_json_field(None)
        assert result is None

    def test_validate_json_field_simple_types(self):
        """Test JSON field validation with simple types."""
        assert validate_json_field("string") == "string"
        assert validate_json_field(123) == 123
        assert validate_json_field([1, 2, 3]) == [1, 2, 3]


class TestPaginationValidation:
    """Test cases for pagination validation."""

    def test_validate_pagination_params_valid(self):
        """Test pagination validation with valid parameters."""
        skip, limit = validate_pagination_params(0, 50)
        assert skip == 0
        assert limit == 50

    def test_validate_pagination_params_defaults(self):
        """Test pagination validation with default parameters."""
        skip, limit = validate_pagination_params()
        assert skip == 0
        assert limit == 50

    def test_validate_pagination_params_negative_skip(self):
        """Test pagination validation with negative skip."""
        with pytest.raises(ValidationException, match="Skip parameter must be non-negative"):
            validate_pagination_params(-1, 50)

    def test_validate_pagination_params_zero_limit(self):
        """Test pagination validation with zero limit."""
        with pytest.raises(ValidationException, match="Limit parameter must be positive"):
            validate_pagination_params(0, 0)

    def test_validate_pagination_params_too_large_limit(self):
        """Test pagination validation with too large limit."""
        with pytest.raises(ValidationException, match="Limit parameter too large"):
            validate_pagination_params(0, 101)

    def test_validate_pagination_params_boundary_values(self):
        """Test pagination validation with boundary values."""
        # Test limit = 1 (minimum)
        skip, limit = validate_pagination_params(0, 1)
        assert skip == 0
        assert limit == 1

        # Test limit = 100 (maximum)
        skip, limit = validate_pagination_params(0, 100)
        assert skip == 0
        assert limit == 100


class TestSearchQueryValidation:
    """Test cases for search query validation."""

    def test_validate_search_query_valid(self):
        """Test search query validation with valid input."""
        query = "search terms"
        result = validate_search_query(query)
        assert result == query

    def test_validate_search_query_empty(self):
        """Test search query validation with empty input."""
        # Based on the actual implementation, empty query returns empty string
        result = validate_search_query("")
        assert result == ""

        result = validate_search_query("   ")
        assert result == ""

    def test_validate_search_query_too_long(self):
        """Test search query validation with too long input."""
        long_query = "a" * 201  # Over the 200 character limit
        with pytest.raises(ValidationException, match="Search query too long"):
            validate_search_query(long_query)

    def test_validate_search_query_strip_whitespace(self):
        """Test search query validation strips whitespace."""
        query_with_whitespace = "  search terms  "
        result = validate_search_query(query_with_whitespace)
        assert result == "search terms"


class TestPermissionValidation:
    """Test cases for permission validation."""

    def test_validate_user_permissions_valid(self):
        """Test user permission validation with valid role."""
        user = Mock(spec=User)
        user.role = UserRole.ADMIN

        # Should not raise an exception
        validate_user_permissions(user, UserRole.ADMIN)
        validate_user_permissions(user, UserRole.USER)  # Admin should have user permissions

    def test_validate_user_permissions_insufficient(self):
        """Test user permission validation with insufficient role."""
        user = Mock(spec=User)
        user.role = UserRole.USER

        with pytest.raises(BusinessLogicException, match="Admin privileges required"):
            validate_user_permissions(user, UserRole.ADMIN)

    def test_validate_resource_ownership_owner(self):
        """Test resource ownership validation for resource owner."""
        user_id = "user123"
        resource_user_id = "user123"
        user_roles = [UserRole.USER]

        # Should not raise an exception
        validate_resource_ownership(resource_user_id, user_id, user_roles)

    def test_validate_resource_ownership_admin(self):
        """Test resource ownership validation for admin user."""
        user_id = "admin123"
        resource_user_id = "user123"  # Different user
        user_roles = [UserRole.ADMIN]

        # Should not raise an exception for admin
        validate_resource_ownership(resource_user_id, user_id, user_roles)

    def test_validate_resource_ownership_unauthorized(self):
        """Test resource ownership validation for unauthorized user."""
        user_id = "user123"
        resource_user_id = "user456"  # Different user
        user_roles = [UserRole.USER]

        with pytest.raises(BusinessLogicException, match="Access denied"):
            validate_resource_ownership(resource_user_id, user_id, user_roles)


class TestPydanticModelValidation:
    """Test cases for Pydantic model validation."""

    def test_validate_pydantic_model_valid(self):
        """Test Pydantic model validation with valid data."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            name: str
            age: int

        data = {"name": "John", "age": 30}
        result = validate_pydantic_model(TestModel, data)

        assert isinstance(result, TestModel)
        assert result.name == "John"
        assert result.age == 30

    def test_validate_pydantic_model_invalid(self):
        """Test Pydantic model validation with invalid data."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            name: str
            age: int

        data = {"name": "John", "age": "not_a_number"}

        with pytest.raises(ValidationException, match="Validation failed"):
            validate_pydantic_model(TestModel, data)

    def test_validate_pydantic_model_missing_field(self):
        """Test Pydantic model validation with missing required field."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            name: str
            age: int

        data = {"name": "John"}  # Missing age

        with pytest.raises(ValidationException, match="Validation failed"):
            validate_pydantic_model(TestModel, data)


class TestValidationExceptions:
    """Test cases for validation exception classes."""

    def test_validation_exception(self):
        """Test ValidationException creation."""
        message = "Test validation error"
        exception = ValidationException(message)

        assert str(exception) == message
        assert exception.code == "VALIDATION_ERROR"

    def test_security_validation_exception(self):
        """Test SecurityValidationException creation."""
        message = "Test security error"
        exception = SecurityValidationException(message)

        assert str(exception) == message
        assert exception.code == "SECURITY_VIOLATION"

    def test_business_logic_exception(self):
        """Test BusinessLogicException creation."""
        message = "Test business logic error"
        exception = BusinessLogicException(message)

        assert str(exception) == message
        assert exception.code == "BUSINESS_LOGIC_ERROR"


class TestRegexPatterns:
    """Test cases for regex patterns used in validation."""

    def test_email_pattern_valid(self):
        """Test email regex pattern with valid emails."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "firstname+lastname@company.org",
            "123456@example.com",
        ]

        for email in valid_emails:
            assert EMAIL_PATTERN.match(email), f"Email pattern should match {email}"

    def test_email_pattern_invalid(self):
        """Test email regex pattern with invalid emails."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user@domain",
            "user name@example.com",
        ]

        for email in invalid_emails:
            assert not EMAIL_PATTERN.match(email), f"Email pattern should not match {email}"

    def test_identifier_pattern_valid(self):
        """Test identifier regex pattern with valid identifiers."""
        valid_identifiers = [
            "validIdentifier",
            "test_123",
            "a",
            "camelCase",
            "snake_case_identifier",
        ]

        for identifier in valid_identifiers:
            assert IDENTIFIER_PATTERN.match(identifier), f"Identifier pattern should match {identifier}"

    def test_identifier_pattern_invalid(self):
        """Test identifier regex pattern with invalid identifiers."""
        invalid_identifiers = [
            "123invalid",  # Starts with number
            "invalid identifier",  # Contains space
            "",  # Empty string
            "_invalid",  # Starts with underscore (depending on pattern)
        ]

        for identifier in invalid_identifiers:
            assert not IDENTIFIER_PATTERN.match(identifier), f"Identifier pattern should not match {identifier}"

    def test_safe_string_pattern_valid(self):
        """Test safe string regex pattern with valid strings."""
        valid_strings = [
            "This is a safe string",
            "String with numbers 123",
            "String with punctuation!?().,",
            "String-with_dashes and_underscores",
        ]

        for string in valid_strings:
            assert SAFE_STRING_PATTERN.match(string), f"Safe string pattern should match '{string}'"

    def test_safe_string_pattern_invalid(self):
        """Test safe string regex pattern with invalid strings."""
        invalid_strings = [
            "<script>alert('xss')</script>",
            "String with & ampersand",
            "String with % percent",
            "String with @ at symbol",
        ]

        for string in invalid_strings:
            assert not SAFE_STRING_PATTERN.match(string), f"Safe string pattern should not match '{string}'"
