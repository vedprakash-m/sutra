"""
Comprehensive tests for validation module to achieve 80% coverage.
Focuses on missing coverage areas: PromptTemplateValidator, CollectionValidator,
PlaybookValidator, RateLimitValidator, and business logic validators.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from api.shared.validation import (
    # Core validation functions
    validate_identifier,
    validate_safe_string,
    validate_content,
    validate_tags,
    validate_json_field,
    validate_pagination_params,
    validate_search_query,

    # Model validators
    PromptTemplateValidator,
    CollectionValidator,
    PlaybookValidator,
    RateLimitValidator,

    # Business logic validators
    validate_user_permissions,
    validate_resource_ownership,
    validate_budget_limits,
    validate_pydantic_model,
    validate_execution_input,
    _validate_playbook_step,

    # Exceptions
    ValidationException,
    SecurityValidationException,
    BusinessLogicException,
    RateLimitException,

    # Constants
    MAX_STRING_LENGTH,
    MAX_CONTENT_LENGTH,
    MAX_VARIABLES_COUNT,
    MAX_STEPS_COUNT,
    MAX_TAGS_COUNT,
    MAX_TAG_LENGTH,
    MAX_DESCRIPTION_LENGTH,
)

from api.shared.models import User, UserRole, PromptTemplate, PromptStatus


class TestPromptTemplateValidator:
    """Comprehensive tests for PromptTemplateValidator."""

    def test_validate_create_request_success(self):
        """Test successful prompt template creation validation."""
        data = {
            "title": "Test Prompt",
            "content": "This is test content with {{variable}}",
            "description": "Test description",
            "tags": ["test", "validation"],
            "variables": [
                {
                    "name": "variable",
                    "description": "Test variable",
                    "type": "string",
                    "required": True,
                    "default_value": "default"
                }
            ]
        }
        user_id = "test-user-123"

        result = PromptTemplateValidator.validate_create_request(data, user_id)

        assert result["title"] == "Test Prompt"
        assert result["content"] == "This is test content with {{variable}}"
        assert result["description"] == "Test description"
        assert result["tags"] == ["test", "validation"]
        assert result["user_id"] == user_id
        assert result["status"] == PromptStatus.DRAFT
        assert len(result["variables"]) == 1
        assert result["variables"][0]["name"] == "variable"

    def test_validate_create_request_missing_title(self):
        """Test validation with missing title."""
        data = {"content": "Test content"}
        user_id = "test-user"

        with pytest.raises(ValidationException, match="Title is required"):
            PromptTemplateValidator.validate_create_request(data, user_id)

    def test_validate_create_request_empty_title(self):
        """Test validation with empty title."""
        data = {"title": "", "content": "Test content"}
        user_id = "test-user"

        with pytest.raises(ValidationException, match="Title is required"):
            PromptTemplateValidator.validate_create_request(data, user_id)

    def test_validate_create_request_too_many_variables(self):
        """Test validation with too many variables."""
        variables = [{"name": f"var{i}", "type": "string"} for i in range(MAX_VARIABLES_COUNT + 1)]
        data = {
            "title": "Test",
            "content": "Test content",
            "variables": variables
        }
        user_id = "test-user"

        with pytest.raises(ValidationException, match="Too many variables"):
            PromptTemplateValidator.validate_create_request(data, user_id)

    def test_validate_create_request_invalid_variable_type(self):
        """Test validation with invalid variable type."""
        data = {
            "title": "Test",
            "content": "Test content",
            "variables": [
                {
                    "name": "test_var",
                    "type": "invalid_type",
                    "description": "Test"
                }
            ]
        }
        user_id = "test-user"

        with pytest.raises(ValidationException, match="Invalid variable type"):
            PromptTemplateValidator.validate_create_request(data, user_id)

    def test_validate_create_request_invalid_variable_name(self):
        """Test validation with invalid variable name."""
        data = {
            "title": "Test",
            "content": "Test content",
            "variables": [
                {
                    "name": "123invalid",  # Can't start with number
                    "type": "string"
                }
            ]
        }
        user_id = "test-user"

        with pytest.raises(ValidationException):
            PromptTemplateValidator.validate_create_request(data, user_id)

    def test_validate_create_request_variable_not_dict(self):
        """Test validation with variable that's not a dictionary."""
        data = {
            "title": "Test",
            "content": "Test content",
            "variables": ["not_a_dict"]
        }
        user_id = "test-user"

        with pytest.raises(ValidationException, match="Variable 0 must be an object"):
            PromptTemplateValidator.validate_create_request(data, user_id)

    def test_validate_update_request_success(self):
        """Test successful prompt template update validation."""
        existing_prompt = Mock(spec=PromptTemplate)
        data = {
            "title": "Updated Title",
            "description": "Updated description",
            "content": "Updated content",
            "tags": ["updated"],
            "status": "active",
            "variables": [
                {
                    "name": "new_var",
                    "type": "string",
                    "description": "New variable",
                    "required": False,
                    "default_value": "test"
                }
            ]
        }

        result = PromptTemplateValidator.validate_update_request(data, existing_prompt)

        assert result["title"] == "Updated Title"
        assert result["description"] == "Updated description"
        assert result["content"] == "Updated content"
        assert result["tags"] == ["updated"]
        assert result["status"] == "active"
        assert len(result["variables"]) == 1

    def test_validate_update_request_invalid_status(self):
        """Test update validation with invalid status."""
        existing_prompt = Mock(spec=PromptTemplate)
        data = {"status": "invalid_status"}

        with pytest.raises(ValidationException, match="Invalid status"):
            PromptTemplateValidator.validate_update_request(data, existing_prompt)

    def test_validate_update_request_partial_fields(self):
        """Test update validation with only some fields."""
        existing_prompt = Mock(spec=PromptTemplate)
        data = {"title": "New Title"}

        result = PromptTemplateValidator.validate_update_request(data, existing_prompt)

        assert result["title"] == "New Title"
        assert "description" not in result  # Only updated fields included

    def test_validate_update_request_variables_validation(self):
        """Test update validation with invalid variables."""
        existing_prompt = Mock(spec=PromptTemplate)
        data = {
            "variables": [
                {
                    "name": "123invalid",  # Invalid name
                    "type": "string"
                }
            ]
        }

        with pytest.raises(ValidationException):
            PromptTemplateValidator.validate_update_request(data, existing_prompt)

    def test_validate_update_request_too_many_variables(self):
        """Test update validation with too many variables."""
        existing_prompt = Mock(spec=PromptTemplate)
        variables = [{"name": f"var{i}", "type": "string"} for i in range(MAX_VARIABLES_COUNT + 1)]
        data = {"variables": variables}

        with pytest.raises(ValidationException, match="Too many variables"):
            PromptTemplateValidator.validate_update_request(data, existing_prompt)


class TestCollectionValidator:
    """Comprehensive tests for CollectionValidator."""

    def test_validate_create_request_success(self):
        """Test successful collection creation validation."""
        data = {
            "name": "Test Collection",
            "description": "Test description",
            "tags": ["test", "collection"],
            "is_public": True,
            "prompt_ids": ["prompt1", "prompt2"]
        }
        user_id = "test-user-123"

        result = CollectionValidator.validate_create_request(data, user_id)

        assert result["name"] == "Test Collection"
        assert result["description"] == "Test description"
        assert result["tags"] == ["test", "collection"]
        assert result["is_public"] is True
        assert result["prompt_ids"] == ["prompt1", "prompt2"]
        assert result["user_id"] == user_id

    def test_validate_create_request_missing_name(self):
        """Test validation with missing name."""
        data = {"description": "Test"}
        user_id = "test-user"

        with pytest.raises(ValidationException, match="Name is required"):
            CollectionValidator.validate_create_request(data, user_id)

    def test_validate_create_request_empty_name(self):
        """Test validation with empty name."""
        data = {"name": ""}
        user_id = "test-user"

        with pytest.raises(ValidationException, match="Name is required"):
            CollectionValidator.validate_create_request(data, user_id)

    def test_validate_create_request_invalid_prompt_ids(self):
        """Test validation with invalid prompt_ids."""
        data = {
            "name": "Test Collection",
            "prompt_ids": "not_a_list"  # Should be list
        }
        user_id = "test-user"

        with pytest.raises(ValidationException, match="prompt_ids must be a list"):
            CollectionValidator.validate_create_request(data, user_id)

    def test_validate_create_request_filters_prompt_ids(self):
        """Test that invalid prompt IDs are filtered out."""
        data = {
            "name": "Test Collection",
            "prompt_ids": ["valid-id", "", None, "  ", "another-valid-id"]
        }
        user_id = "test-user"

        result = CollectionValidator.validate_create_request(data, user_id)

        # Should filter out empty/None values
        assert result["prompt_ids"] == ["valid-id", "another-valid-id"]

    def test_validate_create_request_defaults(self):
        """Test validation with default values."""
        data = {"name": "Minimal Collection"}
        user_id = "test-user"

        result = CollectionValidator.validate_create_request(data, user_id)

        assert result["name"] == "Minimal Collection"
        assert result["description"] == ""
        assert result["tags"] == []
        assert result["is_public"] is False
        assert result["prompt_ids"] == []


class TestPlaybookValidator:
    """Comprehensive tests for PlaybookValidator."""

    def test_validate_create_request_success(self):
        """Test successful playbook creation validation."""
        data = {
            "name": "Test Playbook",
            "description": "Test description",
            "tags": ["test", "playbook"],
            "steps": [
                {
                    "type": "prompt",
                    "stepId": "step1",
                    "promptId": "prompt-123",
                    "config": {
                        "temperature": 0.7,
                        "maxTokens": 1000
                    }
                },
                {
                    "type": "manual_review",
                    "stepId": "review1"
                }
            ]
        }
        user_id = "test-user-123"

        result = PlaybookValidator.validate_create_request(data, user_id)

        assert result["name"] == "Test Playbook"
        assert result["description"] == "Test description"
        assert result["tags"] == ["test", "playbook"]

    def test_validate_create_request_missing_name(self):
        """Test validation with missing name."""
        data = {"steps": [{"type": "prompt"}]}
        user_id = "test-user"

        with pytest.raises(ValidationException, match="Name is required"):
            PlaybookValidator.validate_create_request(data, user_id)


class TestPlaybookStepValidation:
    """Tests for _validate_playbook_step function."""

    def test_validate_step_missing_type(self):
        """Test step validation with missing type."""
        step = {"stepId": "test"}

        errors = _validate_playbook_step(step, 0)

        assert len(errors) > 0
        assert any("Step type is required" in error for error in errors)

    def test_validate_step_invalid_type(self):
        """Test step validation with invalid type."""
        step = {"type": "invalid_type"}

        errors = _validate_playbook_step(step, 0)

        assert len(errors) > 0
        assert any("Invalid step type" in error for error in errors)

    def test_validate_step_invalid_step_id(self):
        """Test step validation with invalid step ID."""
        step = {
            "type": "prompt",
            "stepId": "123invalid"  # Can't start with number
        }

        errors = _validate_playbook_step(step, 0)

        assert len(errors) > 0
        assert any("Invalid step ID format" in error for error in errors)

    def test_validate_prompt_step_missing_prompt(self):
        """Test prompt step validation without prompt reference."""
        step = {"type": "prompt"}

        errors = _validate_playbook_step(step, 0)

        assert len(errors) > 0
        assert any("must have either promptId or promptText" in error for error in errors)

    def test_validate_prompt_step_invalid_temperature(self):
        """Test prompt step with invalid temperature."""
        step = {
            "type": "prompt",
            "promptId": "test",
            "config": {"temperature": 3.0}  # Too high
        }

        errors = _validate_playbook_step(step, 0)

        assert len(errors) > 0
        assert any("Temperature must be between 0 and 2" in error for error in errors)

    def test_validate_prompt_step_invalid_max_tokens(self):
        """Test prompt step with invalid max tokens."""
        step = {
            "type": "prompt",
            "promptId": "test",
            "config": {"maxTokens": 20000}  # Too high
        }

        errors = _validate_playbook_step(step, 0)

        assert len(errors) > 0
        assert any("Max tokens must be between 1 and 10000" in error for error in errors)

    def test_validate_step_invalid_parsing_rules(self):
        """Test step with invalid output parsing rules."""
        step = {
            "type": "prompt",
            "promptId": "test",
            "outputParsingRules": "not_a_dict"  # Should be dict
        }

        errors = _validate_playbook_step(step, 0)

        assert len(errors) > 0
        assert any("Output parsing rules must be a dictionary" in error for error in errors)

    def test_validate_step_invalid_regex(self):
        """Test step with invalid regex pattern."""
        step = {
            "type": "prompt",
            "promptId": "test",
            "outputParsingRules": {
                "regex": "[invalid regex"  # Invalid regex
            }
        }

        errors = _validate_playbook_step(step, 0)

        assert len(errors) > 0
        assert any("Invalid regex pattern" in error for error in errors)

    def test_validate_step_success(self):
        """Test successful step validation."""
        step = {
            "type": "prompt",
            "stepId": "valid_step",
            "promptId": "test-prompt",
            "config": {
                "temperature": 0.7,
                "maxTokens": 1000
            },
            "outputParsingRules": {
                "regex": r"\d+"
            }
        }

        errors = _validate_playbook_step(step, 0)

        assert len(errors) == 0

    def test_validate_step_prompt_with_text(self):
        """Test prompt step with promptText instead of promptId."""
        step = {
            "type": "prompt",
            "promptText": "This is prompt text"
        }

        errors = _validate_playbook_step(step, 0)

        assert len(errors) == 0

    def test_validate_step_all_types(self):
        """Test validation for all valid step types."""
        valid_types = ["prompt", "manual_review", "condition", "loop"]

        for step_type in valid_types:
            step = {"type": step_type}
            if step_type == "prompt":
                step["promptId"] = "test"

            errors = _validate_playbook_step(step, 0)
            # Should not have type errors
            assert not any("Invalid step type" in error for error in errors)


class TestRateLimitValidator:
    """Tests for RateLimitValidator."""

    def test_check_rate_limit_within_limit(self):
        """Test rate limit check when within limit."""
        # Should not raise exception
        RateLimitValidator.check_rate_limit("user123", "prompt_executions", 500)

    def test_check_rate_limit_exceeded(self):
        """Test rate limit check when limit exceeded."""
        with pytest.raises(RateLimitException, match="Rate limit exceeded"):
            RateLimitValidator.check_rate_limit("user123", "prompt_executions", 1001)

    def test_check_rate_limit_unknown_operation(self):
        """Test rate limit check for unknown operation type (uses default)."""
        # Unknown operation type gets default limit of 100
        with pytest.raises(RateLimitException):
            RateLimitValidator.check_rate_limit("user123", "unknown_operation", 101)

    def test_check_rate_limit_edge_case(self):
        """Test rate limit check at exact limit."""
        # Just under limit should pass
        RateLimitValidator.check_rate_limit("user123", "prompt_executions", 999)

        # At exact limit should fail (because it uses >=)
        with pytest.raises(RateLimitException):
            RateLimitValidator.check_rate_limit("user123", "prompt_executions", 1000)

    def test_rate_limits_configuration(self):
        """Test that all expected rate limits are configured."""
        expected_operations = [
            "prompt_executions",
            "prompt_creations",
            "collection_operations",
            "playbook_executions",
            "admin_operations"
        ]

        for operation in expected_operations:
            assert operation in RateLimitValidator.RATE_LIMITS
            assert isinstance(RateLimitValidator.RATE_LIMITS[operation], int)
            assert RateLimitValidator.RATE_LIMITS[operation] > 0


class TestBusinessLogicValidators:
    """Tests for business logic validation functions."""

    def test_validate_user_permissions_admin_required_has_admin(self):
        """Test user permission validation when admin required and user has admin."""
        user = Mock(spec=User)
        user.roles = [UserRole.ADMIN, UserRole.USER]

        # Should not raise exception
        validate_user_permissions(user, UserRole.ADMIN)

    def test_validate_user_permissions_admin_required_no_admin(self):
        """Test user permission validation when admin required but user doesn't have admin."""
        user = Mock(spec=User)
        user.roles = [UserRole.USER]

        with pytest.raises(BusinessLogicException, match="Admin privileges required"):
            validate_user_permissions(user, UserRole.ADMIN)

    def test_validate_user_permissions_user_role(self):
        """Test user permission validation for user role."""
        user = Mock(spec=User)
        user.roles = [UserRole.USER]

        # Should not raise exception
        validate_user_permissions(user, UserRole.USER)

    def test_validate_resource_ownership_owner(self):
        """Test resource ownership validation for resource owner."""
        validate_resource_ownership("user123", "user123", [UserRole.USER])

    def test_validate_resource_ownership_admin(self):
        """Test resource ownership validation for admin user."""
        validate_resource_ownership("user123", "admin456", [UserRole.ADMIN])

    def test_validate_resource_ownership_unauthorized(self):
        """Test resource ownership validation for unauthorized user."""
        with pytest.raises(BusinessLogicException, match="Access denied"):
            validate_resource_ownership("user123", "user456", [UserRole.USER])

    def test_validate_budget_limits_non_numeric(self):
        """Test budget validation with non-numeric values."""
        with pytest.raises(ValidationException, match="Budget values must be numeric"):
            validate_budget_limits({"total_budget": "not_a_number", "usage_limit": 100})

    def test_validate_budget_limits_current_usage_non_numeric(self):
        """Test budget validation with non-numeric current usage."""
        with pytest.raises(ValidationException, match="Budget values must be numeric"):
            validate_budget_limits({"current_usage": "invalid", "budget_limit": 100})

    def test_validate_budget_limits_success_cases(self):
        """Test successful budget validation cases."""
        # Both total_budget and usage_limit
        result = validate_budget_limits({"total_budget": 100.0, "usage_limit": 50.0})
        assert result is True

        # Both current_usage and budget_limit
        result = validate_budget_limits({"current_usage": 50.0, "budget_limit": 100.0})
        assert result is True

        # Neither combination (should pass)
        result = validate_budget_limits({"some_other_field": 123})
        assert result is True


class TestExecutionInputValidation:
    """Tests for validate_execution_input function."""

    def test_validate_execution_input_success(self):
        """Test successful execution input validation."""
        data = {
            "initialInputs": {
                "var1": "value1",
                "var2": "value2",
                "var3": 123
            }
        }

        result = validate_execution_input(data)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_execution_input_not_dict(self):
        """Test execution input validation when initialInputs is not a dict."""
        data = {"initialInputs": "not_a_dict"}

        result = validate_execution_input(data)

        assert result["valid"] is False
        assert any("Initial inputs must be a dictionary" in error for error in result["errors"])

    def test_validate_execution_input_invalid_variable_name(self):
        """Test execution input validation with invalid variable name."""
        data = {
            "initialInputs": {
                "123invalid": "value",  # Can't start with number
                "valid_var": "value"
            }
        }

        result = validate_execution_input(data)

        assert result["valid"] is False
        assert any("Invalid variable name '123invalid'" in error for error in result["errors"])

    def test_validate_execution_input_value_too_long(self):
        """Test execution input validation with value too long."""
        long_value = "a" * (MAX_CONTENT_LENGTH + 1)
        data = {
            "initialInputs": {
                "test_var": long_value
            }
        }

        result = validate_execution_input(data)

        assert result["valid"] is False
        assert any("value is too long" in error for error in result["errors"])

    def test_validate_execution_input_empty(self):
        """Test execution input validation with empty data."""
        result = validate_execution_input({})

        assert result["valid"] is True
        assert len(result["errors"]) == 0


class TestCoreValidationEdgeCases:
    """Tests for core validation functions edge cases."""

    def test_validate_identifier_empty(self):
        """Test identifier validation with empty string."""
        with pytest.raises(ValidationException, match="cannot be empty"):
            validate_identifier("")

    def test_validate_identifier_too_long(self):
        """Test identifier validation with too long string."""
        long_id = "a" * 101
        with pytest.raises(ValidationException, match="too long"):
            validate_identifier(long_id)

    def test_validate_safe_string_dangerous_patterns(self):
        """Test safe string validation with various dangerous patterns."""
        dangerous_strings = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "data:text/html,<script>alert(1)</script>",
            "vbscript:alert('xss')",
            "onload=alert('xss')",
            "onerror=alert('xss')",
            "onclick=alert('xss')",
        ]

        for dangerous_string in dangerous_strings:
            with pytest.raises(SecurityValidationException, match="Potentially dangerous content detected"):
                validate_safe_string(dangerous_string)

    def test_validate_safe_string_empty_input(self):
        """Test safe string validation with empty input."""
        result = validate_safe_string("")
        assert result == ""

        result = validate_safe_string(None)
        assert result is None

    def test_validate_content_script_injection(self):
        """Test content validation with script injection attempts."""
        dangerous_content = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "data:text/html,<script>alert(1)</script>",
            "vbscript:alert('xss')",
        ]

        for content in dangerous_content:
            with pytest.raises(SecurityValidationException, match="Script injection detected"):
                validate_content(content)

    def test_validate_tags_too_many(self):
        """Test tag validation with too many tags."""
        too_many_tags = [f"tag{i}" for i in range(MAX_TAGS_COUNT + 1)]

        with pytest.raises(ValidationException, match="Too many tags"):
            validate_tags(too_many_tags)

    def test_validate_tags_tag_too_long(self):
        """Test tag validation with tag too long."""
        long_tag = "a" * (MAX_TAG_LENGTH + 1)

        with pytest.raises(ValidationException, match="Tag too long"):
            validate_tags([long_tag])

    def test_validate_tags_edge_cases(self):
        """Test tag validation edge cases."""
        # Test with empty list
        result = validate_tags([])
        assert result == []

        # Test that empty/None entries are skipped
        result = validate_tags(["valid123"])
        assert result == ["valid123"]

    def test_validate_pagination_params_negative_skip(self):
        """Test pagination validation with negative skip."""
        with pytest.raises(ValidationException, match="Skip parameter must be non-negative"):
            validate_pagination_params(-1, 10)

    def test_validate_pagination_params_zero_limit(self):
        """Test pagination validation with zero limit."""
        with pytest.raises(ValidationException, match="Limit parameter must be positive"):
            validate_pagination_params(0, 0)

    def test_validate_pagination_params_limit_too_high(self):
        """Test pagination validation with limit too high."""
        with pytest.raises(ValidationException, match="Limit parameter too large"):
            validate_pagination_params(0, 101)

    def test_validate_pagination_params_success(self):
        """Test successful pagination validation."""
        skip, limit = validate_pagination_params(10, 50)
        assert skip == 10
        assert limit == 50

    def test_validate_search_query_dangerous_chars(self):
        """Test search query validation removes dangerous characters."""
        query = 'test <script> "quotes" & ampersand ; semicolon'
        result = validate_search_query(query)

        # Should remove dangerous characters
        assert "<" not in result
        assert ">" not in result
        assert '"' not in result
        assert "&" not in result
        assert ";" not in result

    def test_validate_pydantic_model_success(self):
        """Test successful Pydantic model validation."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            name: str
            age: int

        data = {"name": "John", "age": 30}
        result = validate_pydantic_model(TestModel, data)

        assert isinstance(result, TestModel)
        assert result.name == "John"
        assert result.age == 30

    def test_validate_pydantic_model_validation_error(self):
        """Test Pydantic model validation with validation error."""
        from pydantic import BaseModel

        class TestModel(BaseModel):
            name: str
            age: int

        data = {"name": "John", "age": "not_a_number"}

        with pytest.raises(ValidationException, match="Validation failed"):
            validate_pydantic_model(TestModel, data)

    def test_validate_json_field_success(self):
        """Test JSON field validation with valid data."""
        data = {"key": "value", "number": 123, "list": [1, 2, 3]}
        result = validate_json_field(data)
        assert result == data

    def test_validate_json_field_none(self):
        """Test JSON field validation with None."""
        result = validate_json_field(None)
        assert result is None

    def test_validate_json_field_invalid_json(self):
        """Test JSON field validation with non-serializable data."""
        import datetime

        # Object with datetime is not JSON serializable by default
        invalid_data = {"date": datetime.datetime.now()}

        with pytest.raises(ValidationException, match="Invalid JSON data"):
            validate_json_field(invalid_data)

    def test_validate_tags_invalid_characters(self):
        """Test tag validation with invalid characters."""
        with pytest.raises(ValidationException):
            validate_tags(["invalid tag with spaces"])

    def test_validate_tags_valid_only(self):
        """Test tag validation with only valid tags."""
        result = validate_tags(["valid_tag", "also_valid", "test123"])

        assert result == ["valid_tag", "also_valid", "test123"]
