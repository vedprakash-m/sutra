import json

import azure.functions as func


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """Simple test function without authentication"""
    return func.HttpResponse(
        json.dumps({"message": "Test endpoint working", "method": req.method}),
        status_code=200,
        mimetype="application/json",
    )
