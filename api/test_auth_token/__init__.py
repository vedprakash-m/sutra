"""
Test endpoint for debugging authentication token flow
"""

import json
import logging
import os
from typing import Any, Dict

import azure.functions as func

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Test endpoint to debug authentication token flow"""
    try:
        headers = dict(req.headers)

        # Log all headers for debugging
        logger.info("=== AUTH DEBUG HEADERS ===")
        for key, value in headers.items():
            if "auth" in key.lower() or "principal" in key.lower() or "bearer" in value.lower():
                logger.info(f"{key}: {value[:50]}..." if len(value) > 50 else f"{key}: {value}")

        auth_header = headers.get("Authorization") or headers.get("authorization")

        debug_info = {
            "timestamp": "2025-07-04T02:40:00Z",
            "headers_received": len(headers),
            "auth_header_present": bool(auth_header),
            "auth_header_type": auth_header.split()[0] if auth_header and " " in auth_header else None,
            "token_length": len(auth_header.split()[1]) if auth_header and " " in auth_header else 0,
            "principal_header": bool(headers.get("x-ms-client-principal")),
            "environment_vars": {
                "SUTRA_ENTRA_ID_CLIENT_ID": (
                    os.getenv("SUTRA_ENTRA_ID_CLIENT_ID", "NOT_SET")[:50] + "..."
                    if os.getenv("SUTRA_ENTRA_ID_CLIENT_ID") and len(os.getenv("SUTRA_ENTRA_ID_CLIENT_ID", "")) > 50
                    else os.getenv("SUTRA_ENTRA_ID_CLIENT_ID", "NOT_SET")
                ),
                "SUTRA_ENTRA_ID_AUTHORITY": os.getenv("SUTRA_ENTRA_ID_AUTHORITY", "NOT_SET"),
                "ENTRA_CLIENT_ID": os.getenv("ENTRA_CLIENT_ID", "NOT_SET"),
                "ENTRA_TENANT_ID": os.getenv("ENTRA_TENANT_ID", "NOT_SET"),
            },
        }

        # Test token validation
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

            try:
                from shared.entra_auth import validate_bearer_token

                user = validate_bearer_token(auth_header)

                debug_info["token_validation"] = {
                    "success": bool(user),
                    "user_email": user.email if user else None,
                    "user_role": user.role if user else None,
                }

            except Exception as e:
                debug_info["token_validation"] = {"success": False, "error": str(e)}

        return func.HttpResponse(
            json.dumps(debug_info, indent=2),
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

    except Exception as e:
        logger.error(f"Auth debug error: {e}")
        return func.HttpResponse(
            json.dumps({"error": "debug_failed", "message": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )
