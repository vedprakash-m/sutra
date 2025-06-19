import pytest
from api.shared.validation import (
    validate_email,
    validate_budget_limits,
    validate_tags,
    validate_collection_data,
    validate_llm_integration_data,
    validate_playbook_data,
    ValidationException,
    MAX_STRING_LENGTH
)


class TestValidationExtended:
    """Test suite for extended validation scenarios."""

    def test_validate_email_valid(self):
        """Test email validation with valid addresses."""
        assert validate_email("test@example.com") == "test@example.com"
        assert validate_email("test.name@example.co.uk") == "test.name@example.co.uk"

    def test_validate_email_invalid(self):
        """Test email validation with invalid addresses."""
        with pytest.raises(ValidationException, match="Invalid email address format"):
            validate_email("invalid-email")
        with pytest.raises(ValidationException, match="Invalid email address format"):
            validate_email("@missingusername.com")
        with pytest.raises(ValidationException, match="Invalid email address format"):
            validate_email("username@.com")

    def test_validate_budget_limits_valid(self):
        """Test budget limits validation with valid inputs."""
        assert validate_budget_limits({"total_budget": 100.0, "usage_limit": 10.0}) is True
        assert validate_budget_limits({"current_usage": 10.0, "budget_limit": 100.0}) is True

    def test_validate_budget_limits_invalid(self):
        """Test budget limits validation with invalid inputs."""
        with pytest.raises(ValidationException, match="Budget values cannot be negative"):
            validate_budget_limits({"total_budget": -10.0, "usage_limit": 5.0})
        with pytest.raises(ValidationException, match="Usage limit cannot exceed total budget"):
            validate_budget_limits({"total_budget": 5.0, "usage_limit": 10.0})
        with pytest.raises(ValidationException, match="Current usage cannot exceed budget limit"):
            validate_budget_limits({"current_usage": 110.0, "budget_limit": 100.0})

    def test_validate_llm_integration_edge_cases(self):
        """Test LLM integration validation with edge cases."""
        # Missing provider
        data = {
            "api_key": "test-key",
            "budget_limit": 100.0
        }
        result = validate_llm_integration_data(data)
        assert result["valid"] is False
        assert any("provider" in e.lower() for e in result["errors"])

        # Invalid budget format
        data = {
            "provider": "openai",
            "api_key": "test-key",
            "budget_limit": "not_a_number"
        }
        result = validate_llm_integration_data(data)
        assert result["valid"] is False

    def test_validate_collection_data_edge_cases(self):
        """Test collection validation with edge cases."""
        # Very long name
        data = {
            "name": "a" * (MAX_STRING_LENGTH + 1),  # Very long name
            "description": "Test description"
        }
        result = validate_collection_data(data)
        assert result["valid"] is False
        assert any("less than" in e for e in result["errors"]) 

    def test_validate_playbook_data_complex_steps(self):
        """Test playbook validation with complex step configurations."""
        data = {
            "name": "Complex Playbook",
            "description": "Test playbook with multiple steps",
            "steps": [
                {
                    "name": "Step 1",
                    "type": "prompt",
                    "description": "First step",
                    "promptText": "Test prompt",
                    "llm_providers": ["openai", "anthropic"]
                },
                {
                    "name": "Step 2",
                    "type": "prompt",
                    "description": "Second step",
                    "promptId": "prompt-123",
                    "llm_providers": ["google"],
                    "variables_mapping": {"output1": "input2"}
                }
            ]
        }
        result = validate_playbook_data(data)
        assert result["valid"] is True, f"Validation failed with errors: {result['errors']}"

class TestValidationErrorHandling:
    """Test suite for error handling in validation functions."""

    def test_validation_with_none_inputs(self):
        """Test validation functions handle None inputs gracefully."""
        with pytest.raises(ValidationException, match="Invalid email address format"):
            validate_email(None)

    def test_validation_with_empty_dict_inputs(self):
        """Test validation functions handle empty dict inputs."""
        result = validate_collection_data({})
        assert result["valid"] is False
        assert any("name is required" in e.lower() for e in result["errors"])

    def test_validation_with_malformed_data(self):
        """Test validation with malformed data structures."""
        # Collection with wrong data types
        data = {
            "name": 123,  # Should be string
            "description": ["not", "a", "string"],  # Should be string
            "tags": "not_a_list"  # Should be list
        }
        result = validate_collection_data(data)
        assert result["valid"] is False
        assert any("name must be a string" in e.lower() for e in result["errors"])
        assert any("description must be a string" in e.lower() for e in result["errors"])
        assert any("tags must be a list" in e.lower() for e in result["errors"])

        # Playbook with malformed steps
        data = {
            "name": "Test Playbook",
            "description": "Test description",
            "steps": "not_a_list"  # Should be list
        }
        result = validate_playbook_data(data)
        assert result["valid"] is False
