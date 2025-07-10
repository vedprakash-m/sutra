import json
import logging
import os
import sys

import azure.functions as func

# Add the root directory to Python path for proper imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

logger = logging.getLogger(__name__)

# Simple rate limiting based on IP
ip_usage = {}


async def get_admin_configured_limits():
    """Get admin-configured limits for anonymous users."""
    try:
        # Try to import database manager
        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
        from shared.database import get_database_manager

        db_manager = get_database_manager()

        if db_manager._development_mode:
            # Default limits for development
            return {"llm_calls_per_day": 5}

        # Try to get admin configuration
        config = await db_manager.read_item(
            container_name="SystemConfig",
            item_id="guest_user_limits",
            partition_key="guest_user_limits",
        )

        if config and config.get("limits"):
            return config["limits"]
    except Exception as e:
        logger.warning(f"Could not load admin limits: {e}")

    # Default fallback
    return {"llm_calls_per_day": 5}


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Anonymous LLM API - No login required, IP-based rate limiting

    Supports:
    - POST /api/anonymous/llm/execute - Execute LLM prompt without authentication
    - GET /api/anonymous/llm/models - List available models for anonymous users
    - GET /api/anonymous/llm/usage - Check remaining usage for IP
    """
    try:
        method = req.method
        route_params = req.route_params
        action = route_params.get("action", "execute")

        # Get IP address for rate limiting
        ip_address = req.headers.get("x-forwarded-for") or req.headers.get("x-real-ip") or "127.0.0.1"

        if method == "POST" and action == "execute":
            return await execute_anonymous_llm(req, ip_address)
        elif method == "GET" and action == "models":
            return await list_anonymous_models(req)
        elif method == "GET" and action == "usage":
            return await get_anonymous_usage(req, ip_address)
        else:
            return func.HttpResponse(
                json.dumps({"error": "Method not allowed"}),
                status_code=405,
                mimetype="application/json",
            )

    except Exception as e:
        logger.error(f"Error in anonymous LLM API: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Internal error: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
        )


async def execute_anonymous_llm(req: func.HttpRequest, ip_address: str) -> func.HttpResponse:
    """Execute LLM prompt for anonymous users."""
    try:
        # Get admin-configured limits
        limits = await get_admin_configured_limits()
        daily_limit = limits.get("llm_calls_per_day", 5)

        # Simple rate limiting
        if ip_address not in ip_usage:
            ip_usage[ip_address] = {"calls": 0, "date": "2025-06-25"}

        # Check if it's a new day (simple check for demo)
        if ip_usage[ip_address]["calls"] >= daily_limit:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "daily_limit_exceeded",
                        "message": f"Anonymous users are limited to {daily_limit} calls per day. Please sign up for unlimited access.",
                        "daily_limit": daily_limit,
                        "calls_used": ip_usage[ip_address]["calls"],
                        "remaining": 0,
                        "note": "This limit is configurable by administrators",
                    }
                ),
                status_code=429,
                mimetype="application/json",
            )

        # Parse request body
        try:
            body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json",
            )

        # Validate required fields
        prompt = body.get("prompt")
        if not prompt:
            return func.HttpResponse(
                json.dumps({"error": "Prompt is required"}),
                status_code=400,
                mimetype="application/json",
            )

        # Validate prompt length for anonymous users
        if len(prompt) > 500:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "prompt_too_long",
                        "message": "Anonymous users are limited to 500 characters per prompt. Please shorten your prompt or sign up for a free account.",
                        "max_length": 500,
                        "current_length": len(prompt),
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        # Mock LLM execution for development
        mock_response = {
            "id": f"anon_llm_{hash(ip_address)}_{len(prompt)}",
            "object": "text_completion",
            "model": "gpt-3.5-turbo",
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": 35,
                "total_tokens": len(prompt.split()) + 35,
            },
            "choices": [
                {
                    "text": f"🤖 AI Response to '{prompt[:30]}...'\n\nThis is a demo response from Sutra AI. In production, this would be generated by GPT-3.5 Turbo. Anonymous users get limited responses - sign up for full access to all models and unlimited calls!",
                    "index": 0,
                    "finish_reason": "stop",
                }
            ],
            "created": 1703123456,
            "user_type": "anonymous",
            "_mock": True,
        }

        # Increment usage
        ip_usage[ip_address]["calls"] += 1
        remaining_calls = daily_limit - ip_usage[ip_address]["calls"]

        # Add anonymous user information
        mock_response["anonymous_info"] = {
            "remaining_calls": max(0, remaining_calls),
            "daily_limit": daily_limit,
            "calls_used": ip_usage[ip_address]["calls"],
            "signup_message": f"You have {max(0, remaining_calls)} free calls remaining today. Sign up for unlimited access!",
        }

        logger.info(f"Anonymous LLM execution for IP: {ip_address}, remaining: {remaining_calls}")

        return func.HttpResponse(
            json.dumps(mock_response, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error executing anonymous LLM prompt: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Failed to execute prompt: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
        )


async def list_anonymous_models(req: func.HttpRequest) -> func.HttpResponse:
    """List available models for anonymous users."""
    try:
        # Anonymous users only get access to basic models
        models = [
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "provider": "openai",
                "description": "Fast and efficient for basic tasks",
                "max_tokens": 100,
                "available_for_anonymous": True,
                "note": "Limited to 100 tokens for anonymous users",
            }
        ]

        response_data = {
            "models": models,
            "user_type": "anonymous",
            "limitations": {
                "max_prompt_length": 500,
                "max_tokens_per_response": 100,
                "models_available": 1,
                "calls_per_day": 5,
            },
            "upgrade_message": "Sign up for access to more models and higher limits!",
        }

        return func.HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error listing anonymous models: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Failed to list models: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
        )


async def get_anonymous_usage(req: func.HttpRequest, ip_address: str) -> func.HttpResponse:
    """Get usage information for anonymous user (IP-based)."""
    try:
        # Get admin-configured limits
        limits = await get_admin_configured_limits()
        daily_limit = limits.get("llm_calls_per_day", 5)

        if ip_address not in ip_usage:
            ip_usage[ip_address] = {"calls": 0, "date": "2025-06-25"}

        calls_used = ip_usage[ip_address]["calls"]
        remaining = max(0, daily_limit - calls_used)

        usage_data = {
            "session_type": "anonymous",
            "ip_based": True,
            "daily_limits": {"llm_calls": daily_limit},
            "current_usage": {"llm_calls": calls_used},
            "remaining": {"llm_calls": remaining},
            "resets_at": "2025-06-26T00:00:00Z",  # Next day
            "limitations": {
                "max_prompt_length": 500,
                "max_tokens_per_response": 100,
                "model_restrictions": ["gpt-3.5-turbo only"],
            },
            "admin_note": "Anonymous user limits are configurable by administrators",
            "upgrade_benefits": [
                "Unlimited daily calls",
                "Access to all models (GPT-4, Claude, etc.)",
                "Longer prompts (no 500 char limit)",
                "More tokens per response",
                "Save prompts and create collections",
                "Build and save playbooks",
            ],
        }

        return func.HttpResponse(
            json.dumps(usage_data, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error getting anonymous usage: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Failed to get usage data: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
        )
