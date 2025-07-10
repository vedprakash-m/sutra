import json
import logging

import azure.functions as func

logger = logging.getLogger(__name__)


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """Simple test endpoint for anonymous users."""
    try:
        method = req.method

        if method == "GET":
            return func.HttpResponse(
                json.dumps(
                    {
                        "message": "Anonymous endpoint is working!",
                        "timestamp": "2025-06-25T06:00:00Z",
                        "test": True,
                    }
                ),
                status_code=200,
                mimetype="application/json",
            )
        elif method == "POST":
            try:
                body = req.get_json()
                prompt = body.get("prompt", "No prompt provided")

                return func.HttpResponse(
                    json.dumps({"response": f"Echo: {prompt}", "test": True, "anonymous": True}),
                    status_code=200,
                    mimetype="application/json",
                )
            except Exception:
                return func.HttpResponse(
                    json.dumps({"error": "Invalid JSON"}),
                    status_code=400,
                    mimetype="application/json",
                )
        else:
            return func.HttpResponse(
                json.dumps({"error": "Method not allowed"}),
                status_code=405,
                mimetype="application/json",
            )

    except Exception as e:
        logger.error(f"Error in test endpoint: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Internal error: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
        )
