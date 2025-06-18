import pytest
from unittest.mock import MagicMock, patch
from api.shared.validation import (
    validate_email,
    validate_identifier,
    validate_collection_data,
    validate_playbook_data,
    validate_llm_integration_data,
    validate_budget_limits
)
from api.shared.models import UserRole, LLMProvider, PromptVariable


class TestValidationExtended:
    """Extended tests for validation functions with better coverage."""

    # Note: Some tests commented out due to missing functions in validation.py
    
    # def test_validate_prompt_variables_valid(self):
    #     """Test prompt variable validation with valid inputs."""
    #     variables = [
    #         PromptVariable(name="var1", description="Test var", type="string"),
    #         PromptVariable(name="var2", description="Number var", type="number", required=False)
    #     ]
    #     assert validate_prompt_variables(variables) is True

    # def test_validate_prompt_variables_invalid(self):
    #     """Test prompt variable validation with invalid inputs."""
    #     # Empty name
    #     variables = [
    #         PromptVariable(name="", description="Test var", type="string")
    #     ]
    #     assert validate_prompt_variables(variables) is False

    #     # Duplicate names
    #     variables = [
    #         PromptVariable(name="var1", description="Test var", type="string"),
    #         PromptVariable(name="var1", description="Another var", type="number")
    #     ]
    #     assert validate_prompt_variables(variables) is False

    # def test_sanitize_html_input_basic(self):
    #     """Test HTML sanitization with basic inputs."""
    #     assert sanitize_html_input("Hello World") == "Hello World"
    #     assert sanitize_html_input("<script>alert('xss')</script>") == ""
    #     assert sanitize_html_input("<p>Safe text</p>") == "Safe text"
    #     assert sanitize_html_input("<b>Bold</b> text") == "Bold text"

    # def test_sanitize_html_input_edge_cases(self):
    #     """Test HTML sanitization with edge cases."""
    #     assert sanitize_html_input("") == ""
    #     assert sanitize_html_input(None) == ""
    #     assert sanitize_html_input("   ") == ""
    #     assert sanitize_html_input("Normal text with & symbols") == "Normal text with & symbols"

    # def test_validate_api_key_format_valid(self):
    #     """Test API key format validation with valid keys."""
    #     assert validate_api_key_format("sk-1234567890abcdef") is True
    #     assert validate_api_key_format("key-abcdef1234567890") is True
    #     assert validate_api_key_format("api_key_1234567890") is True

    # def test_validate_api_key_format_invalid(self):
    #     """Test API key format validation with invalid keys."""
    #     assert validate_api_key_format("") is False
    #     assert validate_api_key_format("short") is False
    #     assert validate_api_key_format(None) is False
    #     assert validate_api_key_format("   ") is False

    def test_validate_budget_limits_valid(self):
        """Test budget limits validation with valid inputs."""
        assert validate_budget_limits(100.0, 10.0) is True
        assert validate_budget_limits(1000.0, 0.0) is True
        assert validate_budget_limits(0.0, 0.0) is True

    def test_validate_budget_limits_invalid(self):
        """Test budget limits validation with invalid inputs."""
        assert validate_budget_limits(-10.0, 5.0) is False  # Negative total
        assert validate_budget_limits(100.0, -5.0) is False  # Negative daily
        assert validate_budget_limits(50.0, 100.0) is False  # Daily > Total
        assert validate_budget_limits(None, 10.0) is False  # None total
        assert validate_budget_limits(100.0, None) is False  # None daily

    def test_validate_llm_integration_edge_cases(self):
        """Test LLM integration validation with edge cases."""
        # Missing provider
        data = {
            "api_key": "test-key",
            "budget_limit": 100.0
        }
        result = validate_llm_integration_data(data)
        assert result["valid"] is False
        assert "provider" in result["errors"]

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
            "name": "a" * 1000,  # Very long name
            "description": "Test description"
        }
        result = validate_collection_data(data)
        assert result["valid"] is False
        assert "name" in result["errors"]

        # Empty description
        data = {
            "name": "Test Collection",
            "description": ""
        }
        result = validate_collection_data(data)
        assert result["valid"] is False

    def test_validate_playbook_data_complex_steps(self):
        """Test playbook validation with complex step configurations."""
        data = {
            "name": "Complex Playbook",
            "description": "Test playbook with multiple steps",
            "steps": [
                {
                    "name": "Step 1",
                    "description": "First step",
                    "prompt_content": "Test prompt",
                    "llm_providers": ["openai", "anthropic"]
                },
                {
                    "name": "Step 2", 
                    "description": "Second step",
                    "prompt_id": "prompt-123",
                    "llm_providers": ["google"],
                    "variables_mapping": {"output1": "input2"}
                }
            ]
        }
        result = validate_playbook_data(data)
        assert result["valid"] is True

        # Invalid step - no prompt content or ID
        data["steps"].append({
            "name": "Invalid Step",
            "description": "Missing prompt",
            "llm_providers": ["openai"]
        })
        result = validate_playbook_data(data)
        assert result["valid"] is False


class TestValidationErrorHandling:
    """Test validation error handling and edge cases."""

    def test_validation_with_none_inputs(self):
        """Test validation functions handle None inputs gracefully."""
        assert validate_email(None) is False
        assert validate_identifier(None) is False
        
        result = validate_collection_data(None)
        assert result["valid"] is False
        
        result = validate_playbook_data(None)
        assert result["valid"] is False

    def test_validation_with_empty_dict_inputs(self):
        """Test validation functions handle empty dict inputs."""
        result = validate_collection_data({})
        assert result["valid"] is False
        assert "name" in result["errors"]
        
        result = validate_playbook_data({})
        assert result["valid"] is False
        assert "name" in result["errors"]

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

        # Playbook with malformed steps
        data = {
            "name": "Test Playbook",
            "description": "Test description",
            "steps": "not_a_list"  # Should be list
        }
        result = validate_playbook_data(data)
        assert result["valid"] is False
