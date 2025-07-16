"""
Real-time cost tracking system for LLM API usage.
Provides comprehensive cost monitoring, analytics, and budget management.
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


class CostAlertLevel(Enum):
    """Alert levels for cost thresholds."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class CostEntry:
    """Individual cost tracking entry."""

    id: str
    user_id: str
    session_id: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    input_cost: Decimal
    output_cost: Decimal
    total_cost: Decimal
    timestamp: datetime
    execution_time_ms: int
    request_id: str
    metadata: Dict[str, Any]


@dataclass
class CostSummary:
    """Cost summary for a period or entity."""

    total_requests: int
    total_tokens: int
    total_cost: Decimal
    cost_by_provider: Dict[str, Decimal]
    cost_by_model: Dict[str, Decimal]
    average_cost_per_request: Decimal
    average_tokens_per_request: float
    period_start: datetime
    period_end: datetime


@dataclass
class CostAlert:
    """Cost alert notification."""

    id: str
    level: CostAlertLevel
    message: str
    threshold_amount: Decimal
    current_amount: Decimal
    user_id: Optional[str]
    timestamp: datetime
    acknowledged: bool = False


class CostTracker:
    """
    Production-grade cost tracking system for LLM API usage.

    Features:
    - Real-time cost calculation and tracking
    - Provider-specific pricing models
    - Historical analytics and reporting
    - Budget threshold monitoring
    - Alert system for cost overruns
    """

    def __init__(self, cosmos_client: CosmosClient, database_name: str):
        self.cosmos_client = cosmos_client
        self.database_name = database_name
        self.logger = logging.getLogger(__name__)

        # Cost tracking collections
        self.cost_entries_container = "CostEntries"
        self.cost_summaries_container = "CostSummaries"
        self.cost_alerts_container = "CostAlerts"
        self.budget_settings_container = "BudgetSettings"

        # Current API pricing (per 1K tokens) - Updated as of 2024
        self.pricing_models = {
            "openai": {
                "gpt-4": {"input": Decimal("0.03"), "output": Decimal("0.06")},
                "gpt-4-turbo": {"input": Decimal("0.01"), "output": Decimal("0.03")},
                "gpt-4o": {"input": Decimal("0.005"), "output": Decimal("0.015")},
                "gpt-3.5-turbo": {"input": Decimal("0.0015"), "output": Decimal("0.002")},
            },
            "anthropic": {
                "claude-3-5-sonnet-20241022": {"input": Decimal("0.003"), "output": Decimal("0.015")},
                "claude-3-haiku-20240307": {"input": Decimal("0.00025"), "output": Decimal("0.00125")},
                "claude-3-opus-20240229": {"input": Decimal("0.015"), "output": Decimal("0.075")},
            },
            "google": {
                "gemini-1.5-pro": {"input": Decimal("0.00125"), "output": Decimal("0.005")},
                "gemini-1.5-flash": {"input": Decimal("0.000075"), "output": Decimal("0.0003")},
                "gemini-pro": {"input": Decimal("0.0005"), "output": Decimal("0.0015")},
            },
        }

        # Alert thresholds (configurable per user/organization)
        self.default_thresholds = {
            CostAlertLevel.INFO: Decimal("10.00"),  # $10
            CostAlertLevel.WARNING: Decimal("50.00"),  # $50
            CostAlertLevel.CRITICAL: Decimal("100.00"),  # $100
            CostAlertLevel.EMERGENCY: Decimal("200.00"),  # $200
        }

    async def track_llm_usage(
        self,
        user_id: str,
        session_id: str,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        execution_time_ms: int,
        request_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CostEntry:
        """
        Track LLM API usage and calculate costs.

        Args:
            user_id: User identifier
            session_id: Session identifier
            provider: LLM provider (openai, anthropic, google)
            model: Model identifier
            prompt_tokens: Input tokens used
            completion_tokens: Output tokens generated
            execution_time_ms: Request execution time
            request_id: Unique request identifier
            metadata: Additional metadata

        Returns:
            CostEntry: Created cost entry with calculated costs
        """
        try:
            # Calculate costs
            total_tokens = prompt_tokens + completion_tokens
            input_cost, output_cost, total_cost = self._calculate_cost(provider, model, prompt_tokens, completion_tokens)

            # Create cost entry
            cost_entry = CostEntry(
                id=f"cost_{request_id}_{datetime.now(timezone.utc).timestamp()}",
                user_id=user_id,
                session_id=session_id,
                provider=provider,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                input_cost=input_cost,
                output_cost=output_cost,
                total_cost=total_cost,
                timestamp=datetime.now(timezone.utc),
                execution_time_ms=execution_time_ms,
                request_id=request_id,
                metadata=metadata or {},
            )

            # Store in database
            await self._store_cost_entry(cost_entry)

            # Check for budget alerts
            await self._check_budget_alerts(user_id, total_cost)

            self.logger.info(f"Tracked LLM usage: {provider}/{model} - " f"${float(total_cost):.6f} ({total_tokens} tokens)")

            return cost_entry

        except Exception as e:
            self.logger.error(f"Error tracking LLM usage: {str(e)}")
            raise

    def _calculate_cost(
        self, provider: str, model: str, prompt_tokens: int, completion_tokens: int
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """Calculate costs based on provider pricing."""
        try:
            pricing = self.pricing_models.get(provider, {}).get(model)
            if not pricing:
                self.logger.warning(f"No pricing found for {provider}/{model}")
                return Decimal("0"), Decimal("0"), Decimal("0")

            # Calculate costs per 1K tokens
            input_cost = (Decimal(prompt_tokens) / 1000) * pricing["input"]
            output_cost = (Decimal(completion_tokens) / 1000) * pricing["output"]
            total_cost = input_cost + output_cost

            # Round to 6 decimal places
            input_cost = input_cost.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
            output_cost = output_cost.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
            total_cost = total_cost.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

            return input_cost, output_cost, total_cost

        except Exception as e:
            self.logger.error(f"Error calculating cost: {str(e)}")
            return Decimal("0"), Decimal("0"), Decimal("0")

    async def _store_cost_entry(self, cost_entry: CostEntry) -> None:
        """Store cost entry in database."""
        try:
            container = self.cosmos_client.get_database_client(self.database_name).get_container_client(
                self.cost_entries_container
            )

            # Convert to dictionary for storage
            entry_dict = asdict(cost_entry)
            entry_dict["timestamp"] = cost_entry.timestamp.isoformat()
            entry_dict["input_cost"] = float(cost_entry.input_cost)
            entry_dict["output_cost"] = float(cost_entry.output_cost)
            entry_dict["total_cost"] = float(cost_entry.total_cost)

            await container.create_item(entry_dict)

        except Exception as e:
            self.logger.error(f"Error storing cost entry: {str(e)}")
            raise

    async def get_cost_summary(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        provider: Optional[str] = None,
    ) -> CostSummary:
        """
        Get cost summary for specified period and filters.

        Args:
            user_id: Filter by user (optional)
            start_date: Start of period (default: 30 days ago)
            end_date: End of period (default: now)
            provider: Filter by provider (optional)

        Returns:
            CostSummary: Aggregated cost data
        """
        try:
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)

            # Build query
            query_parts = ["SELECT * FROM c WHERE c.timestamp >= @start AND c.timestamp <= @end"]
            parameters = [{"name": "@start", "value": start_date.isoformat()}, {"name": "@end", "value": end_date.isoformat()}]

            if user_id:
                query_parts.append("AND c.user_id = @user_id")
                parameters.append({"name": "@user_id", "value": user_id})

            if provider:
                query_parts.append("AND c.provider = @provider")
                parameters.append({"name": "@provider", "value": provider})

            query = " ".join(query_parts)

            # Execute query
            container = self.cosmos_client.get_database_client(self.database_name).get_container_client(
                self.cost_entries_container
            )

            entries = []
            async for item in container.query_items(query=query, parameters=parameters):
                entries.append(item)

            # Calculate summary
            return self._calculate_summary(entries, start_date, end_date)

        except Exception as e:
            self.logger.error(f"Error getting cost summary: {str(e)}")
            raise

    def _calculate_summary(self, entries: List[Dict], start_date: datetime, end_date: datetime) -> CostSummary:
        """Calculate cost summary from entries."""
        if not entries:
            return CostSummary(
                total_requests=0,
                total_tokens=0,
                total_cost=Decimal("0"),
                cost_by_provider={},
                cost_by_model={},
                average_cost_per_request=Decimal("0"),
                average_tokens_per_request=0.0,
                period_start=start_date,
                period_end=end_date,
            )

        total_requests = len(entries)
        total_tokens = sum(entry["total_tokens"] for entry in entries)
        total_cost = sum(Decimal(str(entry["total_cost"])) for entry in entries)

        # Group by provider
        cost_by_provider = {}
        for entry in entries:
            provider = entry["provider"]
            cost_by_provider[provider] = cost_by_provider.get(provider, Decimal("0")) + Decimal(str(entry["total_cost"]))

        # Group by model
        cost_by_model = {}
        for entry in entries:
            model = f"{entry['provider']}/{entry['model']}"
            cost_by_model[model] = cost_by_model.get(model, Decimal("0")) + Decimal(str(entry["total_cost"]))

        # Calculate averages
        avg_cost = total_cost / total_requests if total_requests > 0 else Decimal("0")
        avg_tokens = total_tokens / total_requests if total_requests > 0 else 0.0

        return CostSummary(
            total_requests=total_requests,
            total_tokens=total_tokens,
            total_cost=total_cost,
            cost_by_provider=cost_by_provider,
            cost_by_model=cost_by_model,
            average_cost_per_request=avg_cost,
            average_tokens_per_request=avg_tokens,
            period_start=start_date,
            period_end=end_date,
        )

    async def _check_budget_alerts(self, user_id: str, new_cost: Decimal) -> None:
        """Check if cost thresholds are exceeded and create alerts."""
        try:
            # Get current month's spending
            start_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            summary = await self.get_cost_summary(user_id=user_id, start_date=start_of_month)

            current_spending = summary.total_cost

            # Check each threshold
            for level, threshold in self.default_thresholds.items():
                if current_spending >= threshold:
                    # Check if alert already exists for this period
                    if not await self._alert_exists(user_id, level, start_of_month):
                        await self._create_alert(user_id, level, threshold, current_spending)

        except Exception as e:
            self.logger.error(f"Error checking budget alerts: {str(e)}")

    async def _alert_exists(self, user_id: str, level: CostAlertLevel, start_date: datetime) -> bool:
        """Check if alert already exists for user/level/period."""
        try:
            container = self.cosmos_client.get_database_client(self.database_name).get_container_client(
                self.cost_alerts_container
            )

            query = """
                SELECT * FROM c
                WHERE c.user_id = @user_id
                AND c.level = @level
                AND c.timestamp >= @start_date
            """
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@level", "value": level.value},
                {"name": "@start_date", "value": start_date.isoformat()},
            ]

            async for _ in container.query_items(query=query, parameters=parameters):
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking alert existence: {str(e)}")
            return True  # Assume exists to avoid spam

    async def _create_alert(self, user_id: str, level: CostAlertLevel, threshold: Decimal, current_amount: Decimal) -> None:
        """Create a new cost alert."""
        try:
            alert = CostAlert(
                id=f"alert_{user_id}_{level.value}_{datetime.now(timezone.utc).timestamp()}",
                level=level,
                message=f"Cost threshold exceeded: ${float(current_amount):.2f} >= ${float(threshold):.2f}",
                threshold_amount=threshold,
                current_amount=current_amount,
                user_id=user_id,
                timestamp=datetime.now(timezone.utc),
            )

            container = self.cosmos_client.get_database_client(self.database_name).get_container_client(
                self.cost_alerts_container
            )

            alert_dict = asdict(alert)
            alert_dict["timestamp"] = alert.timestamp.isoformat()
            alert_dict["level"] = alert.level.value
            alert_dict["threshold_amount"] = float(alert.threshold_amount)
            alert_dict["current_amount"] = float(alert.current_amount)

            await container.create_item(alert_dict)

            self.logger.warning(f"Created cost alert: {alert.message}")

        except Exception as e:
            self.logger.error(f"Error creating alert: {str(e)}")

    async def get_recent_alerts(self, user_id: Optional[str] = None, limit: int = 50) -> List[CostAlert]:
        """Get recent cost alerts."""
        try:
            container = self.cosmos_client.get_database_client(self.database_name).get_container_client(
                self.cost_alerts_container
            )

            query = "SELECT TOP @limit * FROM c"
            parameters = [{"name": "@limit", "value": limit}]

            if user_id:
                query += " WHERE c.user_id = @user_id"
                parameters.append({"name": "@user_id", "value": user_id})

            query += " ORDER BY c.timestamp DESC"

            alerts = []
            async for item in container.query_items(query=query, parameters=parameters):
                alert = CostAlert(
                    id=item["id"],
                    level=CostAlertLevel(item["level"]),
                    message=item["message"],
                    threshold_amount=Decimal(str(item["threshold_amount"])),
                    current_amount=Decimal(str(item["current_amount"])),
                    user_id=item.get("user_id"),
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                    acknowledged=item.get("acknowledged", False),
                )
                alerts.append(alert)

            return alerts

        except Exception as e:
            self.logger.error(f"Error getting recent alerts: {str(e)}")
            return []

    async def update_pricing_model(self, provider: str, model: str, input_price: Decimal, output_price: Decimal) -> None:
        """Update pricing for a specific model."""
        try:
            if provider not in self.pricing_models:
                self.pricing_models[provider] = {}

            self.pricing_models[provider][model] = {"input": input_price, "output": output_price}

            self.logger.info(f"Updated pricing for {provider}/{model}")

        except Exception as e:
            self.logger.error(f"Error updating pricing model: {str(e)}")
            raise

    async def get_cost_analytics(self, user_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive cost analytics.

        Returns:
            Dict containing usage trends, cost breakdowns, and optimization insights
        """
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)

            # Get overall summary
            summary = await self.get_cost_summary(user_id, start_date, end_date)

            # Get daily breakdown
            daily_costs = await self._get_daily_costs(user_id, start_date, end_date)

            # Get model efficiency metrics
            efficiency_metrics = await self._get_efficiency_metrics(user_id, start_date, end_date)

            return {
                "summary": {
                    "total_cost": float(summary.total_cost),
                    "total_requests": summary.total_requests,
                    "total_tokens": summary.total_tokens,
                    "average_cost_per_request": float(summary.average_cost_per_request),
                    "cost_by_provider": {k: float(v) for k, v in summary.cost_by_provider.items()},
                    "cost_by_model": {k: float(v) for k, v in summary.cost_by_model.items()},
                },
                "daily_breakdown": daily_costs,
                "efficiency_metrics": efficiency_metrics,
                "period": {"start": start_date.isoformat(), "end": end_date.isoformat(), "days": days},
            }

        except Exception as e:
            self.logger.error(f"Error getting cost analytics: {str(e)}")
            return {}

    async def _get_daily_costs(self, user_id: Optional[str], start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get daily cost breakdown."""
        try:
            # This would be more efficient with aggregation queries in production
            daily_costs = []
            current_date = start_date.date()

            while current_date <= end_date.date():
                day_start = datetime.combine(current_date, datetime.min.time())
                day_end = datetime.combine(current_date, datetime.max.time())

                summary = await self.get_cost_summary(user_id, day_start, day_end)

                daily_costs.append(
                    {
                        "date": current_date.isoformat(),
                        "cost": float(summary.total_cost),
                        "requests": summary.total_requests,
                        "tokens": summary.total_tokens,
                    }
                )

                current_date += timedelta(days=1)

            return daily_costs

        except Exception as e:
            self.logger.error(f"Error getting daily costs: {str(e)}")
            return []

    async def _get_efficiency_metrics(
        self, user_id: Optional[str], start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get model efficiency metrics."""
        try:
            summary = await self.get_cost_summary(user_id, start_date, end_date)

            if not summary.cost_by_model:
                return {}

            # Calculate cost per token for each model
            efficiency = {}
            for model, cost in summary.cost_by_model.items():
                # This is simplified - would need to track tokens per model separately
                efficiency[model] = {
                    "total_cost": float(cost),
                    "cost_percentage": float((cost / summary.total_cost) * 100) if summary.total_cost > 0 else 0,
                }

            # Find most/least efficient models
            sorted_models = sorted(efficiency.items(), key=lambda x: x[1]["total_cost"])
            most_expensive = sorted_models[-1] if sorted_models else None
            least_expensive = sorted_models[0] if sorted_models else None

            return {
                "model_breakdown": efficiency,
                "most_expensive_model": most_expensive[0] if most_expensive else None,
                "least_expensive_model": least_expensive[0] if least_expensive else None,
                "recommendations": self._generate_cost_recommendations(efficiency),
            }

        except Exception as e:
            self.logger.error(f"Error getting efficiency metrics: {str(e)}")
            return {}

    def _generate_cost_recommendations(self, efficiency: Dict[str, Any]) -> List[str]:
        """Generate cost optimization recommendations."""
        recommendations = []

        if not efficiency:
            return recommendations

        # Find high-cost models
        total_spending = sum(model["total_cost"] for model in efficiency.values())

        for model, metrics in efficiency.items():
            if metrics["cost_percentage"] > 50:
                recommendations.append(
                    f"Consider optimizing usage of {model} - accounts for " f"{metrics['cost_percentage']:.1f}% of total costs"
                )

        # General recommendations
        if total_spending > 100:
            recommendations.append("Consider implementing more aggressive caching to reduce API calls")

        if len(efficiency) > 3:
            recommendations.append("Consolidate to fewer models to benefit from volume pricing")

        return recommendations
