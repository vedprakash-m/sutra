import azure.functions as func
import json
import logging
import sys
import os

# Add the root directory to Python path for proper imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from shared.guest_user import GuestUserManager, get_guest_usage_stats
from shared.database import get_database_manager

logger = logging.getLogger(__name__)


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Guest User Management API

    Supports:
    - GET /api/guest/session - Get or create guest session
    - GET /api/guest/session/{session_id}/stats - Get session usage stats
    """
    try:
        method = req.method
        route_params = req.route_params
        session_id = route_params.get("session_id")
        action = route_params.get("action")

        if method == "GET":
            if action == "stats" and session_id:
                return await get_session_stats(session_id)
            else:
                return await get_or_create_session(req)
        else:
            return func.HttpResponse(
                json.dumps({"error": "Method not allowed"}),
                status_code=405,
                mimetype="application/json",
            )

    except Exception as e:
        logger.error(f"Error in guest API: {str(e)}")
        return func.HttpResponse(
            json.dumps(
                {
                    "error": "internal_error",
                    "message": "Failed to process guest request",
                }
            ),
            status_code=500,
            mimetype="application/json",
        )


async def get_or_create_session(req: func.HttpRequest) -> func.HttpResponse:
    """Get existing guest session or create a new one."""
    try:
        # Get IP address and user agent
        ip_address = (
            req.headers.get("x-forwarded-for")
            or req.headers.get("x-real-ip")
            or "127.0.0.1"
        )
        user_agent = req.headers.get("user-agent", "unknown")
        existing_session_id = req.headers.get("x-guest-session-id")

        db_manager = get_database_manager()
        guest_manager = GuestUserManager(db_manager)

        guest_session = None

        # Try to get existing session
        if existing_session_id:
            guest_session = await guest_manager.get_guest_session(existing_session_id)

            # If session is expired or inactive, create a new one
            if not guest_session or not guest_session.get("active"):
                guest_session = None

        # Create new session if needed
        if not guest_session:
            guest_session = await guest_manager.create_guest_session(
                ip_address, user_agent
            )

        # Get usage stats
        stats = await get_guest_usage_stats(guest_session["id"], db_manager)

        response_data = {
            "session": {
                "id": guest_session["id"],
                "created_at": guest_session.get("created_at"),
                "expires_at": guest_session.get("expires_at"),
                "active": guest_session.get("active", True),
            },
            "usage": stats.get("usage", {}),
            "limits": stats.get("limits", {}),
            "remaining": stats.get("remaining", {}),
            "info": {
                "message": "Welcome! You can test Sutra with limited usage as a guest user.",
                "upgrade_message": "Sign up for a free account to get unlimited access to all features.",
            },
        }

        return func.HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            headers={
                "Content-Type": "application/json",
                "X-Guest-Session-Id": guest_session["id"],
            },
        )

    except Exception as e:
        logger.error(f"Error getting/creating guest session: {str(e)}")
        return func.HttpResponse(
            json.dumps(
                {"error": "session_error", "message": "Could not create guest session"}
            ),
            status_code=500,
            mimetype="application/json",
        )


async def get_session_stats(session_id: str) -> func.HttpResponse:
    """Get detailed stats for a guest session."""
    try:
        db_manager = get_database_manager()
        stats = await get_guest_usage_stats(session_id, db_manager)

        if "error" in stats:
            return func.HttpResponse(
                json.dumps(stats), status_code=404, mimetype="application/json"
            )

        return func.HttpResponse(
            json.dumps(stats, default=str),
            status_code=200,
            headers={
                "Content-Type": "application/json",
                "X-Guest-Session-Id": session_id,
            },
        )

    except Exception as e:
        logger.error(f"Error getting session stats: {str(e)}")
        return func.HttpResponse(
            json.dumps(
                {
                    "error": "stats_error",
                    "message": "Could not retrieve session statistics",
                }
            ),
            status_code=500,
            mimetype="application/json",
        )
