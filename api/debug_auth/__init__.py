import azure.functions as func
import json
import logging
import traceback
import sys
import os

# Add the root directory to Python path for proper imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

logger = logging.getLogger(__name__)


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Debug authentication endpoint to isolate issues
    """
    logger.info("=== DEBUG AUTH ENDPOINT START ===")

    try:
        # Step 1: Basic request logging
        logger.info(f"Method: {req.method}")
        logger.info(f"URL: {req.url}")
        logger.info(f"Headers: {dict(req.headers)}")

        # Step 2: Test imports
        try:
            from shared.unified_auth import get_auth_provider

            logger.info("✅ Successfully imported get_auth_provider")
        except Exception as e:
            logger.error(f"❌ Failed to import get_auth_provider: {e}")
            logger.error(traceback.format_exc())
            return func.HttpResponse(
                json.dumps({"error": "import_error", "message": str(e)}),
                status_code=500,
                mimetype="application/json",
            )

        # Step 3: Test auth provider initialization
        try:
            auth_provider = get_auth_provider()
            logger.info("✅ Successfully initialized auth provider")
            logger.info(f"Provider type: {type(auth_provider)}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize auth provider: {e}")
            logger.error(traceback.format_exc())
            return func.HttpResponse(
                json.dumps({"error": "auth_provider_init_error", "message": str(e)}),
                status_code=500,
                mimetype="application/json",
            )

        # Step 4: Test user extraction
        try:
            user = await auth_provider.get_user_from_request(req)
            logger.info(f"User extraction result: {user}")
            if user:
                logger.info(f"✅ User found: {user.email}")
            else:
                logger.info("⚠️ No user found (unauthenticated)")
        except Exception as e:
            logger.error(f"❌ Failed to extract user: {e}")
            logger.error(traceback.format_exc())
            return func.HttpResponse(
                json.dumps({"error": "user_extraction_error", "message": str(e)}),
                status_code=500,
                mimetype="application/json",
            )

        # Step 5: Return success with debug info
        result = {
            "status": "success",
            "message": "Debug authentication completed",
            "user_authenticated": user is not None,
            "user_email": user.email if user else None,
            "user_role": str(user.role) if user else None,
            "provider_type": str(type(auth_provider)),
            "headers_count": len(req.headers),
            "method": req.method,
        }

        logger.info(f"=== DEBUG AUTH ENDPOINT SUCCESS: {result} ===")

        return func.HttpResponse(
            json.dumps(result), status_code=200, mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"❌ Unexpected error in debug endpoint: {e}")
        logger.error(traceback.format_exc())
        return func.HttpResponse(
            json.dumps(
                {
                    "error": "unexpected_error",
                    "message": str(e),
                    "traceback": traceback.format_exc(),
                }
            ),
            status_code=500,
            mimetype="application/json",
        )
