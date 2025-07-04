import azure.functions as func
import json
import logging
import sys
import os

# Add the root directory to Python path for proper imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from shared.guest_user import allow_guest_access
from shared.unified_auth import require_authentication
from shared.database import get_database_manager
from shared.error_handling import handle_api_error, SutraAPIError
import traceback

logger = logging.getLogger(__name__)


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    LLM Execution API with guest access support

    Supports:
    - POST /api/llm/execute - Execute LLM prompt
    - GET /api/llm/models - List available models
    """
    try:
        # Manual authentication - allow guest access
        user = None
        try:
            user = await require_authentication(req)
        except Exception:
            # Allow guest access for this endpoint
            pass

        method = req.method
        route_params = req.route_params
        action = route_params.get("action", "execute")

        logger.info(
            f"Guest LLM API called by {user.email if user else 'guest'}: {method} {req.url}"
        )

        if method == "POST" and action == "execute":
            return await execute_llm_prompt(req)
        elif method == "GET" and action == "models":
            return await list_available_models(req)
        else:
            return func.HttpResponse(
                json.dumps({"error": "Method not allowed"}),
                status_code=405,
                mimetype="application/json",
            )

    except Exception as e:
        logger.error(f"Guest LLM API error: {str(e)}")
        logger.error(traceback.format_exc())

        # Return proper error response
        return func.HttpResponse(
            json.dumps(
                {"error": "internal_error", "message": "An internal error occurred"}
            ),
            status_code=500,
            mimetype="application/json",
        )


async def execute_llm_prompt(req: func.HttpRequest) -> func.HttpResponse:
    """Execute an LLM prompt with guest access support."""
    try:
        # Parse request body
        try:
            body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json",
            )

        # Get user (authenticated or guest)
        user = req.current_user
        is_guest = getattr(user, "role", None) == "guest"

        # Validate required fields
        prompt = body.get("prompt")
        if not prompt:
            return func.HttpResponse(
                json.dumps({"error": "Prompt is required"}),
                status_code=400,
                mimetype="application/json",
            )

        # Get model preference
        model = body.get(
            "model", "gpt-3.5-turbo"
        )  # Default to cheaper model for guests
        max_tokens = body.get(
            "max_tokens", 150 if is_guest else 1000
        )  # Limit tokens for guests

        # For guests, limit to specific models and parameters
        if is_guest:
            allowed_models = ["gpt-3.5-turbo", "gpt-4o-mini"]
            if model not in allowed_models:
                model = "gpt-3.5-turbo"
            max_tokens = min(max_tokens, 150)  # Hard limit for guests

        # Mock LLM execution for development
        mock_response = {
            "id": f"llm_exec_{user.id}_{len(prompt)}",
            "object": "text_completion",
            "model": model,
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": 50,
                "total_tokens": len(prompt.split()) + 50,
            },
            "choices": [
                {
                    "text": f"This is a mock response to your prompt: '{prompt[:50]}...' \n\nIn a real implementation, this would be the actual LLM response. The system is working correctly and would integrate with OpenAI, Anthropic, or other LLM providers.",
                    "index": 0,
                    "finish_reason": "stop",
                }
            ],
            "created": 1703123456,
            "user_type": "guest" if is_guest else "authenticated",
            "_mock": True,
        }

        # Add guest-specific information
        if is_guest:
            guest_session = getattr(req, "guest_session", {})
            remaining_calls = (
                guest_session.get("limits", {}).get("llm_calls_per_day", 5)
                - guest_session.get("usage", {}).get("llm_calls", 0)
                - 1
            )

            mock_response["guest_info"] = {
                "remaining_calls": max(0, remaining_calls),
                "upgrade_message": f"You have {max(0, remaining_calls)} LLM calls remaining today. Sign up for unlimited access!",
            }

        logger.info(
            f"LLM execution for user {user.id} ({'guest' if is_guest else 'authenticated'})"
        )

        return func.HttpResponse(
            json.dumps(mock_response, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error executing LLM prompt: {str(e)}")
        raise SutraAPIError(f"Failed to execute LLM prompt: {str(e)}", 500)


async def list_available_models(req: func.HttpRequest) -> func.HttpResponse:
    """List available LLM models."""
    try:
        user = req.current_user
        is_guest = getattr(user, "role", None) == "guest"

        if is_guest:
            # Limited models for guest users
            models = [
                {
                    "id": "gpt-3.5-turbo",
                    "name": "GPT-3.5 Turbo",
                    "provider": "openai",
                    "description": "Fast and efficient for most tasks",
                    "max_tokens": 150,
                    "available_for_guests": True,
                },
                {
                    "id": "gpt-4o-mini",
                    "name": "GPT-4o Mini",
                    "provider": "openai",
                    "description": "Smaller version of GPT-4o",
                    "max_tokens": 150,
                    "available_for_guests": True,
                },
            ]
        else:
            # Full model list for authenticated users
            models = [
                {
                    "id": "gpt-3.5-turbo",
                    "name": "GPT-3.5 Turbo",
                    "provider": "openai",
                    "description": "Fast and efficient for most tasks",
                    "max_tokens": 4000,
                    "available_for_guests": True,
                },
                {
                    "id": "gpt-4",
                    "name": "GPT-4",
                    "provider": "openai",
                    "description": "Most capable model for complex tasks",
                    "max_tokens": 8000,
                    "available_for_guests": False,
                },
                {
                    "id": "gpt-4o-mini",
                    "name": "GPT-4o Mini",
                    "provider": "openai",
                    "description": "Smaller version of GPT-4o",
                    "max_tokens": 4000,
                    "available_for_guests": True,
                },
                {
                    "id": "claude-3-sonnet",
                    "name": "Claude 3 Sonnet",
                    "provider": "anthropic",
                    "description": "Balanced performance and speed",
                    "max_tokens": 4000,
                    "available_for_guests": False,
                },
            ]

        response_data = {
            "models": models,
            "user_type": "guest" if is_guest else "authenticated",
            "note": "Guest users have access to limited models with reduced token limits"
            if is_guest
            else None,
        }

        return func.HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise SutraAPIError(f"Failed to list models: {str(e)}", 500)
