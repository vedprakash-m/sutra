"""
Guest User System for Sutra
Allows unauthenticated users to test the service with limited LLM calls
"""

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from functools import wraps

import azure.functions
from functools import wraps
import azure.functions as func

logger = logging.getLogger(__name__)


class GuestUserManager:
    """Manages guest user sessions and usage tracking."""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.default_guest_limits = {
            "llm_calls_per_day": 5,
            "prompts_per_day": 10,
            "collections_per_session": 3,
            "playbooks_per_session": 2,
            "session_duration_hours": 24
        }

    async def get_guest_limits(self) -> Dict[str, int]:
        """Get guest user limits from admin configuration."""
        try:
            if not self.db_manager:
                return self.default_guest_limits

            # Get admin-configured limits
            config = await self.db_manager.read_item(
                container_name="SystemConfig",
                item_id="guest_user_limits",
                partition_key="guest_user_limits"
            )

            if config:
                return {**self.default_guest_limits, **config.get("limits", {})}

        except Exception as e:
            logger.warning(f"Could not load guest limits from config: {e}")

        return self.default_guest_limits

    async def create_guest_session(self, ip_address: str, user_agent: str = None) -> Dict[str, Any]:
        """Create a new guest user session."""
        try:
            session_id = f"guest_{uuid.uuid4().hex[:12]}"
            now = datetime.now(timezone.utc)

            limits = await self.get_guest_limits()

            guest_session = {
                "id": session_id,
                "type": "guest_session",
                "ip_address": ip_address,
                "user_agent": user_agent or "unknown",
                "created_at": now.isoformat(),
                "expires_at": (now + timedelta(hours=limits["session_duration_hours"])).isoformat(),
                "usage": {
                    "llm_calls": 0,
                    "prompts_created": 0,
                    "collections_created": 0,
                    "playbooks_created": 0,
                    "last_activity": now.isoformat()
                },
                "limits": limits,
                "active": True
            }

            if self.db_manager and not self.db_manager._development_mode:
                await self.db_manager.create_item(
                    container_name="GuestSessions",
                    item=guest_session,
                    partition_key=session_id
                )

            logger.info(f"Created guest session {session_id} for IP {ip_address}")
            return guest_session

        except Exception as e:
            logger.error(f"Error creating guest session: {e}")
            raise

    async def get_guest_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get guest session by ID."""
        try:
            if not self.db_manager or self.db_manager._development_mode:
                # Return mock session for development
                return {
                    "id": session_id,
                    "type": "guest_session",
                    "usage": {"llm_calls": 0, "prompts_created": 0},
                    "limits": self.default_guest_limits,
                    "active": True,
                    "_mock": True
                }

            session = await self.db_manager.read_item(
                container_name="GuestSessions",
                item_id=session_id,
                partition_key=session_id
            )

            # Check if session is expired
            if session and session.get("expires_at"):
                expires_at = datetime.fromisoformat(session["expires_at"].replace("Z", "+00:00"))
                if datetime.now(timezone.utc) > expires_at:
                    session["active"] = False
                    await self.update_guest_session(session)

            return session

        except Exception as e:
            logger.warning(f"Could not get guest session {session_id}: {e}")
            return None

    async def update_guest_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Update guest session usage."""
        try:
            session["usage"]["last_activity"] = datetime.now(timezone.utc).isoformat()

            if self.db_manager and not self.db_manager._development_mode:
                updated_session = await self.db_manager.update_item(
                    container_name="GuestSessions",
                    item=session
                )
                return updated_session

            return session

        except Exception as e:
            logger.error(f"Error updating guest session: {e}")
            return session

    async def check_usage_limit(self, session: Dict[str, Any], usage_type: str) -> bool:
        """Check if guest user has exceeded usage limits."""
        try:
            usage = session.get("usage", {})
            limits = session.get("limits", self.default_guest_limits)

            current_usage = usage.get(usage_type, 0)
            limit = limits.get(f"{usage_type}_per_day", 0)

            return current_usage < limit

        except Exception as e:
            logger.error(f"Error checking usage limit: {e}")
            return False

    async def increment_usage(self, session: Dict[str, Any], usage_type: str) -> Dict[str, Any]:
        """Increment usage counter for guest session."""
        try:
            if "usage" not in session:
                session["usage"] = {}

            session["usage"][usage_type] = session["usage"].get(usage_type, 0) + 1
            return await self.update_guest_session(session)

        except Exception as e:
            logger.error(f"Error incrementing usage: {e}")
            return session

    async def get_or_create_anonymous_session(self, ip_address: str, user_agent: str = None) -> Dict[str, Any]:
        """Get or create anonymous guest session based on IP address."""
        try:
            # For anonymous users, use IP-based session ID
            session_id = f"anon_{hash(ip_address) % 1000000:06d}"
            now = datetime.now(timezone.utc)

            # Try to get existing session
            existing_session = await self.get_guest_session(session_id)

            if existing_session and existing_session.get("active"):
                # Check if session is from today (reset daily limits)
                created_at = datetime.fromisoformat(existing_session.get("created_at", "").replace("Z", "+00:00"))
                if created_at.date() == now.date():
                    return existing_session

            # Create new anonymous session
            limits = await self.get_guest_limits()

            anonymous_session = {
                "id": session_id,
                "type": "anonymous_session",
                "ip_address": ip_address,
                "user_agent": user_agent or "unknown",
                "created_at": now.isoformat(),
                "expires_at": (now + timedelta(hours=24)).isoformat(),  # Daily reset
                "usage": {
                    "llm_calls": 0,
                    "prompts_created": 0,
                    "collections_created": 0,
                    "playbooks_created": 0,
                    "last_activity": now.isoformat()
                },
                "limits": limits,
                "active": True,
                "anonymous": True
            }

            if self.db_manager and not self.db_manager._development_mode:
                await self.db_manager.create_item(
                    container_name="GuestSessions",
                    item=anonymous_session,
                    partition_key=session_id
                )

            logger.info(f"Created anonymous session {session_id} for IP {ip_address}")
            return anonymous_session

        except Exception as e:
            logger.error(f"Error creating anonymous session: {e}")
            # Return minimal session for fallback
            limits = await self.get_guest_limits()
            return {
                "id": f"temp_{uuid.uuid4().hex[:8]}",
                "type": "temp_anonymous",
                "usage": {"llm_calls": 0},
                "limits": limits,
                "active": True,
                "anonymous": True,
                "_temp": True
            }


def allow_guest_access(usage_type: str = "llm_calls", allow_anonymous: bool = True):
    """
    Decorator to allow guest access with usage tracking.

    Args:
        usage_type: Type of usage to track (llm_calls, prompts_created, etc.)
        allow_anonymous: If True, allows completely anonymous access without session creation
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(req: azure.functions.HttpRequest) -> azure.functions.HttpResponse:
            try:
                from shared.database import get_database_manager

                # Check if user is authenticated
                auth_header = req.headers.get("x-ms-client-principal")
                if auth_header:
                    # User is authenticated, proceed normally
                    return await func(req)

                # For anonymous access, use IP-based tracking
                ip_address = req.headers.get("x-forwarded-for") or req.headers.get("x-real-ip") or "127.0.0.1"
                guest_session_id = req.headers.get("x-guest-session-id")

                db_manager = get_database_manager()
                guest_manager = GuestUserManager(db_manager)

                guest_session = None

                # Try to get existing session by ID or create anonymous session based on IP
                if guest_session_id:
                    guest_session = await guest_manager.get_guest_session(guest_session_id)

                if not guest_session and allow_anonymous:
                    # Create anonymous session based on IP address for tracking
                    user_agent = req.headers.get("user-agent", "unknown")
                    guest_session = await guest_manager.get_or_create_anonymous_session(ip_address, user_agent)

                # If still no session and anonymous access not allowed, require session creation
                if not guest_session and not allow_anonymous:
                    return azure.functions.HttpResponse(
                        json.dumps({
                            "error": "guest_session_required",
                            "message": "Please create a guest session first.",
                            "action": "create_session_first"
                        }),
                        status_code=401,
                        headers={"Content-Type": "application/json"}
                    )

                # Check usage limits
                if not await guest_manager.check_usage_limit(guest_session, usage_type):
                    limits = guest_session.get("limits", {})
                    limit = limits.get(f"{usage_type}_per_day", 0)

                    return azure.functions.HttpResponse(
                        json.dumps({
                            "error": "guest_limit_exceeded",
                            "message": f"Guest user limit exceeded. You can make {limit} {usage_type.replace('_', ' ')} per day.",
                            "limits": limits,
                            "usage": guest_session.get("usage", {}),
                            "suggestion": "Please sign up for a free account to get higher limits."
                        }),
                        status_code=429,
                        headers={
                            "Content-Type": "application/json",
                            "X-Guest-Session-Id": guest_session["id"]
                        }
                    )

                # Create mock user object for guest
                class GuestUser:
                    def __init__(self, session):
                        self.id = session["id"]
                        self.email = "guest@sutra.app" if not session.get("anonymous") else "anonymous@sutra.app"
                        self.name = "Guest User" if not session.get("anonymous") else "Anonymous User"
                        self.role = "guest" if not session.get("anonymous") else "anonymous"
                        self.session = session

                req.current_user = GuestUser(guest_session)
                req.guest_session = guest_session

                # Call the original function
                response = await func(req)

                # Increment usage if the request was successful
                if response.status_code < 400:
                    await guest_manager.increment_usage(guest_session, usage_type)

                # Add guest session ID to response headers
                if hasattr(response, 'headers'):
                    response.headers["X-Guest-Session-Id"] = guest_session["id"]

                return response

            except Exception as e:
                logger.error(f"Error in guest access decorator: {e}")
                return azure.functions.HttpResponse(
                    json.dumps({
                        "error": "guest_access_error",
                        "message": "Error processing guest request"
                    }),
                    status_code=500,
                    headers={"Content-Type": "application/json"}
                )

        return wrapper
    return decorator


async def get_guest_usage_stats(session_id: str, db_manager=None) -> Dict[str, Any]:
    """Get usage statistics for a guest session."""
    try:
        guest_manager = GuestUserManager(db_manager)
        session = await guest_manager.get_guest_session(session_id)

        if not session:
            return {"error": "Session not found"}

        limits = session.get("limits", {})
        usage = session.get("usage", {})

        stats = {
            "session_id": session_id,
            "active": session.get("active", False),
            "created_at": session.get("created_at"),
            "expires_at": session.get("expires_at"),
            "usage": usage,
            "limits": limits,
            "remaining": {}
        }

        # Calculate remaining usage
        for limit_key, limit_value in limits.items():
            if limit_key.endswith("_per_day") or limit_key.endswith("_per_session"):
                usage_key = limit_key.replace("_per_day", "").replace("_per_session", "")
                current_usage = usage.get(usage_key, 0)
                stats["remaining"][usage_key] = max(0, limit_value - current_usage)

        return stats

    except Exception as e:
        logger.error(f"Error getting guest usage stats: {e}")
        return {"error": "Could not retrieve usage stats"}
