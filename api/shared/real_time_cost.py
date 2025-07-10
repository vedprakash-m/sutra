"""
Real-Time Cost Management System
Integrates with actual LLM provider APIs for live cost tracking
Part of systematic resolution for cost management architecture gap
"""

import asyncio
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from .error_handling import SutraAPIError
from .models import LLMProvider, User
from .unified_auth import get_auth_provider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CostTrackingStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BUDGET_EXCEEDED = "budget_exceeded"
    RATE_LIMITED = "rate_limited"


@dataclass
class RealTimeCostRecord:
    """Real-time cost record"""

    id: str
    user_id: str
    provider: str
    model: str
    request_id: str
    timestamp: datetime
    cost: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    request_duration: float
    request_type: str
    status: str
    prompt_id: Optional[str] = None
    playbook_id: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LiveUsageMetrics:
    """Live usage metrics"""

    user_id: str
    period: str  # "hour", "day", "month"
    total_cost: float
    total_requests: int
    total_tokens: int
    by_provider: Dict[str, Dict[str, Any]]
    last_updated: datetime
    status: CostTrackingStatus


@dataclass
class BudgetAlert:
    """Budget alert definition"""

    user_id: str
    alert_type: str  # "warning", "limit", "exceeded"
    threshold: float  # percentage of budget
    current_usage: float
    budget_limit: float
    triggered_at: datetime
    message: str


class ProviderCostCalculator:
    """Calculate costs for different LLM providers"""

    # Current pricing per 1K tokens (as of 2024)
    PRICING = {
        "openai": {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        },
        "anthropic": {
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        },
        "google": {
            "gemini-pro": {"input": 0.0005, "output": 0.0015},
            "gemini-ultra": {"input": 0.001, "output": 0.003},
        },
    }

    @classmethod
    def calculate_cost(cls, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage"""
        try:
            pricing = cls.PRICING.get(provider.lower(), {}).get(model.lower(), {})
            if not pricing:
                logger.warning(f"No pricing found for {provider}/{model}, using default")
                return 0.01  # Default fallback cost

            input_cost = (input_tokens / 1000) * pricing["input"]
            output_cost = (output_tokens / 1000) * pricing["output"]
            total_cost = input_cost + output_cost

            return round(total_cost, 6)  # Round to 6 decimal places
        except Exception as e:
            logger.error(f"Cost calculation error: {str(e)}")
            return 0.01  # Fallback cost


class ProviderAPIClient:
    """Client for integrating with LLM provider APIs for usage data"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_openai_usage(self, api_key: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get usage data from OpenAI API"""
        if not self.session:
            raise ValueError("Session not initialized")

        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            url = "https://api.openai.com/v1/usage"
            params = {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            }

            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    logger.error(f"OpenAI API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching OpenAI usage: {str(e)}")
            return []

    async def get_anthropic_usage(self, api_key: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get usage data from Anthropic API"""
        # Note: Anthropic doesn't have a public usage API yet
        # This would be implemented when available
        logger.info("Anthropic usage API not yet available")
        return []

    async def get_google_usage(self, api_key: str, project_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get usage data from Google Cloud Billing API"""
        # This would integrate with Google Cloud Billing API
        logger.info("Google Cloud billing integration not yet implemented")
        return []


class RealTimeCostManager:
    """
    Real-time cost management system
    Tracks actual costs and enforces budgets in real-time
    """

    def __init__(self):
        self.calculator = ProviderCostCalculator()
        self.cost_records: List[RealTimeCostRecord] = []
        self.usage_cache: Dict[str, LiveUsageMetrics] = {}
        self.budget_alerts: List[BudgetAlert] = []

        # Configuration
        self.cache_ttl = timedelta(minutes=5)  # Cache usage metrics for 5 minutes
        self.alert_cooldown = timedelta(minutes=30)  # Don't spam alerts
        self.max_daily_requests = 1000  # Default daily limit

    async def track_request_cost(
        self,
        user_id: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        request_duration: float,
        request_type: str = "api_call",
        prompt_id: Optional[str] = None,
        playbook_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RealTimeCostRecord:
        """Track cost for a single request"""

        # Calculate cost
        cost = self.calculator.calculate_cost(provider, model, input_tokens, output_tokens)
        total_tokens = input_tokens + output_tokens

        # Create cost record
        record = RealTimeCostRecord(
            id=f"cost_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id[:8]}",
            user_id=user_id,
            provider=provider,
            model=model,
            request_id=f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(timezone.utc),
            cost=cost,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            request_duration=request_duration,
            request_type=request_type,
            status="success",
            prompt_id=prompt_id,
            playbook_id=playbook_id,
            metadata=metadata,
        )

        # Store record
        self.cost_records.append(record)

        # Update live metrics
        await self._update_live_metrics(user_id, record)

        # Check budget limits
        await self._check_budget_limits(user_id)

        logger.info(f"Tracked cost: ${cost:.6f} for user {user_id} ({provider}/{model})")
        return record

    async def get_live_usage(self, user_id: str, period: str = "month") -> LiveUsageMetrics:
        """Get live usage metrics for a user"""
        cache_key = f"{user_id}_{period}"

        # Check cache
        if cache_key in self.usage_cache:
            cached = self.usage_cache[cache_key]
            if datetime.now(timezone.utc) - cached.last_updated < self.cache_ttl:
                return cached

        # Calculate fresh metrics
        metrics = await self._calculate_usage_metrics(user_id, period)

        # Cache results
        self.usage_cache[cache_key] = metrics

        return metrics

    async def _calculate_usage_metrics(self, user_id: str, period: str) -> LiveUsageMetrics:
        """Calculate usage metrics for a specific period"""
        now = datetime.now(timezone.utc)

        # Determine time range
        if period == "hour":
            start_time = now - timedelta(hours=1)
        elif period == "day":
            start_time = now - timedelta(days=1)
        elif period == "month":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(days=1)

        # Filter records for user and time period
        relevant_records = [
            record for record in self.cost_records if record.user_id == user_id and record.timestamp >= start_time
        ]

        # Calculate totals
        total_cost = sum(record.cost for record in relevant_records)
        total_requests = len(relevant_records)
        total_tokens = sum(record.total_tokens for record in relevant_records)

        # Calculate by provider
        by_provider = {}
        for record in relevant_records:
            if record.provider not in by_provider:
                by_provider[record.provider] = {
                    "cost": 0,
                    "requests": 0,
                    "tokens": 0,
                    "models": {},
                }

            by_provider[record.provider]["cost"] += record.cost
            by_provider[record.provider]["requests"] += 1
            by_provider[record.provider]["tokens"] += record.total_tokens

            # Track model usage
            model_key = record.model
            if model_key not in by_provider[record.provider]["models"]:
                by_provider[record.provider]["models"][model_key] = {
                    "cost": 0,
                    "requests": 0,
                    "tokens": 0,
                }
            by_provider[record.provider]["models"][model_key]["cost"] += record.cost
            by_provider[record.provider]["models"][model_key]["requests"] += 1
            by_provider[record.provider]["models"][model_key]["tokens"] += record.total_tokens

        # Determine status
        status = CostTrackingStatus.ACTIVE
        if total_requests > self.max_daily_requests and period == "day":
            status = CostTrackingStatus.RATE_LIMITED

        return LiveUsageMetrics(
            user_id=user_id,
            period=period,
            total_cost=total_cost,
            total_requests=total_requests,
            total_tokens=total_tokens,
            by_provider=by_provider,
            last_updated=now,
            status=status,
        )

    async def _update_live_metrics(self, user_id: str, record: RealTimeCostRecord):
        """Update cached live metrics with new record"""
        for period in ["hour", "day", "month"]:
            cache_key = f"{user_id}_{period}"
            if cache_key in self.usage_cache:
                metrics = self.usage_cache[cache_key]

                # Update totals
                metrics.total_cost += record.cost
                metrics.total_requests += 1
                metrics.total_tokens += record.total_tokens
                metrics.last_updated = datetime.now(timezone.utc)

                # Update provider breakdown
                if record.provider not in metrics.by_provider:
                    metrics.by_provider[record.provider] = {
                        "cost": 0,
                        "requests": 0,
                        "tokens": 0,
                        "models": {},
                    }

                metrics.by_provider[record.provider]["cost"] += record.cost
                metrics.by_provider[record.provider]["requests"] += 1
                metrics.by_provider[record.provider]["tokens"] += record.total_tokens

    async def _check_budget_limits(self, user_id: str):
        """Check if user has exceeded budget limits"""
        # This would integrate with budget configuration
        # For now, implement basic warnings

        daily_metrics = await self.get_live_usage(user_id, "day")
        monthly_metrics = await self.get_live_usage(user_id, "month")

        # Example budget limits (would come from configuration)
        daily_budget = 10.0  # $10/day
        monthly_budget = 200.0  # $200/month

        # Check daily budget
        if daily_metrics.total_cost > daily_budget * 0.8:  # 80% warning
            await self._create_budget_alert(
                user_id,
                "warning" if daily_metrics.total_cost < daily_budget else "exceeded",
                daily_metrics.total_cost,
                daily_budget,
                "daily",
            )

        # Check monthly budget
        if monthly_metrics.total_cost > monthly_budget * 0.8:  # 80% warning
            await self._create_budget_alert(
                user_id,
                "warning" if monthly_metrics.total_cost < monthly_budget else "exceeded",
                monthly_metrics.total_cost,
                monthly_budget,
                "monthly",
            )

    async def _create_budget_alert(
        self,
        user_id: str,
        alert_type: str,
        current_usage: float,
        budget_limit: float,
        period: str,
    ):
        """Create budget alert"""

        # Check if we recently sent this alert (avoid spam)
        recent_alerts = [
            alert
            for alert in self.budget_alerts
            if (
                alert.user_id == user_id
                and alert.alert_type == alert_type
                and datetime.now(timezone.utc) - alert.triggered_at < self.alert_cooldown
            )
        ]

        if recent_alerts:
            return  # Don't spam alerts

        percentage = (current_usage / budget_limit) * 100

        message = f"Budget {alert_type}: {percentage:.1f}% of {period} budget used (${current_usage:.2f}/${budget_limit:.2f})"

        alert = BudgetAlert(
            user_id=user_id,
            alert_type=alert_type,
            threshold=percentage,
            current_usage=current_usage,
            budget_limit=budget_limit,
            triggered_at=datetime.now(timezone.utc),
            message=message,
        )

        self.budget_alerts.append(alert)
        logger.warning(f"Budget alert for {user_id}: {message}")

    async def get_cost_summary(self, user_id: str, period: str = "month") -> Dict[str, Any]:
        """Get cost summary for API responses"""
        metrics = await self.get_live_usage(user_id, period)

        # Calculate trends and predictions
        summary = {
            "period": period,
            "total_cost": round(metrics.total_cost, 4),
            "total_requests": metrics.total_requests,
            "total_tokens": metrics.total_tokens,
            "average_cost_per_request": round(metrics.total_cost / max(metrics.total_requests, 1), 6),
            "by_provider": {
                provider: {
                    "cost": round(data["cost"], 4),
                    "requests": data["requests"],
                    "tokens": data["tokens"],
                    "models": {
                        model: {
                            "cost": round(model_data["cost"], 4),
                            "requests": model_data["requests"],
                            "tokens": model_data["tokens"],
                        }
                        for model, model_data in data.get("models", {}).items()
                    },
                }
                for provider, data in metrics.by_provider.items()
            },
            "status": metrics.status.value,
            "last_updated": metrics.last_updated.isoformat(),
        }

        return summary

    async def estimate_request_cost(
        self,
        provider: str,
        model: str,
        estimated_input_tokens: int,
        estimated_output_tokens: int,
    ) -> Dict[str, Any]:
        """Estimate cost for a potential request"""
        estimated_cost = self.calculator.calculate_cost(provider, model, estimated_input_tokens, estimated_output_tokens)

        return {
            "provider": provider,
            "model": model,
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "estimated_total_tokens": estimated_input_tokens + estimated_output_tokens,
            "estimated_cost": round(estimated_cost, 6),
            "pricing_per_1k_tokens": self.calculator.PRICING.get(provider, {}).get(model, {}),
        }

    async def get_recent_alerts(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent budget alerts for a user"""
        user_alerts = [alert for alert in self.budget_alerts if alert.user_id == user_id]

        # Sort by most recent first
        user_alerts.sort(key=lambda x: x.triggered_at, reverse=True)

        return [
            {
                "alert_type": alert.alert_type,
                "threshold": alert.threshold,
                "current_usage": alert.current_usage,
                "budget_limit": alert.budget_limit,
                "triggered_at": alert.triggered_at.isoformat(),
                "message": alert.message,
            }
            for alert in user_alerts[:limit]
        ]


# Singleton instance
_real_time_cost_manager: Optional[RealTimeCostManager] = None


def get_real_time_cost_manager() -> RealTimeCostManager:
    """Get singleton real-time cost manager"""
    global _real_time_cost_manager
    if _real_time_cost_manager is None:
        _real_time_cost_manager = RealTimeCostManager()
    return _real_time_cost_manager


# Alias for convenience
def get_cost_manager() -> RealTimeCostManager:
    """Alias for get_real_time_cost_manager"""
    return get_real_time_cost_manager()


# Export public interface
__all__ = [
    "RealTimeCostManager",
    "RealTimeCostRecord",
    "LiveUsageMetrics",
    "BudgetAlert",
    "CostTrackingStatus",
    "ProviderCostCalculator",
    "get_real_time_cost_manager",
    "get_cost_manager",
]
