import azure.functions as func
import json
import logging
import traceback
import sys
import os

# Add the root directory to Python path for proper imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from shared.unified_auth import auth_required

logger = logging.getLogger(__name__)


@auth_required()
async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Test authenticated endpoint with decorator
    """
    try:
        # Get authenticated user from unified auth decorator
        user = getattr(req, "user", None)
        if not user:
            return func.HttpResponse(
                json.dumps({"error": "Authentication required"}),
                status_code=401,
                mimetype="application/json",
            )

        result = {
            "status": "success",
            "message": "Test authenticated endpoint works",
            "user_email": user.email,
            "user_role": str(user.role),
            "user_id": user.id,
            "method": req.method,
        }

        logger.info(f"Test authenticated endpoint success: {result}")

        return func.HttpResponse(
            json.dumps(result), status_code=200, mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Test authenticated endpoint error: {e}")
        logger.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({"error": "unexpected_error", "message": str(e)}),
            status_code=500,
            mimetype="application/json",
        )
