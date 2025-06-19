import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from .models import UsageRecord, LLMProvider
from .database import get_database_manager


class BudgetManager:
    """Manages budget tracking and enforcement for LLM usage."""

    def __init__(self):
        self.db_manager = get_database_manager()

    async def track_usage(
        self,
        user_id: str,
        provider: LLMProvider,
        operation: str,
        cost: float,
        tokens_used: int,
        execution_time_ms: int,
        metadata: Dict[str, Any] = None,
    ) -> UsageRecord:
        """Track usage for budget monitoring."""
        try:
            # Create usage record
            now = datetime.now(timezone.utc)
            usage_record = UsageRecord(
                id=f"{user_id}_{provider}_{now.isoformat()}",
                user_id=user_id,
                provider=provider,
                operation=operation,
                cost=cost,
                tokens_used=tokens_used,
                execution_time_ms=execution_time_ms,
                date=now.strftime("%Y-%m-%d"),
                timestamp=now,
                metadata=metadata or {},
            )

            # Store in database
            await self.db_manager.create_item(
                container_name="usage",
                item=usage_record.dict(),
                partition_key=usage_record.date,
            )

            return usage_record

        except Exception as e:
            logging.error(f"Failed to track usage: {e}")
            raise

    async def get_user_usage(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get usage statistics for a user over the specified number of days."""
        try:
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = (
                end_date.replace(day=1)
                if days >= 30
                else end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            )

            # Query usage records
            query = """
                SELECT * FROM c
                WHERE c.user_id = @user_id
                AND c.timestamp >= @start_date
                AND c.timestamp <= @end_date
            """

            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@start_date", "value": start_date.isoformat()},
                {"name": "@end_date", "value": end_date.isoformat()},
            ]

            usage_records = await self.db_manager.query_items(
                container_name="usage", query=query, parameters=parameters
            )

            # Aggregate statistics
            total_cost = sum(record.get("cost", 0) for record in usage_records)
            total_tokens = sum(record.get("tokens_used", 0) for record in usage_records)
            total_requests = len(usage_records)

            # Group by provider
            provider_stats = {}
            for record in usage_records:
                provider = record.get("provider")
                if provider not in provider_stats:
                    provider_stats[provider] = {"cost": 0, "tokens": 0, "requests": 0}

                provider_stats[provider]["cost"] += record.get("cost", 0)
                provider_stats[provider]["tokens"] += record.get("tokens_used", 0)
                provider_stats[provider]["requests"] += 1

            # Group by operation
            operation_stats = {}
            for record in usage_records:
                operation = record.get("operation")
                if operation not in operation_stats:
                    operation_stats[operation] = {"cost": 0, "tokens": 0, "requests": 0}

                operation_stats[operation]["cost"] += record.get("cost", 0)
                operation_stats[operation]["tokens"] += record.get("tokens_used", 0)
                operation_stats[operation]["requests"] += 1

            return {
                "user_id": user_id,
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "total_requests": total_requests,
                "provider_breakdown": provider_stats,
                "operation_breakdown": operation_stats,
                "daily_usage": await self._get_daily_usage(usage_records),
            }

        except Exception as e:
            logging.error(f"Failed to get user usage: {e}")
            raise

    async def get_system_usage(self, days: int = 30) -> Dict[str, Any]:
        """Get system-wide usage statistics."""
        try:
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = (
                end_date.replace(day=1)
                if days >= 30
                else end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            )

            # Query all usage records
            query = """
                SELECT * FROM c
                WHERE c.timestamp >= @start_date
                AND c.timestamp <= @end_date
            """

            parameters = [
                {"name": "@start_date", "value": start_date.isoformat()},
                {"name": "@end_date", "value": end_date.isoformat()},
            ]

            usage_records = await self.db_manager.query_items(
                container_name="usage", query=query, parameters=parameters
            )

            # Aggregate statistics
            total_cost = sum(record.get("cost", 0) for record in usage_records)
            total_tokens = sum(record.get("tokens_used", 0) for record in usage_records)
            total_requests = len(usage_records)
            unique_users = len(set(record.get("user_id") for record in usage_records))

            # Group by provider
            provider_stats = {}
            for record in usage_records:
                provider = record.get("provider")
                if provider not in provider_stats:
                    provider_stats[provider] = {
                        "cost": 0,
                        "tokens": 0,
                        "requests": 0,
                        "unique_users": set(),
                    }

                provider_stats[provider]["cost"] += record.get("cost", 0)
                provider_stats[provider]["tokens"] += record.get("tokens_used", 0)
                provider_stats[provider]["requests"] += 1
                provider_stats[provider]["unique_users"].add(record.get("user_id"))

            # Convert sets to counts
            for provider in provider_stats:
                provider_stats[provider]["unique_users"] = len(
                    provider_stats[provider]["unique_users"]
                )

            # Get top users by cost
            user_costs = {}
            for record in usage_records:
                user_id = record.get("user_id")
                user_costs[user_id] = user_costs.get(user_id, 0) + record.get("cost", 0)

            top_users = sorted(user_costs.items(), key=lambda x: x[1], reverse=True)[
                :10
            ]

            return {
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "total_requests": total_requests,
                "unique_users": unique_users,
                "provider_breakdown": provider_stats,
                "top_users": [
                    {"user_id": user_id, "cost": cost} for user_id, cost in top_users
                ],
                "daily_usage": await self._get_daily_usage(usage_records),
            }

        except Exception as e:
            logging.error(f"Failed to get system usage: {e}")
            raise

    async def check_user_budget(
        self, user_id: str, additional_cost: float = 0
    ) -> Dict[str, Any]:
        """Check if user is within budget limits."""
        try:
            # Get user's current monthly usage
            usage_stats = await self.get_user_usage(user_id, days=30)
            current_cost = usage_stats["total_cost"]

            # Get user budget limit from system config (this would be configurable)
            user_budget_limit = 100.0  # Default $100 per month per user

            # Calculate remaining budget
            remaining_budget = user_budget_limit - current_cost
            projected_cost = current_cost + additional_cost

            return {
                "user_id": user_id,
                "current_cost": current_cost,
                "budget_limit": user_budget_limit,
                "remaining_budget": remaining_budget,
                "additional_cost": additional_cost,
                "projected_cost": projected_cost,
                "within_budget": projected_cost <= user_budget_limit,
                "utilization_percent": (projected_cost / user_budget_limit) * 100,
            }

        except Exception as e:
            logging.error(f"Failed to check user budget: {e}")
            raise

    async def check_provider_budget(
        self, provider: LLMProvider, additional_cost: float = 0
    ) -> Dict[str, Any]:
        """Check if provider is within budget limits."""
        try:
            # Get provider's current monthly usage
            end_date = datetime.now(timezone.utc)
            start_date = end_date.replace(day=1)

            query = """
                SELECT * FROM c
                WHERE c.provider = @provider
                AND c.timestamp >= @start_date
                AND c.timestamp <= @end_date
            """

            parameters = [
                {"name": "@provider", "value": provider},
                {"name": "@start_date", "value": start_date.isoformat()},
                {"name": "@end_date", "value": end_date.isoformat()},
            ]

            usage_records = await self.db_manager.query_items(
                container_name="usage", query=query, parameters=parameters
            )

            current_cost = sum(record.get("cost", 0) for record in usage_records)

            # Get provider budget limit from system config
            provider_budget_limits = {
                LLMProvider.OPENAI: 500.0,  # $500/month
                LLMProvider.ANTHROPIC: 300.0,  # $300/month
                LLMProvider.GOOGLE: 200.0,  # $200/month
            }

            budget_limit = provider_budget_limits.get(provider, 100.0)
            remaining_budget = budget_limit - current_cost
            projected_cost = current_cost + additional_cost

            return {
                "provider": provider,
                "current_cost": current_cost,
                "budget_limit": budget_limit,
                "remaining_budget": remaining_budget,
                "additional_cost": additional_cost,
                "projected_cost": projected_cost,
                "within_budget": projected_cost <= budget_limit,
                "utilization_percent": (projected_cost / budget_limit) * 100,
            }

        except Exception as e:
            logging.error(f"Failed to check provider budget: {e}")
            raise

    async def get_budget_alerts(self) -> List[Dict[str, Any]]:
        """Get budget alerts for users and providers exceeding thresholds."""
        alerts = []

        try:
            # Check system-wide usage
            system_stats = await self.get_system_usage(days=30)

            # Check each provider budget
            for provider in LLMProvider:
                provider_budget = await self.check_provider_budget(provider)

                if provider_budget["utilization_percent"] > 90:
                    alerts.append(
                        {
                            "type": "provider_budget_critical",
                            "provider": provider,
                            "utilization_percent": provider_budget[
                                "utilization_percent"
                            ],
                            "remaining_budget": provider_budget["remaining_budget"],
                            "message": f"Provider {provider} budget is {provider_budget['utilization_percent']:.1f}% utilized",
                        }
                    )
                elif provider_budget["utilization_percent"] > 75:
                    alerts.append(
                        {
                            "type": "provider_budget_warning",
                            "provider": provider,
                            "utilization_percent": provider_budget[
                                "utilization_percent"
                            ],
                            "remaining_budget": provider_budget["remaining_budget"],
                            "message": f"Provider {provider} budget is {provider_budget['utilization_percent']:.1f}% utilized",
                        }
                    )

            # Check top users for budget issues
            top_users = system_stats.get("top_users", [])[:5]  # Check top 5 users

            for user_data in top_users:
                user_budget = await self.check_user_budget(user_data["user_id"])

                if user_budget["utilization_percent"] > 90:
                    alerts.append(
                        {
                            "type": "user_budget_critical",
                            "user_id": user_data["user_id"],
                            "utilization_percent": user_budget["utilization_percent"],
                            "remaining_budget": user_budget["remaining_budget"],
                            "message": f"User {user_data['user_id']} budget is {user_budget['utilization_percent']:.1f}% utilized",
                        }
                    )

            return alerts

        except Exception as e:
            logging.error(f"Failed to get budget alerts: {e}")
            return []

    async def _get_daily_usage(
        self, usage_records: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """Helper to aggregate usage by day."""
        daily_usage = {}

        for record in usage_records:
            date = record.get("date", record.get("timestamp", "")[:10])

            if date not in daily_usage:
                daily_usage[date] = {"cost": 0, "tokens": 0, "requests": 0}

            daily_usage[date]["cost"] += record.get("cost", 0)
            daily_usage[date]["tokens"] += record.get("tokens_used", 0)
            daily_usage[date]["requests"] += 1

        return daily_usage


# Global budget manager instance
_budget_manager = None


def get_budget_manager() -> BudgetManager:
    """Get the global budget manager instance."""
    global _budget_manager
    if _budget_manager is None:
        _budget_manager = BudgetManager()
    return _budget_manager
