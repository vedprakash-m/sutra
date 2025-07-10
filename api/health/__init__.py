"""
Health check endpoint for Sutra API (No-Gateway Architecture)
Provides system health status with enhanced security
"""

import logging
import os
import sys

import azure.functions as func

# Add the root directory to Python path for proper imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from shared.middleware import create_health_response, enhanced_security_middleware

# Initialize logging
logger = logging.getLogger(__name__)


@enhanced_security_middleware
def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint with rate limiting and security headers.

    GET /api/health

    Returns:
        200: System is healthy
        503: System is unhealthy
    """
    logger.info("Health check requested")

    try:
        if req.method == "GET":
            return create_health_response()
        else:
            return func.HttpResponse(
                '{"error": "Method not allowed"}',
                status_code=405,
                mimetype="application/json",
            )

    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return func.HttpResponse(
            '{"status": "unhealthy", "error": "Internal server error"}',
            status_code=503,
            mimetype="application/json",
        )
