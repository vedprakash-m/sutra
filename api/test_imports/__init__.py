import json
import logging
import os
import sys
import traceback

import azure.functions as func

# Add the root directory to Python path for proper imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

logger = logging.getLogger(__name__)


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Test importing the decorator without using it
    """
    try:
        # Test 1: Can we import the decorator?
        try:
            from shared.unified_auth import auth_required

            logger.info("✅ Successfully imported auth_required decorator")
        except Exception as e:
            logger.error(f"❌ Failed to import auth_required decorator: {e}")
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "import_error",
                        "message": str(e),
                        "step": "decorator_import",
                    }
                ),
                status_code=500,
                mimetype="application/json",
            )

        # Test 2: Can we import the provider functions?
        try:
            from shared.unified_auth import get_auth_provider, require_authentication

            logger.info("✅ Successfully imported auth provider functions")
        except Exception as e:
            logger.error(f"❌ Failed to import auth provider functions: {e}")
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "import_error",
                        "message": str(e),
                        "step": "provider_import",
                    }
                ),
                status_code=500,
                mimetype="application/json",
            )

        # Test 3: Can we create the provider?
        try:
            provider = get_auth_provider()
            logger.info(f"✅ Successfully created auth provider: {type(provider)}")
        except Exception as e:
            logger.error(f"❌ Failed to create auth provider: {e}")
            logger.error(traceback.format_exc())
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "provider_creation_error",
                        "message": str(e),
                        "step": "provider_creation",
                    }
                ),
                status_code=500,
                mimetype="application/json",
            )

        # Test 4: Can we call require_authentication?
        try:
            # This should throw an authentication error since we don't have valid auth
            user = await require_authentication(req)
            logger.info(f"✅ Unexpected success: {user}")
        except Exception as e:
            logger.info(f"✅ Expected auth error (this is good): {e}")

        result = {
            "status": "success",
            "message": "All import and provider creation tests passed",
            "provider_type": str(type(provider)),
            "method": req.method,
        }

        return func.HttpResponse(json.dumps(result), status_code=200, mimetype="application/json")

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
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
