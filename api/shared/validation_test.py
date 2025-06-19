"""
Unit tests for validation utilities.
"""

import pytest
from datetime import datetime

from .validation import (
    ValidationException, SecurityValidationException, BusinessLogicException,
    validate_email, validate_identifier,
    validate_collection_data, validate_playbook_data, validate_llm_integration_data
)


def test_validate_email_valid():
    """Test valid email validation."""
    email = "user@example.com"
    result = validate_email(email)
    assert result == email.lower()


def test_validate_email_invalid():
    """Test invalid email validation."""
    with pytest.raises(ValidationException):
        validate_email("invalid-email")


def test_validate_identifier_valid():
    """Test valid identifier validation."""
    identifier = "valid_identifier123"
    result = validate_identifier(identifier)
    assert result == identifier


def test_validate_identifier_invalid():
    """Test invalid identifier validation."""
    with pytest.raises(ValidationException):
        validate_identifier("123invalid")  # Can't start with number


def test_validate_collection_data_valid():
    """Test valid collection data."""
    data = {
        "name": "Test Collection",
        "description": "A test collection",
        "prompt_ids": [],
        "tags": ["test", "collection"],
        "is_public": False
    }
    result = validate_collection_data(data)
    assert result["valid"] == True
    assert len(result["errors"]) == 0


def test_validate_collection_data_missing_name():
    """Test collection validation with missing name."""
    data = {
        "description": "A test collection",
        "prompt_ids": [],
        "tags": [],
        "is_public": False
    }
    result = validate_collection_data(data)
    assert result["valid"] == False
    assert len(result["errors"]) > 0


def test_validate_playbook_data_valid():
    """Test valid playbook data."""
    data = {
        "name": "Test Playbook",
        "description": "A test playbook",
        "steps": [
            {
                "name": "Step 1",
                "type": "prompt",
                "promptText": "Test prompt"
            }
        ],
        "tags": ["test", "playbook"]
    }
    result = validate_playbook_data(data)
    assert result["valid"] is True, f"Validation failed with errors: {result['errors']}"


def test_validate_playbook_data_missing_name():
    """Test playbook validation with missing name."""
    data = {
        "description": "A test playbook",
        "steps": [],
        "tags": []
    }
    result = validate_playbook_data(data)
    assert result["valid"] == False
    assert len(result["errors"]) > 0


def test_validate_llm_integration_data_valid():
    """Test valid LLM integration data."""
    data = {
        "provider": "openai",
        "apiKey": "test-api-key-1234567890",
        "enabled": True
    }
    result = validate_llm_integration_data(data)
    assert result["valid"] == True
    assert len(result["errors"]) == 0


def test_validate_llm_integration_data_invalid_provider():
    """Test LLM integration validation with invalid provider."""
    data = {
        "provider": "invalid_provider",
        "apiKey": "test-api-key-1234567890",
        "enabled": True
    }
    result = validate_llm_integration_data(data)
    assert result["valid"] == False
    assert len(result["errors"]) > 0
