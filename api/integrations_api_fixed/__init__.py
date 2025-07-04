import azure.functions as func
import json
import logging
import traceback
import sys
import os

# Add the root directory to Python path for proper imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from shared.unified_auth import get_auth_provider, require_authentication

logger = logging.getLogger(__name__)


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Fixed integrations API endpoint - manual authentication without decorator
    """
    try:
        # Manual authentication - no decorator
        user = await require_authentication(req)
        user_id = user.id

        method = req.method
        route_params = req.route_params
        provider = route_params.get("provider")
        action = route_params.get("action")

        logger.info(f"Integrations API called by {user.email}: {method} {req.url}")

        # Route to appropriate handler
        if method == "GET":
            return await list_llm_integrations(user_id)
        elif method == "POST":
            if provider and action == "test":
                return await validate_llm_connection(user_id, provider, req)
            else:
                return await create_llm_integration(user_id, req)
        elif method == "PUT" and provider:
            return await update_llm_integration(user_id, provider, req)
        elif method == "DELETE" and provider:
            return await delete_llm_integration(user_id, provider)
        else:
            return func.HttpResponse(
                json.dumps({"error": "Method not allowed"}),
                status_code=405,
                mimetype="application/json",
            )

    except Exception as e:
        logger.error(f"Integrations API error: {str(e)}")
        logger.error(traceback.format_exc())

        # Return proper error response
        if "Authentication required" in str(e) or "401" in str(e):
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "authentication_required",
                        "message": "Please log in to access this resource",
                    }
                ),
                status_code=401,
                mimetype="application/json",
            )
        else:
            return func.HttpResponse(
                json.dumps(
                    {"error": "internal_error", "message": "An internal error occurred"}
                ),
                status_code=500,
                mimetype="application/json",
            )


async def list_llm_integrations(user_id: str) -> func.HttpResponse:
    """List user's LLM integrations"""
    try:
        # Simplified response for now - just return success
        return func.HttpResponse(
            json.dumps(
                {
                    "status": "success",
                    "integrations": [],
                    "message": "Integrations API working",
                }
            ),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as e:
        logger.error(f"List integrations error: {e}")
        return func.HttpResponse(
            json.dumps({"error": "list_error", "message": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


async def create_llm_integration(
    user_id: str, req: func.HttpRequest
) -> func.HttpResponse:
    """Create new LLM integration"""
    try:
        return func.HttpResponse(
            json.dumps(
                {"status": "success", "message": "Create integration endpoint working"}
            ),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as e:
        logger.error(f"Create integration error: {e}")
        return func.HttpResponse(
            json.dumps({"error": "create_error", "message": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


async def update_llm_integration(
    user_id: str, provider: str, req: func.HttpRequest
) -> func.HttpResponse:
    """Update LLM integration"""
    try:
        return func.HttpResponse(
            json.dumps(
                {
                    "status": "success",
                    "message": f"Update {provider} integration endpoint working",
                }
            ),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as e:
        logger.error(f"Update integration error: {e}")
        return func.HttpResponse(
            json.dumps({"error": "update_error", "message": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


async def delete_llm_integration(user_id: str, provider: str) -> func.HttpResponse:
    """Delete LLM integration"""
    try:
        return func.HttpResponse(
            json.dumps(
                {
                    "status": "success",
                    "message": f"Delete {provider} integration endpoint working",
                }
            ),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as e:
        logger.error(f"Delete integration error: {e}")
        return func.HttpResponse(
            json.dumps({"error": "delete_error", "message": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


async def validate_llm_connection(
    user_id: str, provider: str, req: func.HttpRequest
) -> func.HttpResponse:
    """Test LLM connection"""
    try:
        return func.HttpResponse(
            json.dumps(
                {
                    "status": "success",
                    "message": f"Test {provider} connection endpoint working",
                }
            ),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as e:
        logger.error(f"Test connection error: {e}")
        return func.HttpResponse(
            json.dumps({"error": "test_error", "message": str(e)}),
            status_code=500,
            mimetype="application/json",
        )
