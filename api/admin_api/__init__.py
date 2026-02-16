import json
import os
import sys

import azure.functions as func

# Add the root directory to Python path for proper imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
import traceback
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from shared.database import get_database_manager
from shared.error_handling import SutraAPIError, handle_api_error
from shared.models import UserRole, ValidationError
from shared.middleware import enhanced_security_middleware
from shared.unified_auth import require_authentication

# Initialize logging
logger = logging.getLogger(__name__)


@enhanced_security_middleware
async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Admin API endpoint for system administration and management.

    Supports:
    - GET /api/admin/users - List all users (admin only)
    - PUT /api/admin/users/{user_id}/role - Update user role (admin only)
    - GET /api/admin/system/health - System health check
    - GET /api/admin/system/stats - System statistics
    - POST /api/admin/system/maintenance - Enable/disable maintenance mode
    - GET /api/admin/llm/settings - Get LLM provider settings
    - PUT /api/admin/llm/settings - Update LLM provider settings
    - GET /api/admin/usage - Get usage statistics and monitoring
    """
    try:
        # Manual authentication - no decorator - admin only
        user = await require_authentication(req)

        # Check if user is admin
        if user.role != UserRole.ADMIN:
            return func.HttpResponse(
                json.dumps({"error": "Admin access required"}),
                status_code=403,
                mimetype="application/json",
            )

        user_id = user.id

        logger.info(f"Admin API called by {user.email}: {req.method} {req.url}")

        method = req.method
        route_params = req.route_params
        resource = route_params.get("resource")  # users, system, llm, usage
        action = route_params.get("action")  # health, stats, maintenance, settings
        target_user_id = route_params.get("user_id")

        # Route to appropriate handler
        if resource == "users":
            if method == "GET":
                return await list_users(user_id, req)
            elif method == "PUT" and target_user_id and action == "role":
                return await update_user_role(user_id, target_user_id, req)
        elif resource == "system":
            if method == "GET" and action == "health":
                return await get_system_health()
            elif method == "GET" and action == "stats":
                return await get_system_stats()
            elif method == "POST" and action == "maintenance":
                return await set_maintenance_mode(user_id, req)
        elif resource == "llm":
            if method == "GET" and action == "settings":
                return await get_llm_settings()
            elif method == "PUT" and action == "settings":
                return await update_llm_settings(user_id, req)
        elif resource == "usage":
            if method == "GET":
                return await get_usage_stats(req)
        elif resource == "test-data":
            if method == "POST" and action == "reset":
                return await reset_test_data(user_id, req)
            elif method == "POST" and action == "seed":
                return await seed_test_data(user_id, req)
        elif resource == "guest":
            if method == "GET" and action == "settings":
                return await get_guest_settings()
            elif method == "PUT" and action == "settings":
                return await update_guest_settings(user_id, req)
            elif method == "GET" and action == "stats":
                return await get_guest_usage_stats_admin(req)
        else:
            return func.HttpResponse(
                json.dumps({"error": "Resource not found"}),
                status_code=404,
                mimetype="application/json",
            )

    except Exception as e:
        logger.error(f"Admin API error: {str(e)}")
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
        elif "Admin access required" in str(e) or "403" in str(e):
            return func.HttpResponse(
                json.dumps({"error": "forbidden", "message": "Admin access required"}),
                status_code=403,
                mimetype="application/json",
            )
        else:
            return func.HttpResponse(
                json.dumps({"error": "internal_error", "message": "An internal error occurred"}),
                status_code=500,
                mimetype="application/json",
            )


async def list_users(admin_user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """List all users (admin only)."""
    try:
        # Parse query parameters
        params = req.params
        page = int(params.get("page", 1))
        limit = min(int(params.get("limit", 50)), 100)
        search = params.get("search", "").strip()
        role_filter = params.get("role")

        db_manager = get_database_manager()

        # Build query
        query_parts = ["SELECT * FROM c"]
        query_params = []

        # Add filters
        where_conditions = []

        if search:
            where_conditions.append("(CONTAINS(LOWER(c.name), LOWER(@search)) OR CONTAINS(LOWER(c.email), LOWER(@search)))")
            query_params.append({"name": "@search", "value": search})

        if role_filter:
            where_conditions.append("c.role = @role")
            query_params.append({"name": "@role", "value": role_filter})

        if where_conditions:
            query_parts.append("WHERE " + " AND ".join(where_conditions))

        # Add ordering and pagination
        query_parts.append("ORDER BY c.createdAt DESC")
        query_parts.append(f"OFFSET {(page - 1) * limit} LIMIT {limit}")

        query = " ".join(query_parts)

        # Execute query
        items = await db_manager.query_items(container_name="Users", query=query, parameters=query_params)

        # Mask sensitive data
        for user in items:
            if "llmApiKeys" in user:
                # Mask API keys for security
                masked_keys = {}
                for provider, config in user["llmApiKeys"].items():
                    if isinstance(config, dict):
                        masked_keys[provider] = {
                            "enabled": config.get("enabled", True),
                            "lastTested": config.get("lastTested"),
                            "status": config.get("status", "unknown"),
                        }
                    else:
                        masked_keys[provider] = {
                            "enabled": True,
                            "status": "configured",
                        }
                user["llmApiKeys"] = masked_keys

        # Get total count for pagination
        count_query = "SELECT VALUE COUNT(1) FROM c"
        count_params = []

        if where_conditions:
            count_query += " WHERE " + " AND ".join(where_conditions)
            if search:
                count_params.append({"name": "@search", "value": search})
            if role_filter:
                count_params.append({"name": "@role", "value": role_filter})

        total_count_result = await db_manager.query_items(container_name="Users", query=count_query, parameters=count_params)
        total_count = total_count_result[0] if total_count_result else 0

        total_pages = (total_count + limit - 1) // limit

        response_data = {
            "users": items,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_count": total_count,
                "limit": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }

        return func.HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise SutraAPIError(f"Failed to list users: {str(e)}", 500)


async def update_user_role(admin_user_id: str, target_user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """Update user role (admin only)."""
    try:
        # Parse request body
        try:
            body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json",
            )

        new_role = body.get("role")
        valid_roles = ["user", "admin"]

        if new_role not in valid_roles:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "Invalid role",
                        "message": f'Role must be one of: {", ".join(valid_roles)}',
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        db_manager = get_database_manager()

        # Get target user
        query = "SELECT * FROM c WHERE c.id = @user_id"
        parameters = [{"name": "@user_id", "value": target_user_id}]

        items = await db_manager.query_items(container_name="Users", query=query, parameters=parameters)

        if not items:
            return func.HttpResponse(
                json.dumps({"error": "User not found"}),
                status_code=404,
                mimetype="application/json",
            )

        user_data = items[0]

        # Update role
        old_role = user_data.get("role", "user")
        user_data["role"] = new_role
        user_data["updatedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Save to database
        updated_user = await db_manager.update_item(container_name="Users", item=user_data, partition_key=user_data["id"])

        logger.info(f"Admin {admin_user_id} updated user {target_user_id} role from {old_role} to {new_role}")

        return func.HttpResponse(
            json.dumps(
                {
                    "message": f"Successfully updated user role to {new_role}",
                    "userId": target_user_id,
                    "oldRole": old_role,
                    "newRole": new_role,
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error updating user role: {str(e)}")
        raise SutraAPIError(f"Failed to update user role: {str(e)}", 500)


async def get_system_health() -> func.HttpResponse:
    """Get system health status."""
    try:
        db_manager = get_database_manager()

        # Check database connectivity
        try:
            # Simple query to test database
            await db_manager.query_items(container_name="Users", query="SELECT VALUE COUNT(1) FROM c")
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        # Check system components
        health_data = {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "components": {
                "database": {"status": db_status, "type": "Cosmos DB"},
                "api": {"status": "healthy", "type": "Azure Functions"},
            },
            "uptime": "Available",  # Would be calculated from deployment time
            "version": "1.0.0",
        }

        status_code = 200 if health_data["status"] == "healthy" else 503

        return func.HttpResponse(
            json.dumps(health_data, default=str),
            status_code=status_code,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        return func.HttpResponse(
            json.dumps(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                }
            ),
            status_code=503,
            mimetype="application/json",
        )


async def get_system_stats() -> func.HttpResponse:
    """Get system statistics."""
    try:
        db_manager = get_database_manager()

        # Get user count
        users_container = db_manager.get_container("Users")
        user_count = list(
            users_container.query_items(query="SELECT VALUE COUNT(1) FROM c", enable_cross_partition_query=True)
        )[0]

        # Get prompt count
        prompts_container = db_manager.get_container("Prompts")
        prompt_count = list(
            prompts_container.query_items(query="SELECT VALUE COUNT(1) FROM c", enable_cross_partition_query=True)
        )[0]

        # Get collection count
        collections_container = db_manager.get_container("Collections")
        collection_count = list(
            collections_container.query_items(query="SELECT VALUE COUNT(1) FROM c", enable_cross_partition_query=True)
        )[0]

        # Get playbook count
        playbooks_container = db_manager.get_container("Playbooks")
        playbook_count = list(
            playbooks_container.query_items(query="SELECT VALUE COUNT(1) FROM c", enable_cross_partition_query=True)
        )[0]

        # Get recent activity (last 24 hours)
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat().replace("+00:00", "Z")

        recent_users = list(
            users_container.query_items(
                query="SELECT VALUE COUNT(1) FROM c WHERE c.createdAt >= @yesterday",
                parameters=[{"name": "@yesterday", "value": yesterday}],
                enable_cross_partition_query=True,
            )
        )[0]

        recent_prompts = list(
            prompts_container.query_items(
                query="SELECT VALUE COUNT(1) FROM c WHERE c.createdAt >= @yesterday",
                parameters=[{"name": "@yesterday", "value": yesterday}],
                enable_cross_partition_query=True,
            )
        )[0]

        stats_data = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "totals": {
                "users": user_count,
                "prompts": prompt_count,
                "collections": collection_count,
                "playbooks": playbook_count,
            },
            "recent_activity": {
                "period": "24 hours",
                "new_users": recent_users,
                "new_prompts": recent_prompts,
            },
        }

        return func.HttpResponse(
            json.dumps(stats_data, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        raise SutraAPIError(f"Failed to get system stats: {str(e)}", 500)


async def set_maintenance_mode(admin_user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """Enable/disable maintenance mode."""
    try:
        # Parse request body
        try:
            body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json",
            )

        enabled = body.get("enabled", False)
        message = body.get("message", "System maintenance in progress")

        # Store maintenance mode status (in production, this would be in a dedicated config store)
        db_manager = get_database_manager()
        config_container = db_manager.get_container("config")

        config_data = {
            "id": "maintenance_mode",
            "enabled": enabled,
            "message": message,
            "setBy": admin_user_id,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        try:
            # Try to update existing config
            config_container.replace_item(item="maintenance_mode", body=config_data)
        except Exception:
            # Create new config if it doesn't exist
            config_container.create_item(config_data)

        action = "enabled" if enabled else "disabled"
        logger.info(f"Admin {admin_user_id} {action} maintenance mode")

        return func.HttpResponse(
            json.dumps(
                {
                    "message": f"Maintenance mode {action}",
                    "enabled": enabled,
                    "maintenanceMessage": message if enabled else None,
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error setting maintenance mode: {str(e)}")
        raise SutraAPIError(f"Failed to set maintenance mode: {str(e)}", 500)


async def get_llm_settings() -> func.HttpResponse:
    """Get LLM provider settings."""
    try:
        db_manager = get_database_manager()

        try:
            config = await db_manager.read_item(
                container_name="SystemConfig",
                item_id="llm_settings",
                partition_key="llm_settings",
            )
        except Exception:
            # Default settings if not configured
            config = {
                "id": "llm_settings",
                "providers": {
                    "openai": {
                        "enabled": True,
                        "priority": 1,
                        "rateLimits": {"requestsPerMinute": 60, "tokensPerDay": 100000},
                        "budgetLimits": {"dailyBudget": 50.0, "monthlyBudget": 1000.0},
                    },
                    "google_gemini": {
                        "enabled": True,
                        "priority": 2,
                        "rateLimits": {"requestsPerMinute": 60, "tokensPerDay": 100000},
                        "budgetLimits": {"dailyBudget": 30.0, "monthlyBudget": 600.0},
                    },
                    "anthropic": {
                        "enabled": True,
                        "priority": 3,
                        "rateLimits": {"requestsPerMinute": 50, "tokensPerDay": 80000},
                        "budgetLimits": {"dailyBudget": 40.0, "monthlyBudget": 800.0},
                    },
                },
                "defaultProvider": "openai",
                "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }

        return func.HttpResponse(
            json.dumps(config, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error getting LLM settings: {str(e)}")
        raise SutraAPIError(f"Failed to get LLM settings: {str(e)}", 500)


async def update_llm_settings(admin_user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """Update LLM provider settings."""
    try:
        # Parse request body
        try:
            body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json",
            )

        db_manager = get_database_manager()
        config_container = db_manager.get_container("config")

        # Get existing settings
        try:
            existing_config = config_container.read_item(item="llm_settings", partition_key="llm_settings")
        except Exception:
            existing_config = {"id": "llm_settings", "providers": {}}

        # Update settings
        if "providers" in body:
            existing_config["providers"] = body["providers"]

        if "defaultProvider" in body:
            existing_config["defaultProvider"] = body["defaultProvider"]

        existing_config["updatedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        existing_config["updatedBy"] = admin_user_id

        # Save settings
        try:
            updated_config = config_container.replace_item(item="llm_settings", body=existing_config)
        except Exception:
            updated_config = config_container.create_item(existing_config)

        logger.info(f"Admin {admin_user_id} updated LLM settings")

        return func.HttpResponse(
            json.dumps(updated_config, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error updating LLM settings: {str(e)}")
        raise SutraAPIError(f"Failed to update LLM settings: {str(e)}", 500)


async def get_usage_stats(req: func.HttpRequest) -> func.HttpResponse:
    """Get usage statistics and monitoring."""
    try:
        # Parse query parameters
        params = req.params
        period = params.get("period", "day")  # day, week, month

        db_manager = get_database_manager()

        # Calculate date range
        now = datetime.now(timezone.utc)
        if period == "day":
            start_date = now - timedelta(days=1)
        elif period == "week":
            start_date = now - timedelta(weeks=1)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=1)

        start_iso = start_date.isoformat() + "Z"

        # Get execution stats
        executions_container = db_manager.get_container("Executions")

        total_executions = list(
            executions_container.query_items(
                query="SELECT VALUE COUNT(1) FROM c WHERE c.startTime >= @start_date",
                parameters=[{"name": "@start_date", "value": start_iso}],
                enable_cross_partition_query=True,
            )
        )[0]

        successful_executions = list(
            executions_container.query_items(
                query="SELECT VALUE COUNT(1) FROM c WHERE c.startTime >= @start_date AND c.status = 'completed'",
                parameters=[{"name": "@start_date", "value": start_iso}],
                enable_cross_partition_query=True,
            )
        )[0]

        failed_executions = list(
            executions_container.query_items(
                query="SELECT VALUE COUNT(1) FROM c WHERE c.startTime >= @start_date AND c.status = 'failed'",
                parameters=[{"name": "@start_date", "value": start_iso}],
                enable_cross_partition_query=True,
            )
        )[0]

        # Get active users
        users_container = db_manager.get_container("Users")
        active_users = list(
            users_container.query_items(
                query="SELECT VALUE COUNT(1) FROM c WHERE c.updatedAt >= @start_date",
                parameters=[{"name": "@start_date", "value": start_iso}],
                enable_cross_partition_query=True,
            )
        )[0]

        usage_data = {
            "period": period,
            "start_date": start_iso,
            "end_date": now.isoformat() + "Z",
            "statistics": {
                "executions": {
                    "total": total_executions,
                    "successful": successful_executions,
                    "failed": failed_executions,
                    "success_rate": (successful_executions / total_executions * 100) if total_executions > 0 else 0,
                },
                "users": {"active": active_users},
            },
        }

        return func.HttpResponse(
            json.dumps(usage_data, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error getting usage stats: {str(e)}")
        raise SutraAPIError(f"Failed to get usage stats: {str(e)}", 500)


# Test Data Management Functions (for E2E testing)


async def reset_test_data(admin_user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """
    Reset test database to clean state (E2E testing only).
    Only works in test/development environments.
    """
    try:
        import os

        environment = os.getenv("ENVIRONMENT", "production")

        # Security check: only allow in test/dev environments
        if environment not in ["test", "development", "local"]:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "Forbidden",
                        "message": "Test data reset only available in test environments",
                    }
                ),
                status_code=403,
                mimetype="application/json",
            )

        db_manager = get_database_manager()

        # List of containers to reset
        containers_to_reset = [
            "Users",
            "Prompts",
            "Collections",
            "Playbooks",
            "Executions",
            "LLMExecutions",
            "AdminSettings",
        ]

        reset_summary = {
            "environment": environment,
            "reset_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "reset_by": admin_user_id,
            "containers_reset": [],
        }

        for container_name in containers_to_reset:
            try:
                # Delete all documents in container
                query = "SELECT * FROM c"
                items = await db_manager.query_items(container_name, query)

                deleted_count = 0
                for item in items:
                    await db_manager.delete_item(container_name, item["id"], item.get("userId", item["id"]))
                    deleted_count += 1

                reset_summary["containers_reset"].append(
                    {
                        "name": container_name,
                        "items_deleted": deleted_count,
                        "status": "success",
                    }
                )

                logger.info(f"Reset container {container_name}: deleted {deleted_count} items")

            except Exception as container_error:
                reset_summary["containers_reset"].append(
                    {
                        "name": container_name,
                        "error": str(container_error),
                        "status": "error",
                    }
                )
                logger.error(f"Error resetting container {container_name}: {container_error}")

        return func.HttpResponse(json.dumps(reset_summary), status_code=200, mimetype="application/json")

    except Exception as e:
        logger.error(f"Error in reset_test_data: {e}")
        return func.HttpResponse(
            json.dumps(
                {
                    "error": "Internal Server Error",
                    "message": "Failed to reset test data",
                    "details": str(e),
                }
            ),
            status_code=500,
            mimetype="application/json",
        )


async def seed_test_data(admin_user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """
    Seed test database with initial data for E2E testing.
    Only works in test/development environments.
    """
    try:
        import os

        environment = os.getenv("ENVIRONMENT", "production")

        # Security check: only allow in test/dev environments
        if environment not in ["test", "development", "local"]:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "Forbidden",
                        "message": "Test data seeding only available in test environments",
                    }
                ),
                status_code=403,
                mimetype="application/json",
            )

        # Parse request body for seed options
        try:
            body = req.get_json()
            seed_options = body if body else {}
        except Exception:
            seed_options = {}

        db_manager = get_database_manager()
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        seed_summary = {
            "environment": environment,
            "seeded_at": now,
            "seeded_by": admin_user_id,
            "data_created": [],
        }

        # Create test users
        test_users = [
            {
                "id": "test-user-1",
                "email": "testuser1@example.com",
                "name": "Test User One",
                "role": "user",
                "userId": "test-user-1",
                "createdAt": now,
                "updatedAt": now,
            },
            {
                "id": "test-admin-1",
                "email": "testadmin@example.com",
                "name": "Test Admin",
                "role": "admin",
                "userId": "test-admin-1",
                "createdAt": now,
                "updatedAt": now,
            },
        ]

        for user in test_users:
            try:
                await db_manager.create_item("Users", user)
                seed_summary["data_created"].append({"type": "user", "id": user["id"], "status": "success"})
            except Exception as e:
                seed_summary["data_created"].append(
                    {
                        "type": "user",
                        "id": user["id"],
                        "error": str(e),
                        "status": "error",
                    }
                )

        # Create test collections
        test_collections = [
            {
                "id": str(uuid.uuid4()),
                "name": "Test Collection 1",
                "description": "A test collection for E2E testing",
                "userId": "test-user-1",
                "isPublic": False,
                "promptIds": [],
                "createdAt": now,
                "updatedAt": now,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Public Test Collection",
                "description": "A public test collection",
                "userId": "test-admin-1",
                "isPublic": True,
                "promptIds": [],
                "createdAt": now,
                "updatedAt": now,
            },
        ]

        for collection in test_collections:
            try:
                await db_manager.create_item("Collections", collection)
                seed_summary["data_created"].append({"type": "collection", "id": collection["id"], "status": "success"})
            except Exception as e:
                seed_summary["data_created"].append(
                    {
                        "type": "collection",
                        "id": collection["id"],
                        "error": str(e),
                        "status": "error",
                    }
                )

        # Create test prompts
        test_prompts = [
            {
                "id": str(uuid.uuid4()),
                "name": "Test Prompt 1",
                "content": 'This is a test prompt for E2E testing. Respond with: "Test successful"',
                "description": "A simple test prompt",
                "userId": "test-user-1",
                "version": 1,
                "isPublic": False,
                "tags": ["test", "e2e"],
                "llmSettings": {
                    "preferredProvider": "openai",
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7,
                },
                "createdAt": now,
                "updatedAt": now,
            }
        ]

        for prompt in test_prompts:
            try:
                await db_manager.create_item("Prompts", prompt)
                seed_summary["data_created"].append({"type": "prompt", "id": prompt["id"], "status": "success"})
            except Exception as e:
                seed_summary["data_created"].append(
                    {
                        "type": "prompt",
                        "id": prompt["id"],
                        "error": str(e),
                        "status": "error",
                    }
                )

        # Create admin settings for testing
        admin_settings = {
            "id": "test-settings",
            "llmProviders": {
                "openai": {
                    "enabled": True,
                    "models": ["gpt-3.5-turbo", "gpt-4"],
                    "rateLimit": 100,
                }
            },
            "systemLimits": {"maxPromptsPerUser": 1000, "maxCollectionsPerUser": 100},
            "maintenanceMode": False,
            "updatedAt": now,
            "updatedBy": admin_user_id,
        }

        try:
            await db_manager.create_item("AdminSettings", admin_settings)
            seed_summary["data_created"].append(
                {
                    "type": "admin_settings",
                    "id": admin_settings["id"],
                    "status": "success",
                }
            )
        except Exception as e:
            seed_summary["data_created"].append(
                {
                    "type": "admin_settings",
                    "id": admin_settings["id"],
                    "error": str(e),
                    "status": "error",
                }
            )

        logger.info(f"Test data seeded by {admin_user_id} in {environment} environment")

        return func.HttpResponse(json.dumps(seed_summary), status_code=200, mimetype="application/json")

    except Exception as e:
        logger.error(f"Error in seed_test_data: {e}")
        return func.HttpResponse(
            json.dumps(
                {
                    "error": "Internal Server Error",
                    "message": "Failed to seed test data",
                    "details": str(e),
                }
            ),
            status_code=500,
            mimetype="application/json",
        )


async def get_guest_settings() -> func.HttpResponse:
    """Get guest user settings."""
    try:
        db_manager = get_database_manager()

        try:
            config = await db_manager.read_item(
                container_name="SystemConfig",
                item_id="guest_user_limits",
                partition_key="guest_user_limits",
            )
        except Exception:
            # Default settings if not configured
            config = {
                "id": "guest_user_limits",
                "limits": {
                    "llm_calls_per_day": 5,
                    "prompts_per_day": 10,
                    "collections_per_session": 3,
                    "playbooks_per_session": 2,
                    "session_duration_hours": 24,
                    "enabled": True,
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

        return func.HttpResponse(
            json.dumps(config, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error getting guest settings: {str(e)}")
        raise SutraAPIError(f"Failed to get guest settings: {str(e)}", 500)


async def update_guest_settings(admin_user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """Update guest user settings."""
    try:
        # Parse request body
        try:
            body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json",
            )

        db_manager = get_database_manager()

        # Get existing settings
        try:
            existing_config = await db_manager.read_item(
                container_name="SystemConfig",
                item_id="guest_user_limits",
                partition_key="guest_user_limits",
            )
        except Exception:
            existing_config = {
                "id": "guest_user_limits",
                "limits": {},
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

        # Update settings
        if "limits" in body:
            # Validate limits
            valid_limit_keys = [
                "llm_calls_per_day",
                "prompts_per_day",
                "collections_per_session",
                "playbooks_per_session",
                "session_duration_hours",
                "enabled",
            ]

            for key, value in body["limits"].items():
                if key in valid_limit_keys:
                    if key == "enabled":
                        existing_config["limits"][key] = bool(value)
                    else:
                        existing_config["limits"][key] = max(0, int(value))

        existing_config["updated_at"] = datetime.now(timezone.utc).isoformat()
        existing_config["updated_by"] = admin_user_id

        # Save settings
        if db_manager._development_mode:
            updated_config = existing_config
            logger.info(f"DEV MODE: Would update guest settings: {updated_config}")
        else:
            try:
                updated_config = await db_manager.update_item(container_name="SystemConfig", item=existing_config)
            except Exception:
                updated_config = await db_manager.create_item(
                    container_name="SystemConfig",
                    item=existing_config,
                    partition_key="guest_user_limits",
                )

        logger.info(f"Admin {admin_user_id} updated guest user settings")

        return func.HttpResponse(
            json.dumps(updated_config, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error updating guest settings: {str(e)}")
        raise SutraAPIError(f"Failed to update guest settings: {str(e)}", 500)


async def get_guest_usage_stats_admin(req: func.HttpRequest) -> func.HttpResponse:
    """Get guest usage statistics for admin dashboard."""
    try:
        # Parse query parameters
        params = req.params
        period = params.get("period", "day")  # day, week, month

        db_manager = get_database_manager()

        # Calculate date range
        now = datetime.now(timezone.utc)
        if period == "day":
            start_date = now - timedelta(days=1)
        elif period == "week":
            start_date = now - timedelta(weeks=1)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=1)

        start_iso = start_date.isoformat()

        if db_manager._development_mode:
            # Return mock stats for development
            stats = {
                "period": period,
                "start_date": start_iso,
                "end_date": now.isoformat(),
                "total_sessions": 42,
                "active_sessions": 8,
                "total_llm_calls": 156,
                "total_prompts_created": 89,
                "total_collections_created": 23,
                "total_playbooks_created": 12,
                "avg_calls_per_session": 3.7,
                "conversion_rate": 0.15,  # Percentage of guests who signed up
                "_mock": True,
            }
        else:
            # Get real statistics from database
            query = """
            SELECT
                COUNT(1) as total_sessions,
                SUM(c.usage.llm_calls) as total_llm_calls,
                SUM(c.usage.prompts_created) as total_prompts_created,
                SUM(c.usage.collections_created) as total_collections_created,
                SUM(c.usage.playbooks_created) as total_playbooks_created
            FROM c
            WHERE c.type = 'guest_session'
            AND c.created_at >= @start_date
            """

            parameters = [{"name": "@start_date", "value": start_iso}]

            result = await db_manager.query_items(container_name="GuestSessions", query=query, parameters=parameters)

            stats_data = result[0] if result else {}

            stats = {
                "period": period,
                "start_date": start_iso,
                "end_date": now.isoformat(),
                "total_sessions": stats_data.get("total_sessions", 0),
                "total_llm_calls": stats_data.get("total_llm_calls", 0),
                "total_prompts_created": stats_data.get("total_prompts_created", 0),
                "total_collections_created": stats_data.get("total_collections_created", 0),
                "total_playbooks_created": stats_data.get("total_playbooks_created", 0),
                "avg_calls_per_session": 0,
            }

            if stats["total_sessions"] > 0:
                stats["avg_calls_per_session"] = round(stats["total_llm_calls"] / stats["total_sessions"], 2)

        return func.HttpResponse(
            json.dumps(stats, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error getting guest usage stats: {str(e)}")
        raise SutraAPIError(f"Failed to get guest usage stats: {str(e)}", 500)
