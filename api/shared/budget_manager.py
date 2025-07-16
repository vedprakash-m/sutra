"""
Budget Enforcement System for Sutra Multi-LLM Prompt Studio.
Provides comprehensive budget management, spending limits, and admin controls.
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from .cost_tracker import CostSummary, CostTracker
from .cost_tracking_middleware import BudgetValidationError


class BudgetPeriod(Enum):
    """Budget period types."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class BudgetAction(Enum):
    """Actions to take when budget limits are reached."""

    WARN_ONLY = "warn_only"
    RESTRICT_EXPENSIVE = "restrict_expensive"
    RESTRICT_ALL = "restrict_all"
    REQUIRE_APPROVAL = "require_approval"
    BLOCK_EXECUTION = "block_execution"


class BudgetStatus(Enum):
    """Budget status levels."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    EXCEEDED = "exceeded"
    SUSPENDED = "suspended"


@dataclass
class BudgetLimit:
    """Individual budget limit configuration."""

    id: str
    name: str
    amount: Decimal
    period: BudgetPeriod
    threshold_percentages: List[int]  # [50, 75, 90, 95] for warnings
    actions: Dict[int, BudgetAction]  # {90: "restrict_expensive", 95: "require_approval"}
    applies_to: Dict[str, Any]  # {"users": ["all"], "providers": ["openai", "anthropic"]}
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class BudgetUsage:
    """Current budget usage tracking."""

    budget_id: str
    period_start: datetime
    period_end: datetime
    total_spent: Decimal
    budget_limit: Decimal
    usage_percentage: float
    status: BudgetStatus
    triggered_actions: List[str]
    remaining_amount: Decimal
    forecast_end_spend: Decimal
    days_remaining: int


@dataclass
class AdminOverride:
    """Admin override for budget restrictions."""

    id: str
    budget_id: str
    user_id: str
    admin_user_id: str
    override_type: str  # "temporary_increase", "permanent_increase", "emergency_access"
    original_limit: Decimal
    new_limit: Decimal
    reason: str
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime


@dataclass
class BudgetForecast:
    """Budget spending forecast."""

    budget_id: str
    forecast_date: datetime
    predicted_spend: Decimal
    confidence_interval: Tuple[Decimal, Decimal]  # (low, high)
    factors: Dict[str, Any]  # Usage patterns, trends, etc.
    recommendations: List[str]


class BudgetManager:
    """
    Production-grade budget enforcement system.

    Features:
    - Flexible budget configuration (daily/weekly/monthly/quarterly/yearly)
    - Progressive action enforcement (warn → restrict → block)
    - Admin override capabilities
    - Predictive spending forecasting
    - Multi-tenant budget isolation
    """

    def __init__(self, cosmos_client: CosmosClient, database_name: str, cost_tracker: CostTracker):
        self.cosmos_client = cosmos_client
        self.database_name = database_name
        self.cost_tracker = cost_tracker
        self.logger = logging.getLogger(__name__)

        # Budget collections
        self.budget_limits_container = "BudgetLimits"
        self.budget_usage_container = "BudgetUsage"
        self.admin_overrides_container = "AdminOverrides"
        self.budget_forecasts_container = "BudgetForecasts"

        # Default budget configurations
        self.default_budgets = {
            "individual_monthly": {
                "amount": Decimal("100.00"),
                "period": BudgetPeriod.MONTHLY,
                "thresholds": [50, 75, 90, 95],
                "actions": {
                    75: BudgetAction.WARN_ONLY,
                    90: BudgetAction.RESTRICT_EXPENSIVE,
                    95: BudgetAction.REQUIRE_APPROVAL,
                    100: BudgetAction.BLOCK_EXECUTION,
                },
            },
            "team_monthly": {
                "amount": Decimal("1000.00"),
                "period": BudgetPeriod.MONTHLY,
                "thresholds": [60, 80, 90, 95],
                "actions": {
                    80: BudgetAction.WARN_ONLY,
                    90: BudgetAction.RESTRICT_EXPENSIVE,
                    95: BudgetAction.REQUIRE_APPROVAL,
                    100: BudgetAction.BLOCK_EXECUTION,
                },
            },
            "organization_quarterly": {
                "amount": Decimal("10000.00"),
                "period": BudgetPeriod.QUARTERLY,
                "thresholds": [70, 85, 95, 98],
                "actions": {
                    85: BudgetAction.WARN_ONLY,
                    95: BudgetAction.RESTRICT_EXPENSIVE,
                    98: BudgetAction.REQUIRE_APPROVAL,
                    100: BudgetAction.BLOCK_EXECUTION,
                },
            },
        }

    async def create_budget_limit(
        self,
        name: str,
        amount: Decimal,
        period: BudgetPeriod,
        applies_to: Dict[str, Any],
        admin_user_id: str,
        threshold_percentages: Optional[List[int]] = None,
        actions: Optional[Dict[int, BudgetAction]] = None,
    ) -> BudgetLimit:
        """Create a new budget limit."""
        try:
            budget_id = f"budget_{datetime.now(timezone.utc).timestamp()}"

            # Use defaults if not provided
            if threshold_percentages is None:
                threshold_percentages = [50, 75, 90, 95]

            if actions is None:
                actions = {
                    75: BudgetAction.WARN_ONLY,
                    90: BudgetAction.RESTRICT_EXPENSIVE,
                    95: BudgetAction.REQUIRE_APPROVAL,
                    100: BudgetAction.BLOCK_EXECUTION,
                }

            budget_limit = BudgetLimit(
                id=budget_id,
                name=name,
                amount=amount,
                period=period,
                threshold_percentages=threshold_percentages,
                actions={k: v for k, v in actions.items()},  # Convert enum values
                applies_to=applies_to,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            # Store in database
            await self._store_budget_limit(budget_limit)

            self.logger.info(f"Created budget limit: {name} (${float(amount):.2f} {period.value})")
            return budget_limit

        except Exception as e:
            self.logger.error(f"Error creating budget limit: {str(e)}")
            raise

    async def _store_budget_limit(self, budget_limit: BudgetLimit) -> None:
        """Store budget limit in database."""
        try:
            container = self.cosmos_client.get_database_client(self.database_name).get_container_client(
                self.budget_limits_container
            )

            # Convert to dictionary for storage
            budget_dict = asdict(budget_limit)
            budget_dict["amount"] = float(budget_limit.amount)
            budget_dict["period"] = budget_limit.period.value
            budget_dict["actions"] = {
                str(k): v.value if isinstance(v, BudgetAction) else v for k, v in budget_limit.actions.items()
            }
            budget_dict["created_at"] = budget_limit.created_at.isoformat()
            budget_dict["updated_at"] = budget_limit.updated_at.isoformat()

            await container.create_item(budget_dict)

        except Exception as e:
            self.logger.error(f"Error storing budget limit: {str(e)}")
            raise

    async def get_applicable_budgets(
        self, user_id: str, provider: Optional[str] = None, organization_id: Optional[str] = None
    ) -> List[BudgetLimit]:
        """Get all budget limits applicable to a user/provider/organization."""
        try:
            container = self.cosmos_client.get_database_client(self.database_name).get_container_client(
                self.budget_limits_container
            )

            query = "SELECT * FROM c WHERE c.is_active = true"

            applicable_budgets = []
            async for item in container.query_items(query=query):
                budget = self._dict_to_budget_limit(item)

                # Check if budget applies to this user/provider/org
                if self._budget_applies_to(budget, user_id, provider, organization_id):
                    applicable_budgets.append(budget)

            return applicable_budgets

        except Exception as e:
            self.logger.error(f"Error getting applicable budgets: {str(e)}")
            return []

    def _budget_applies_to(
        self, budget: BudgetLimit, user_id: str, provider: Optional[str], organization_id: Optional[str]
    ) -> bool:
        """Check if a budget applies to the given context."""
        applies_to = budget.applies_to

        # Check user applicability
        if "users" in applies_to:
            user_list = applies_to["users"]
            if user_list != ["all"] and user_id not in user_list:
                return False

        # Check provider applicability
        if provider and "providers" in applies_to:
            provider_list = applies_to["providers"]
            if provider_list != ["all"] and provider not in provider_list:
                return False

        # Check organization applicability
        if organization_id and "organizations" in applies_to:
            org_list = applies_to["organizations"]
            if org_list != ["all"] and organization_id not in org_list:
                return False

        return True

    def _dict_to_budget_limit(self, item: Dict) -> BudgetLimit:
        """Convert dictionary to BudgetLimit object."""
        return BudgetLimit(
            id=item["id"],
            name=item["name"],
            amount=Decimal(str(item["amount"])),
            period=BudgetPeriod(item["period"]),
            threshold_percentages=item["threshold_percentages"],
            actions={int(k): BudgetAction(v) for k, v in item["actions"].items()},
            applies_to=item["applies_to"],
            is_active=item["is_active"],
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
        )

    async def check_budget_enforcement(
        self, user_id: str, estimated_cost: Decimal, provider: str, model: str, organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check budget enforcement and return actions to take.

        Returns:
            Dict with enforcement decisions and required actions
        """
        try:
            # Get applicable budgets
            budgets = await self.get_applicable_budgets(user_id, provider, organization_id)

            if not budgets:
                return {
                    "can_execute": True,
                    "enforcement_actions": [],
                    "warnings": [],
                    "budget_status": "no_budgets_configured",
                }

            enforcement_actions = []
            warnings = []
            most_restrictive_action = None
            can_execute = True

            # Check each applicable budget
            for budget in budgets:
                usage = await self.get_current_budget_usage(budget.id, user_id)

                if not usage:
                    continue

                projected_spend = usage.total_spent + estimated_cost
                projected_percentage = float((projected_spend / budget.amount) * 100)

                # Check what actions should be triggered
                for threshold, action in budget.actions.items():
                    if projected_percentage >= threshold:
                        action_info = {
                            "budget_id": budget.id,
                            "budget_name": budget.name,
                            "threshold": threshold,
                            "action": action.value,
                            "current_spend": float(usage.total_spent),
                            "estimated_cost": float(estimated_cost),
                            "projected_spend": float(projected_spend),
                            "projected_percentage": projected_percentage,
                            "budget_limit": float(budget.amount),
                        }

                        if action == BudgetAction.BLOCK_EXECUTION:
                            can_execute = False
                            most_restrictive_action = action
                            enforcement_actions.append(action_info)
                        elif action == BudgetAction.REQUIRE_APPROVAL:
                            # Check if there's an admin override
                            override = await self.check_admin_override(budget.id, user_id)
                            if not override:
                                can_execute = False
                                most_restrictive_action = action
                            enforcement_actions.append(action_info)
                        elif action == BudgetAction.RESTRICT_EXPENSIVE:
                            # Check if this is an expensive model
                            if self._is_expensive_model(provider, model):
                                can_execute = False
                                most_restrictive_action = action
                            enforcement_actions.append(action_info)
                        elif action == BudgetAction.RESTRICT_ALL:
                            can_execute = False
                            most_restrictive_action = action
                            enforcement_actions.append(action_info)
                        else:  # WARN_ONLY
                            warnings.append(action_info)

            budget_status = await self._determine_overall_status(budgets, user_id)

            return {
                "can_execute": can_execute,
                "enforcement_actions": enforcement_actions,
                "warnings": warnings,
                "most_restrictive_action": most_restrictive_action.value if most_restrictive_action else None,
                "budget_status": budget_status,
            }

        except Exception as e:
            self.logger.error(f"Error checking budget enforcement: {str(e)}")
            # In case of error, allow execution but log the issue
            return {"can_execute": True, "enforcement_actions": [], "warnings": [{"error": str(e)}], "budget_status": "error"}

    def _is_expensive_model(self, provider: str, model: str) -> bool:
        """Determine if a model is considered expensive."""
        expensive_models = {
            "openai": ["gpt-4", "gpt-4-turbo"],
            "anthropic": ["claude-3-opus-20240229"],
            "google": ["gemini-1.5-pro"],
        }

        return model in expensive_models.get(provider, [])

    async def _determine_overall_status(self, budgets: List[BudgetLimit], user_id: str) -> str:
        """Determine overall budget status across all applicable budgets."""
        if not budgets:
            return "no_budgets"

        worst_status = BudgetStatus.HEALTHY

        for budget in budgets:
            usage = await self.get_current_budget_usage(budget.id, user_id)
            if usage and usage.status.value > worst_status.value:
                worst_status = usage.status

        return worst_status.value

    async def get_current_budget_usage(self, budget_id: str, user_id: str) -> Optional[BudgetUsage]:
        """Get current budget usage for a specific budget."""
        try:
            # Get budget configuration
            budget = await self.get_budget_by_id(budget_id)
            if not budget:
                return None

            # Calculate period boundaries
            period_start, period_end = self._get_period_boundaries(budget.period)

            # Get spending for this period
            cost_summary = await self.cost_tracker.get_cost_summary(
                user_id=user_id, start_date=period_start, end_date=period_end
            )

            # Calculate usage metrics
            total_spent = cost_summary.total_cost
            usage_percentage = float((total_spent / budget.amount) * 100)
            remaining_amount = budget.amount - total_spent

            # Determine status
            status = self._calculate_budget_status(usage_percentage, budget)

            # Calculate forecast
            forecast_spend = await self._calculate_forecast_spend(budget, total_spent, period_start, period_end)

            # Determine triggered actions
            triggered_actions = []
            for threshold, action in budget.actions.items():
                if usage_percentage >= threshold:
                    triggered_actions.append(f"{threshold}%: {action.value}")

            # Calculate days remaining in period
            days_remaining = (period_end - datetime.now(timezone.utc)).days

            return BudgetUsage(
                budget_id=budget_id,
                period_start=period_start,
                period_end=period_end,
                total_spent=total_spent,
                budget_limit=budget.amount,
                usage_percentage=usage_percentage,
                status=status,
                triggered_actions=triggered_actions,
                remaining_amount=remaining_amount,
                forecast_end_spend=forecast_spend,
                days_remaining=max(0, days_remaining),
            )

        except Exception as e:
            self.logger.error(f"Error getting budget usage: {str(e)}")
            return None

    def _get_period_boundaries(self, period: BudgetPeriod) -> Tuple[datetime, datetime]:
        """Get start and end dates for a budget period."""
        now = datetime.now(timezone.utc)

        if period == BudgetPeriod.DAILY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period == BudgetPeriod.WEEKLY:
            days_since_monday = now.weekday()
            start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(weeks=1)
        elif period == BudgetPeriod.MONTHLY:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end = start.replace(year=now.year + 1, month=1)
            else:
                end = start.replace(month=now.month + 1)
        elif period == BudgetPeriod.QUARTERLY:
            quarter = (now.month - 1) // 3 + 1
            start = now.replace(month=(quarter - 1) * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            if quarter == 4:
                end = start.replace(year=now.year + 1, month=1)
            else:
                end = start.replace(month=quarter * 3 + 1)
        elif period == BudgetPeriod.YEARLY:
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=now.year + 1)
        else:
            raise ValueError(f"Unknown budget period: {period}")

        return start, end

    def _calculate_budget_status(self, usage_percentage: float, budget: BudgetLimit) -> BudgetStatus:
        """Calculate budget status based on usage percentage."""
        if usage_percentage >= 100:
            return BudgetStatus.EXCEEDED
        elif usage_percentage >= 95:
            return BudgetStatus.CRITICAL
        elif usage_percentage >= 75:
            return BudgetStatus.WARNING
        else:
            return BudgetStatus.HEALTHY

    async def _calculate_forecast_spend(
        self, budget: BudgetLimit, current_spend: Decimal, period_start: datetime, period_end: datetime
    ) -> Decimal:
        """Calculate forecasted spending for end of period."""
        try:
            now = datetime.now(timezone.utc)

            # Calculate time elapsed and remaining
            total_period_hours = (period_end - period_start).total_seconds() / 3600
            elapsed_hours = (now - period_start).total_seconds() / 3600
            remaining_hours = (period_end - now).total_seconds() / 3600

            if elapsed_hours <= 0:
                return current_spend

            if remaining_hours <= 0:
                return current_spend

            # Simple linear extrapolation (could be enhanced with ML)
            spend_rate_per_hour = current_spend / Decimal(str(elapsed_hours))
            forecasted_additional_spend = spend_rate_per_hour * Decimal(str(remaining_hours))

            return current_spend + forecasted_additional_spend

        except Exception as e:
            self.logger.error(f"Error calculating forecast: {str(e)}")
            return current_spend

    async def get_budget_by_id(self, budget_id: str) -> Optional[BudgetLimit]:
        """Get budget configuration by ID."""
        try:
            container = self.cosmos_client.get_database_client(self.database_name).get_container_client(
                self.budget_limits_container
            )

            query = "SELECT * FROM c WHERE c.id = @budget_id"
            parameters = [{"name": "@budget_id", "value": budget_id}]

            async for item in container.query_items(query=query, parameters=parameters):
                return self._dict_to_budget_limit(item)

            return None

        except Exception as e:
            self.logger.error(f"Error getting budget by ID: {str(e)}")
            return None

    async def create_admin_override(
        self,
        budget_id: str,
        user_id: str,
        admin_user_id: str,
        override_type: str,
        new_limit: Decimal,
        reason: str,
        expires_hours: Optional[int] = None,
    ) -> AdminOverride:
        """Create an admin override for budget restrictions."""
        try:
            # Get original budget
            budget = await self.get_budget_by_id(budget_id)
            if not budget:
                raise ValueError(f"Budget not found: {budget_id}")

            override_id = f"override_{datetime.now(timezone.utc).timestamp()}"
            expires_at = None

            if expires_hours:
                expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)

            override = AdminOverride(
                id=override_id,
                budget_id=budget_id,
                user_id=user_id,
                admin_user_id=admin_user_id,
                override_type=override_type,
                original_limit=budget.amount,
                new_limit=new_limit,
                reason=reason,
                expires_at=expires_at,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )

            # Store in database
            await self._store_admin_override(override)

            self.logger.info(
                f"Created admin override: {override_type} for user {user_id} "
                f"(${float(budget.amount):.2f} → ${float(new_limit):.2f})"
            )

            return override

        except Exception as e:
            self.logger.error(f"Error creating admin override: {str(e)}")
            raise

    async def _store_admin_override(self, override: AdminOverride) -> None:
        """Store admin override in database."""
        try:
            container = self.cosmos_client.get_database_client(self.database_name).get_container_client(
                self.admin_overrides_container
            )

            override_dict = asdict(override)
            override_dict["original_limit"] = float(override.original_limit)
            override_dict["new_limit"] = float(override.new_limit)
            override_dict["created_at"] = override.created_at.isoformat()

            if override.expires_at:
                override_dict["expires_at"] = override.expires_at.isoformat()

            await container.create_item(override_dict)

        except Exception as e:
            self.logger.error(f"Error storing admin override: {str(e)}")
            raise

    async def check_admin_override(self, budget_id: str, user_id: str) -> Optional[AdminOverride]:
        """Check if there's an active admin override for a user/budget."""
        try:
            container = self.cosmos_client.get_database_client(self.database_name).get_container_client(
                self.admin_overrides_container
            )

            query = """
                SELECT * FROM c
                WHERE c.budget_id = @budget_id
                AND c.user_id = @user_id
                AND c.is_active = true
            """
            parameters = [{"name": "@budget_id", "value": budget_id}, {"name": "@user_id", "value": user_id}]

            now = datetime.now(timezone.utc)

            async for item in container.query_items(query=query, parameters=parameters):
                # Check if override is still valid
                if item.get("expires_at"):
                    expires_at = datetime.fromisoformat(item["expires_at"])
                    if now > expires_at:
                        # Override has expired, deactivate it
                        await self._deactivate_override(item["id"])
                        continue

                return AdminOverride(
                    id=item["id"],
                    budget_id=item["budget_id"],
                    user_id=item["user_id"],
                    admin_user_id=item["admin_user_id"],
                    override_type=item["override_type"],
                    original_limit=Decimal(str(item["original_limit"])),
                    new_limit=Decimal(str(item["new_limit"])),
                    reason=item["reason"],
                    expires_at=datetime.fromisoformat(item["expires_at"]) if item.get("expires_at") else None,
                    is_active=item["is_active"],
                    created_at=datetime.fromisoformat(item["created_at"]),
                )

            return None

        except Exception as e:
            self.logger.error(f"Error checking admin override: {str(e)}")
            return None

    async def _deactivate_override(self, override_id: str) -> None:
        """Deactivate an expired override."""
        try:
            container = self.cosmos_client.get_database_client(self.database_name).get_container_client(
                self.admin_overrides_container
            )

            # This would need proper update logic in a real implementation
            # For now, we'll log it
            self.logger.info(f"Override {override_id} has expired and should be deactivated")

        except Exception as e:
            self.logger.error(f"Error deactivating override: {str(e)}")

    async def get_budget_report(
        self, user_id: Optional[str] = None, organization_id: Optional[str] = None, period_days: int = 30
    ) -> Dict[str, Any]:
        """Generate comprehensive budget report."""
        try:
            # Get applicable budgets
            budgets = await self.get_applicable_budgets(user_id, organization_id=organization_id)

            if not budgets:
                return {"status": "no_budgets_configured", "message": "No budget limits configured"}

            report = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "period_days": period_days,
                "user_id": user_id,
                "organization_id": organization_id,
                "budgets": [],
                "overall_status": "healthy",
                "total_spent": 0.0,
                "total_budgeted": 0.0,
                "recommendations": [],
            }

            total_spent = Decimal("0")
            total_budgeted = Decimal("0")
            worst_status = BudgetStatus.HEALTHY

            for budget in budgets:
                usage = await self.get_current_budget_usage(budget.id, user_id or "all")

                if usage:
                    budget_info = {
                        "budget_id": budget.id,
                        "name": budget.name,
                        "period": budget.period.value,
                        "amount": float(budget.amount),
                        "spent": float(usage.total_spent),
                        "remaining": float(usage.remaining_amount),
                        "usage_percentage": usage.usage_percentage,
                        "status": usage.status.value,
                        "forecast_end_spend": float(usage.forecast_end_spend),
                        "days_remaining": usage.days_remaining,
                        "triggered_actions": usage.triggered_actions,
                    }

                    report["budgets"].append(budget_info)
                    total_spent += usage.total_spent
                    total_budgeted += budget.amount

                    if usage.status.value > worst_status.value:
                        worst_status = usage.status

            report["total_spent"] = float(total_spent)
            report["total_budgeted"] = float(total_budgeted)
            report["overall_status"] = worst_status.value

            # Generate recommendations
            report["recommendations"] = await self._generate_budget_recommendations(budgets, user_id)

            return report

        except Exception as e:
            self.logger.error(f"Error generating budget report: {str(e)}")
            return {"error": str(e)}

    async def _generate_budget_recommendations(self, budgets: List[BudgetLimit], user_id: Optional[str]) -> List[str]:
        """Generate budget optimization recommendations."""
        recommendations = []

        for budget in budgets:
            usage = await self.get_current_budget_usage(budget.id, user_id or "all")

            if usage:
                if usage.usage_percentage > 90:
                    recommendations.append(
                        f"Budget '{budget.name}' is at {usage.usage_percentage:.1f}% - "
                        f"consider optimizing usage or requesting increase"
                    )

                if usage.forecast_end_spend > budget.amount:
                    overage = usage.forecast_end_spend - budget.amount
                    recommendations.append(
                        f"Budget '{budget.name}' forecasted to exceed by "
                        f"${float(overage):.2f} - consider cost reduction measures"
                    )

                if usage.days_remaining > 0 and usage.usage_percentage < 25:
                    recommendations.append(
                        f"Budget '{budget.name}' is underutilized ({usage.usage_percentage:.1f}%) - "
                        f"could be reduced or reallocated"
                    )

        return recommendations


# Singleton instance
_budget_manager_instance = None


def get_budget_manager(
    cosmos_client: Optional[CosmosClient] = None, database_name: str = "SutraDB", cost_tracker: Optional[CostTracker] = None
) -> Optional[BudgetManager]:
    """Get or create budget manager instance."""
    global _budget_manager_instance

    if _budget_manager_instance is None and cosmos_client and cost_tracker:
        _budget_manager_instance = BudgetManager(cosmos_client, database_name, cost_tracker)

    return _budget_manager_instance
