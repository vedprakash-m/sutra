"""
Input validation utilities for the Sutra API.

This module provides comprehensive validation for all API inputs including:
- Request data validation
- Business logic validation
- Security constraints
- Rate limiting checks
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, ValidationError, validator

from .models import (
    Collection,
    LLMProvider,
    LLMProviderConfig,
    Playbook,
    PlaybookStatus,
    PlaybookStep,
    PromptStatus,
    PromptTemplate,
    PromptVariable,
    UsageRecord,
    User,
    UserRole,
)

logger = logging.getLogger(__name__)


# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

# Security constraints
MAX_STRING_LENGTH = 10000
MAX_CONTENT_LENGTH = 50000
MAX_VARIABLES_COUNT = 50
MAX_STEPS_COUNT = 100
MAX_TAGS_COUNT = 20
MAX_TAG_LENGTH = 50
MAX_DESCRIPTION_LENGTH = 1000

# Regex patterns for validation
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")
SAFE_STRING_PATTERN = re.compile(r"^[a-zA-Z0-9\s\-_.,!?()]+$")


# =============================================================================
# VALIDATION EXCEPTIONS
# =============================================================================


class ValidationException(Exception):
    """Base validation exception."""

    def __init__(self, message: str, field: Optional[str] = None, code: str = "VALIDATION_ERROR"):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(message)


class SecurityValidationException(ValidationException):
    """Security-related validation exception."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, field, "SECURITY_VIOLATION")


class BusinessLogicException(ValidationException):
    """Business logic validation exception."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, field, "BUSINESS_LOGIC_ERROR")


class RateLimitException(ValidationException):
    """Rate limiting exception."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, code="RATE_LIMIT_EXCEEDED")


# =============================================================================
# CORE VALIDATION FUNCTIONS
# =============================================================================


def validate_email(email: str) -> str:
    """Validate email address format."""
    if not email or not isinstance(email, str) or not EMAIL_PATTERN.match(email):
        raise ValidationException("Invalid email address format", "email")
    return email


def validate_identifier(identifier: str, field_name: str = "identifier") -> str:
    """Validate identifier format (letters, numbers, underscore, hyphen)."""
    if not identifier:
        raise ValidationException(f"{field_name} cannot be empty", field_name)
    if len(identifier) > 100:
        raise ValidationException(f"{field_name} too long (max 100 characters)", field_name)
    if not IDENTIFIER_PATTERN.match(identifier):
        raise ValidationException(
            f"{field_name} must start with letter and contain only letters, numbers, underscore, hyphen",
            field_name,
        )
    return identifier.strip()


def validate_safe_string(text: str, field_name: str = "text", max_length: int = MAX_STRING_LENGTH) -> str:
    """Validate string contains only safe characters."""
    if not text:
        return text

    if len(text) > max_length:
        raise ValidationException(f"{field_name} too long (max {max_length} characters)", field_name)

    # Check for potentially dangerous patterns
    dangerous_patterns = [
        r"<script[^>]*>",
        r"javascript:",
        r"data:text/html",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
    ]

    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, text_lower):
            raise SecurityValidationException(f"Potentially dangerous content detected in {field_name}", field_name)

    return text.strip()


def validate_content(content: str, field_name: str = "content") -> str:
    """Validate content with more permissive rules but still secure."""
    if not content:
        raise ValidationException(f"{field_name} cannot be empty", field_name)

    if len(content) > MAX_CONTENT_LENGTH:
        raise ValidationException(f"{field_name} too long (max {MAX_CONTENT_LENGTH} characters)", field_name)

    # Check for script injections but allow more formatting
    dangerous_patterns = [
        r"<script[^>]*>",
        r"javascript:",
        r"data:text/html",
        r"vbscript:",
    ]

    content_lower = content.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, content_lower):
            raise SecurityValidationException(f"Script injection detected in {field_name}", field_name)

    return content.strip()


def validate_tags(tags: List[str]) -> List[str]:
    """Validate a list of tags."""
    if len(tags) > MAX_TAGS_COUNT:
        raise ValidationException(f"Too many tags (max {MAX_TAGS_COUNT})", "tags")

    validated_tags = []
    for tag in tags:
        if not tag or not isinstance(tag, str):
            continue

        tag = tag.strip().lower()
        if len(tag) > MAX_TAG_LENGTH:
            raise ValidationException(f"Tag too long (max {MAX_TAG_LENGTH} characters)", "tags")

        if not re.match(r"^[a-zA-Z0-9\-_]+$", tag):
            raise ValidationException(
                "Tags can only contain letters, numbers, hyphens, and underscores",
                "tags",
            )

        if tag not in validated_tags:
            validated_tags.append(tag)

    return validated_tags


def validate_json_field(data: Any, field_name: str = "json_field") -> Any:
    """Validate JSON serializable data."""
    try:
        # Test JSON serialization
        json.dumps(data)
        return data
    except (TypeError, ValueError) as e:
        raise ValidationException(f"Invalid JSON data in {field_name}: {str(e)}", field_name)


# =============================================================================
# MODEL-SPECIFIC VALIDATORS
# =============================================================================


class PromptTemplateValidator:
    """Validator for prompt template operations."""

    @staticmethod
    def validate_create_request(data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Validate prompt template creation request."""
        validated = {}

        # Required fields
        validated["title"] = validate_safe_string(data.get("title", ""), "title", 200)
        if not validated["title"]:
            raise ValidationException("Title is required", "title")

        validated["content"] = validate_content(data.get("content", ""), "content")

        # Optional fields
        validated["description"] = validate_safe_string(data.get("description", ""), "description", 1000)
        validated["tags"] = validate_tags(data.get("tags", []))

        # Variables validation
        variables = data.get("variables", [])
        if len(variables) > MAX_VARIABLES_COUNT:
            raise ValidationException(f"Too many variables (max {MAX_VARIABLES_COUNT})", "variables")

        validated_variables = []
        for i, var in enumerate(variables):
            if not isinstance(var, dict):
                raise ValidationException(f"Variable {i} must be an object", "variables")

            var_name = validate_identifier(var.get("name", ""), f"variables[{i}].name")
            var_desc = validate_safe_string(var.get("description", ""), f"variables[{i}].description", 500)
            var_type = var.get("type", "string")

            if var_type not in ["string", "number", "boolean"]:
                raise ValidationException(f"Invalid variable type: {var_type}", f"variables[{i}].type")

            validated_variables.append(
                {
                    "name": var_name,
                    "description": var_desc,
                    "type": var_type,
                    "required": bool(var.get("required", True)),
                    "default_value": var.get("default_value"),
                }
            )

        validated["variables"] = validated_variables
        validated["user_id"] = user_id
        validated["status"] = PromptStatus.DRAFT

        return validated

    @staticmethod
    def validate_update_request(data: Dict[str, Any], existing_prompt: PromptTemplate) -> Dict[str, Any]:
        """Validate prompt template update request."""
        validated = {}

        # Only allow updating certain fields
        updatable_fields = [
            "title",
            "description",
            "content",
            "variables",
            "tags",
            "status",
        ]

        for field in updatable_fields:
            if field in data:
                if field == "title":
                    validated[field] = validate_safe_string(data[field], field, 200)
                elif field == "description":
                    validated[field] = validate_safe_string(data[field], field, 1000)
                elif field == "content":
                    validated[field] = validate_content(data[field], field)
                elif field == "tags":
                    validated[field] = validate_tags(data[field])
                elif field == "status":
                    if data[field] not in [s.value for s in PromptStatus]:
                        raise ValidationException(f"Invalid status: {data[field]}", field)
                    validated[field] = data[field]
                elif field == "variables":
                    # Use same validation as create
                    variables = data[field]
                    if len(variables) > MAX_VARIABLES_COUNT:
                        raise ValidationException(f"Too many variables (max {MAX_VARIABLES_COUNT})", field)

                    validated_variables = []
                    for i, var in enumerate(variables):
                        var_name = validate_identifier(var.get("name", ""), f"{field}[{i}].name")
                        var_desc = validate_safe_string(var.get("description", ""), f"{field}[{i}].description", 500)
                        var_type = var.get("type", "string")

                        if var_type not in ["string", "number", "boolean"]:
                            raise ValidationException(
                                f"Invalid variable type: {var_type}",
                                f"{field}[{i}].type",
                            )

                        validated_variables.append(
                            {
                                "name": var_name,
                                "description": var_desc,
                                "type": var_type,
                                "required": bool(var.get("required", True)),
                                "default_value": var.get("default_value"),
                            }
                        )

                    validated[field] = validated_variables

        return validated


class CollectionValidator:
    """Validator for collection operations."""

    @staticmethod
    def validate_create_request(data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Validate collection creation request."""
        validated = {}

        # Required fields
        validated["name"] = validate_safe_string(data.get("name", ""), "name", 200)
        if not validated["name"]:
            raise ValidationException("Name is required", "name")

        # Optional fields
        validated["description"] = validate_safe_string(data.get("description", ""), "description", 1000)
        validated["tags"] = validate_tags(data.get("tags", []))
        validated["is_public"] = bool(data.get("is_public", False))

        # Prompt IDs validation
        prompt_ids = data.get("prompt_ids", [])
        if not isinstance(prompt_ids, list):
            raise ValidationException("prompt_ids must be a list", "prompt_ids")

        validated_prompt_ids = []
        for prompt_id in prompt_ids:
            if not isinstance(prompt_id, str) or not prompt_id.strip():
                continue
            validated_prompt_ids.append(prompt_id.strip())

        validated["prompt_ids"] = validated_prompt_ids
        validated["user_id"] = user_id

        return validated


class PlaybookValidator:
    """Validator for playbook operations."""

    @staticmethod
    def validate_create_request(data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Validate playbook creation request."""
        validated = {}

        # Required fields
        validated["name"] = validate_safe_string(data.get("name", ""), "name", 200)
        if not validated["name"]:
            raise ValidationException("Name is required", "name")

        # Optional fields
        validated["description"] = validate_safe_string(data.get("description", ""), "description", 1000)
        validated["tags"] = validate_tags(data.get("tags", []))

        # Steps validation
        steps = data.get("steps", [])
        if len(steps) > MAX_STEPS_COUNT:
            raise ValidationException(f"Too many steps (max {MAX_STEPS_COUNT})", "steps")

        validated_steps = []
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                raise ValidationException(f"Step {i} must be an object", "steps")

            step_name = validate_safe_string(step.get("name", ""), f"steps[{i}].name", 200)
            step_type = step.get("type", "prompt")

            if step_type not in ["prompt", "manual_review", "condition", "loop"]:
                raise ValidationException(f"Invalid step type: {step_type}", f"steps[{i}].type")

            validated_step = {
                "step_number": i + 1,
                "name": step_name,
                "type": step_type,
                "config": validate_json_field(step.get("config", {}), f"steps[{i}].config"),
            }

            validated_steps.append(validated_step)

        validated["steps"] = validated_steps
        validated["user_id"] = user_id
        validated["status"] = PlaybookStatus.DRAFT

        return validated


# =============================================================================
# REQUEST VALIDATION HELPERS
# =============================================================================


def validate_pydantic_model(model_class: Type[BaseModel], data: Dict[str, Any]) -> BaseModel:
    """Validate data against a Pydantic model."""
    try:
        return model_class(**data)
    except ValidationError as e:
        # Convert Pydantic validation errors to our format
        errors = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            errors.append(f"{field}: {message}")

        raise ValidationException(f"Validation failed: {'; '.join(errors)}")


def validate_pagination_params(skip: int = 0, limit: int = 50) -> tuple[int, int]:
    """Validate pagination parameters."""
    if skip < 0:
        raise ValidationException("Skip parameter must be non-negative", "skip")

    if limit < 1:
        raise ValidationException("Limit parameter must be positive", "limit")

    if limit > 100:
        raise ValidationException("Limit parameter too large (max 100)", "limit")

    return skip, limit


def validate_search_query(query: str) -> str:
    """Validate search query string."""
    if not query:
        return ""

    query = query.strip()
    if len(query) > 200:
        raise ValidationException("Search query too long (max 200 characters)", "query")

    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", '"', "'", "&", ";"]
    for char in dangerous_chars:
        query = query.replace(char, "")

    return query


# =============================================================================
# RATE LIMITING VALIDATION
# =============================================================================


class RateLimitValidator:
    """Rate limiting validation for API endpoints."""

    # Rate limits per user per hour
    RATE_LIMITS = {
        "prompt_executions": 1000,
        "prompt_creations": 100,
        "collection_operations": 200,
        "playbook_executions": 50,
        "admin_operations": 1000,  # Higher limit for admin users
    }

    @staticmethod
    def check_rate_limit(user_id: str, operation_type: str, current_count: int) -> None:
        """Check if user has exceeded rate limit for operation type."""
        limit = RateLimitValidator.RATE_LIMITS.get(operation_type, 100)

        if current_count >= limit:
            raise RateLimitException(f"Rate limit exceeded for {operation_type}. Limit: {limit} per hour")


# =============================================================================
# BUSINESS LOGIC VALIDATORS
# =============================================================================


def validate_user_permissions(user: User, required_role: UserRole) -> None:
    """Validate user has required permissions."""
    if required_role == UserRole.ADMIN and user.role != UserRole.ADMIN:
        raise BusinessLogicException("Admin privileges required for this operation")


def validate_resource_ownership(resource_user_id: str, requesting_user_id: str, user_roles: List[UserRole]) -> None:
    """Validate user can access resource (owner or admin)."""
    if resource_user_id != requesting_user_id and UserRole.ADMIN not in user_roles:
        raise BusinessLogicException("Access denied: insufficient permissions")


def validate_budget_limits(data: Dict[str, float]) -> bool:
    """Validate total budget and usage limits."""
    total_budget = data.get("total_budget")
    usage_limit = data.get("usage_limit")
    current_usage = data.get("current_usage")
    budget_limit = data.get("budget_limit")

    if total_budget is not None and usage_limit is not None:
        if not all(isinstance(x, (int, float)) for x in [total_budget, usage_limit]):
            raise ValidationException("Budget values must be numeric", "budget")
        if total_budget < 0 or usage_limit < 0:
            raise ValidationException("Budget values cannot be negative", "budget")
        if usage_limit > total_budget:
            raise ValidationException("Usage limit cannot exceed total budget", "budget")

    if current_usage is not None and budget_limit is not None:
        if not all(isinstance(x, (int, float)) for x in [current_usage, budget_limit]):
            raise ValidationException("Budget values must be numeric", "budget")
        if current_usage < 0 or budget_limit < 0:
            raise ValidationException("Budget values cannot be negative", "budget")
        if current_usage > budget_limit:
            raise ValidationException("Current usage cannot exceed budget limit", "budget")

    return True


def validate_collection_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate collection creation/update data."""
    errors = []

    # Required fields
    if "name" not in data or not data["name"]:
        errors.append("Collection name is required")
    elif not isinstance(data.get("name"), str):
        errors.append("Collection name must be a string")
    elif len(data["name"]) > MAX_STRING_LENGTH:
        errors.append(f"Collection name must be a string and less than {MAX_STRING_LENGTH} characters")

    # Optional fields
    if "description" in data and data["description"] and not isinstance(data.get("description"), str):
        errors.append("Description must be a string")
    elif "description" in data and data["description"] and len(data["description"]) > MAX_DESCRIPTION_LENGTH:
        errors.append(f"Description must be a string and less than {MAX_DESCRIPTION_LENGTH} characters")

    if "tags" in data and data["tags"] and not isinstance(data["tags"], list):
        errors.append("Tags must be a list of strings")

    return {"valid": not errors, "errors": errors}


def validate_llm_integration_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate LLM integration data."""
    errors = []

    # Required fields
    if "provider" not in data or not data["provider"]:
        errors.append("Provider is required")
    else:
        valid_providers = ["openai", "google_gemini", "anthropic", "custom"]
        if data["provider"] not in valid_providers:
            errors.append(f"Provider must be one of: {', '.join(valid_providers)}")

    if "apiKey" not in data or not data["apiKey"]:
        errors.append("API key is required")
    elif len(data["apiKey"]) < 10:
        errors.append("API key appears to be too short")
    elif len(data["apiKey"]) > 1000:
        errors.append("API key is too long")

    # Custom provider requires URL
    if data.get("provider") == "custom":
        if "url" not in data or not data["url"]:
            errors.append("Custom provider requires a URL")
        else:
            # Basic URL validation
            url = data["url"]
            if not url.startswith(("http://", "https://")):
                errors.append("URL must start with http:// or https://")
            elif len(url) > 500:
                errors.append("URL is too long")

    return {"valid": len(errors) == 0, "errors": errors}


def validate_playbook_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate playbook creation/update data."""
    errors = []

    # Required fields
    if "name" not in data or not data["name"]:
        errors.append("Playbook name is required")
    elif len(data["name"]) > MAX_STRING_LENGTH:
        errors.append(f"Playbook name cannot exceed {MAX_STRING_LENGTH} characters")

    if "steps" not in data or not isinstance(data["steps"], list) or not data["steps"]:
        errors.append("Playbook must have at least one step")
    else:
        for i, step in enumerate(data["steps"]):
            step_errors = _validate_playbook_step(step, i)
            if step_errors:
                errors.extend(step_errors)

    return {"valid": not errors, "errors": errors}


def _validate_playbook_step(step: Dict[str, Any], index: int) -> List[str]:
    """Validate a single playbook step."""
    errors = []
    step_prefix = f"Step {index + 1}: "

    if "type" not in step:
        errors.append(f"{step_prefix}Step type is required")
    elif step["type"] not in ["prompt", "manual_review", "condition", "loop"]:
        errors.append(f"{step_prefix}Invalid step type")

    if "stepId" in step:
        if not IDENTIFIER_PATTERN.match(step["stepId"]):
            errors.append(f"{step_prefix}Invalid step ID format")

    if step.get("type") == "prompt":
        if "promptId" not in step and "promptText" not in step:
            errors.append(f"{step_prefix}Prompt step must have either promptId or promptText")

        if "config" in step:
            config = step["config"]
            if "temperature" in config:
                temp = config["temperature"]
                if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                    errors.append(f"{step_prefix}Temperature must be between 0 and 2")

            if "maxTokens" in config:
                tokens = config["maxTokens"]
                if not isinstance(tokens, int) or tokens < 1 or tokens > 10000:
                    errors.append(f"{step_prefix}Max tokens must be between 1 and 10000")

    if "outputParsingRules" in step:
        parsing = step["outputParsingRules"]
        if not isinstance(parsing, dict):
            errors.append(f"{step_prefix}Output parsing rules must be a dictionary")
        else:
            if "regex" in parsing:
                try:
                    re.compile(parsing["regex"])
                except re.error:
                    errors.append(f"{step_prefix}Invalid regex pattern")

    return errors


def validate_execution_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate playbook execution input data."""
    errors = []

    if "initialInputs" in data:
        if not isinstance(data["initialInputs"], dict):
            errors.append("Initial inputs must be a dictionary")
        else:
            for var_name, var_value in data["initialInputs"].items():
                if not IDENTIFIER_PATTERN.match(var_name):
                    errors.append(f"Invalid variable name '{var_name}'")

                # Basic type validation
                if isinstance(var_value, str) and len(var_value) > MAX_CONTENT_LENGTH:
                    errors.append(f"Variable '{var_name}' value is too long")

    return {"valid": len(errors) == 0, "errors": errors}
