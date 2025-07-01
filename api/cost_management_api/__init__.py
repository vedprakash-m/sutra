import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import azure.functions as func
from azure.functions import HttpRequest, HttpResponse

# NEW: Use unified authentication and validation systems
from shared.unified_auth import auth_required, get_user_from_request
from shared.utils.fieldConverter import convert_snake_to_camel, convert_camel_to_snake
from shared.real_time_cost import get_cost_manager
from shared.models import UserRole, User
from shared.budget import get_enhanced_budget_manager, BudgetConfig
from shared.error_handling import handle_api_error, SutraAPIError


@auth_required(permissions=["cost.read", "cost.manage"])
async def main(req: HttpRequest, user: User) -> HttpResponse:
    """
    Cost Management API endpoint.

    Handles:
    - POST /api/cost/budget/config - Create/update budget configuration
    - GET /api/cost/budget/usage/{entity_id} - Get real-time usage
    - GET /api/cost/budget/predictions/{entity_id} - Get cost predictions
    - POST /api/cost/estimate - Estimate execution cost
    - GET /api/cost/restrictions/{entity_id} - Check access restrictions
    - GET /api/cost/analytics - Get cost analytics (admin only)
    """

    try:
        # User is already authenticated via decorator
        user_info = {
            "user_id": user.id,  # Fixed: use user.id instead of user.user_id
            "email": user.email,
            "role": user.role,  # Fixed: use user.role instead of user.roles[0].value
            "user_tier": "premium",  # Default for now
        }
        budget_manager = get_enhanced_budget_manager()

        method = req.method
        route_params = req.route_params

        # Route to appropriate handler
        if method == "POST" and req.url.find("/budget/config") != -1:
            return await handle_create_budget_config(req, user_info, budget_manager)

        elif method == "GET" and req.url.find("/budget/usage") != -1:
            entity_id = route_params.get("entity_id", user_info["user_id"])
            return await handle_get_usage(entity_id, user_info, budget_manager)

        elif method == "GET" and req.url.find("/budget/predictions") != -1:
            entity_id = route_params.get("entity_id", user_info["user_id"])
            return await handle_get_predictions(entity_id, user_info, budget_manager)

        elif method == "POST" and req.url.find("/estimate") != -1:
            return await handle_estimate_cost(req, user_info, budget_manager)

        elif method == "GET" and req.url.find("/restrictions") != -1:
            entity_id = route_params.get("entity_id", user_info["user_id"])
            return await handle_check_restrictions(entity_id, user_info, budget_manager)

        elif method == "GET" and req.url.find("/analytics") != -1:
            return await handle_get_analytics(req, user_info, budget_manager)

        else:
            return HttpResponse(
                json.dumps({"error": "Invalid endpoint"}),
                status_code=404,
                headers={"Content-Type": "application/json"},
            )

    except Exception as e:
        logging.error(f"Cost management API error: {e}")
        return HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def handle_create_budget_config(
    req: HttpRequest, user_info: Dict[str, Any], budget_manager
) -> HttpResponse:
    """Handle budget configuration creation/update."""
    try:
        request_body = req.get_json()

        # Validate required fields
        required_fields = ["entity_type", "entity_id", "budget_amount", "budget_period"]
        for field in required_fields:
            if field not in request_body:
                return HttpResponse(
                    json.dumps({"error": f"Missing required field: {field}"}),
                    status_code=400,
                    headers={"Content-Type": "application/json"},
                )

        # Check permissions
        entity_id = request_body["entity_id"]
        if not await can_manage_budget(user_info, entity_id):
            return HttpResponse(
                json.dumps({"error": "Insufficient permissions"}),
                status_code=403,
                headers={"Content-Type": "application/json"},
            )

        # Create budget configuration
        config_data = {
            "id": f"budget_{entity_id}_{datetime.now(timezone.utc).isoformat()}",
            "entity_type": request_body["entity_type"],
            "entity_id": entity_id,
            "name": request_body.get("name", f"Budget for {entity_id}"),
            "budget_amount": float(request_body["budget_amount"]),
            "budget_period": request_body["budget_period"],
            "currency": request_body.get("currency", "USD"),
            "alert_thresholds": request_body.get("alert_thresholds", [50, 75, 90, 95]),
            "auto_actions": request_body.get("auto_actions", {}),
            "model_restrictions": request_body.get("model_restrictions", {}),
            "rollover_policy": request_body.get("rollover_policy", "reset"),
            "is_active": request_body.get("is_active", True),
        }

        budget_config = await budget_manager.create_budget_config(config_data)

        return HttpResponse(
            json.dumps(
                {"success": True, "budget_config": budget_config.__dict__}, default=str
            ),
            status_code=201,
            headers={"Content-Type": "application/json"},
        )

    except Exception as e:
        logging.error(f"Failed to create budget config: {e}")
        return HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def handle_get_usage(
    entity_id: str, user_info: Dict[str, Any], budget_manager
) -> HttpResponse:
    """Handle real-time usage retrieval."""
    try:
        # Check permissions
        if not await can_view_budget(user_info, entity_id):
            return HttpResponse(
                json.dumps({"error": "Insufficient permissions"}),
                status_code=403,
                headers={"Content-Type": "application/json"},
            )

        # Get real-time usage
        usage_data = await budget_manager.get_real_time_usage(entity_id)
        budget_config = await budget_manager.get_budget_config(entity_id)

        response_data = {
            "entity_id": entity_id,
            "current_spend": usage_data.get("current_spend", 0),
            "execution_count": usage_data.get("execution_count", 0),
            "budget_utilization": usage_data.get("budget_utilization", 0),
            "alerts_triggered": usage_data.get("alerts_triggered", []),
            "restrictions_active": usage_data.get("restrictions_active", []),
            "model_usage": usage_data.get("model_usage", {}),
            "cost_breakdown": usage_data.get("cost_breakdown", {}),
        }

        if budget_config:
            response_data.update(
                {
                    "budget_amount": budget_config.budget_amount,
                    "budget_period": budget_config.budget_period,
                    "remaining_budget": budget_config.budget_amount
                    - usage_data.get("current_spend", 0),
                    "alert_thresholds": budget_config.alert_thresholds,
                }
            )

        return HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

    except Exception as e:
        logging.error(f"Failed to get usage data: {e}")
        return HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def handle_get_predictions(
    entity_id: str, user_info: Dict[str, Any], budget_manager
) -> HttpResponse:
    """Handle cost predictions retrieval."""
    try:
        # Check permissions
        if not await can_view_budget(user_info, entity_id):
            return HttpResponse(
                json.dumps({"error": "Insufficient permissions"}),
                status_code=403,
                headers={"Content-Type": "application/json"},
            )

        # Generate predictions
        predictions = await budget_manager.generate_cost_predictions(entity_id)

        return HttpResponse(
            json.dumps(predictions, default=str),
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

    except Exception as e:
        logging.error(f"Failed to get predictions: {e}")
        return HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def handle_estimate_cost(
    req: HttpRequest, user_info: Dict[str, Any], budget_manager
) -> HttpResponse:
    """Handle execution cost estimation."""
    try:
        request_body = req.get_json()

        # Validate required fields
        required_fields = ["model", "prompt"]
        for field in required_fields:
            if field not in request_body:
                return HttpResponse(
                    json.dumps({"error": f"Missing required field: {field}"}),
                    status_code=400,
                    headers={"Content-Type": "application/json"},
                )

        model = request_body["model"]
        prompt = request_body["prompt"]
        max_tokens = request_body.get("max_tokens", 1000)

        # Estimate cost
        estimate = await budget_manager.estimate_execution_cost(
            model, prompt, max_tokens
        )

        # Check budget impact for the user
        user_id = user_info["user_id"]
        budget_check = await budget_manager.check_pre_execution_budget(
            user_id, estimate["estimated_cost"], model
        )

        response_data = {**estimate, "budget_check": budget_check}

        return HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

    except Exception as e:
        logging.error(f"Failed to estimate cost: {e}")
        return HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def handle_check_restrictions(
    entity_id: str, user_info: Dict[str, Any], budget_manager
) -> HttpResponse:
    """Handle access restrictions check."""
    try:
        # Check permissions
        if not await can_view_budget(user_info, entity_id):
            return HttpResponse(
                json.dumps({"error": "Insufficient permissions"}),
                status_code=403,
                headers={"Content-Type": "application/json"},
            )

        # Check restrictions
        restrictions = await budget_manager.check_access_restrictions(entity_id)

        return HttpResponse(
            json.dumps(restrictions, default=str),
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

    except Exception as e:
        logging.error(f"Failed to check restrictions: {e}")
        return HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def handle_get_analytics(
    req: HttpRequest, user_info: Dict[str, Any], budget_manager
) -> HttpResponse:
    """Handle cost analytics retrieval (admin only)."""
    try:
        # Check admin permissions
        if user_info.get("role") != UserRole.ADMIN:
            return HttpResponse(
                json.dumps({"error": "Admin access required"}),
                status_code=403,
                headers={"Content-Type": "application/json"},
            )

        # Get query parameters
        time_period = req.params.get("period", "monthly")
        entity_type = req.params.get("entity_type", "all")

        # Generate analytics report
        analytics_data = {
            "system_overview": await get_system_cost_overview(
                budget_manager, time_period
            ),
            "top_users": await get_top_users_by_cost(budget_manager, time_period),
            "model_usage": await get_model_usage_analytics(budget_manager, time_period),
            "budget_alerts": await get_budget_alerts_summary(budget_manager),
            "cost_trends": await get_cost_trends(budget_manager, time_period),
        }

        return HttpResponse(
            json.dumps(analytics_data, default=str),
            status_code=200,
            headers={"Content-Type": "application/json"},
        )

    except Exception as e:
        logging.error(f"Failed to get analytics: {e}")
        return HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def can_manage_budget(user_info: Dict[str, Any], entity_id: str) -> bool:
    """Check if user can manage budget for the entity."""
    user_id = user_info["user_id"]
    user_role = user_info.get("role", UserRole.USER)

    # Admins can manage any budget
    if user_role == UserRole.ADMIN:
        return True

    # Users can manage their own budget
    if entity_id == user_id:
        return True

    # Team managers can manage team budgets (simplified check)
    if user_role in [UserRole.PROMPT_MANAGER, UserRole.CONTRIBUTOR]:
        # In a real implementation, we'd check team membership here
        return True

    return False


async def can_view_budget(user_info: Dict[str, Any], entity_id: str) -> bool:
    """Check if user can view budget for the entity."""
    user_id = user_info["user_id"]
    user_role = user_info.get("role", UserRole.USER)

    # Admins can view any budget
    if user_role == UserRole.ADMIN:
        return True

    # Users can view their own budget
    if entity_id == user_id:
        return True

    # Team members can view team budgets (simplified check)
    return True


async def get_system_cost_overview(budget_manager, time_period: str) -> Dict[str, Any]:
    """Get system-wide cost overview."""
    # Placeholder implementation
    return {
        "total_spend": 1250.50,
        "total_users": 45,
        "total_executions": 1834,
        "average_cost_per_user": 27.79,
        "period": time_period,
    }


async def get_top_users_by_cost(
    budget_manager, time_period: str
) -> List[Dict[str, Any]]:
    """Get top users by cost."""
    # Placeholder implementation
    return [
        {"user_id": "user1", "cost": 156.78, "executions": 234},
        {"user_id": "user2", "cost": 134.56, "executions": 198},
        {"user_id": "user3", "cost": 112.34, "executions": 167},
    ]


async def get_model_usage_analytics(budget_manager, time_period: str) -> Dict[str, Any]:
    """Get model usage analytics."""
    # Placeholder implementation
    return {
        "gpt-4": {"usage_count": 456, "total_cost": 234.56, "avg_cost": 0.51},
        "gpt-3.5-turbo": {"usage_count": 1234, "total_cost": 123.45, "avg_cost": 0.10},
        "claude-3-sonnet": {"usage_count": 234, "total_cost": 89.12, "avg_cost": 0.38},
    }


async def get_budget_alerts_summary(budget_manager) -> Dict[str, Any]:
    """Get budget alerts summary."""
    # Placeholder implementation
    return {
        "active_alerts": 3,
        "critical_alerts": 1,
        "users_over_budget": 2,
        "recent_restrictions": 1,
    }


async def get_cost_trends(budget_manager, time_period: str) -> Dict[str, Any]:
    """Get cost trends."""
    # Placeholder implementation
    return {
        "trend_direction": "increasing",
        "growth_rate": 12.5,
        "seasonal_patterns": ["weekday_peaks", "month_end_spikes"],
    }
