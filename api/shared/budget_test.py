"""
Tests for budget.py module - Budget tracking and limits
"""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from api.shared.budget import BudgetManager, get_budget_manager
from api.shared.models import LLMProvider, UsageRecord


class TestBudgetManager:
    """Test suite for BudgetManager class."""

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_init(self):
        """Test BudgetManager initialization."""
        budget_manager = BudgetManager()
        assert budget_manager.db_manager is not None

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_track_usage_success(self, mock_get_db_manager):
        """Test successful usage tracking."""
        mock_db_manager = Mock()
        mock_db_manager.create_item = AsyncMock()
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()

        result = await budget_manager.track_usage(
            user_id="user-123",
            provider=LLMProvider.OPENAI,
            operation="completion",
            cost=0.05,
            tokens_used=100,
            execution_time_ms=500,
            metadata={"model": "gpt-3.5-turbo"},
        )

        assert isinstance(result, UsageRecord)
        assert result.user_id == "user-123"
        assert result.provider == LLMProvider.OPENAI
        assert result.cost == 0.05
        assert result.tokens_used == 100
        assert result.execution_time_ms == 500

        mock_db_manager.create_item.assert_called_once()

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_track_usage_with_metadata(self, mock_get_db_manager):
        """Test usage tracking with metadata."""
        mock_db_manager = Mock()
        mock_db_manager.create_item = AsyncMock()
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()
        metadata = {"model": "gpt-4", "temperature": 0.7}

        result = await budget_manager.track_usage(
            user_id="user-123",
            provider=LLMProvider.OPENAI,
            operation="completion",
            cost=0.10,
            tokens_used=50,
            execution_time_ms=800,
            metadata=metadata,
        )

        assert result.metadata == metadata

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_track_usage_error(self, mock_get_db_manager):
        """Test usage tracking error handling."""
        mock_db_manager = Mock()
        mock_db_manager.create_item = AsyncMock(side_effect=Exception("Database error"))
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()

        with pytest.raises(Exception, match="Database error"):
            await budget_manager.track_usage(
                user_id="user-123",
                provider=LLMProvider.OPENAI,
                operation="completion",
                cost=0.05,
                tokens_used=100,
                execution_time_ms=500,
            )

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_get_user_usage_success(self, mock_get_db_manager):
        """Test successful user usage retrieval."""
        mock_db_manager = Mock()
        mock_usage_records = [
            {
                "user_id": "user-123",
                "provider": "openai",
                "operation": "completion",
                "cost": 0.05,
                "tokens_used": 100,
                "timestamp": "2024-01-15T10:00:00Z",
                "date": "2024-01-15",
            },
            {
                "user_id": "user-123",
                "provider": "anthropic",
                "operation": "completion",
                "cost": 0.03,
                "tokens_used": 75,
                "timestamp": "2024-01-15T11:00:00Z",
                "date": "2024-01-15",
            },
        ]
        mock_db_manager.query_items = AsyncMock(return_value=mock_usage_records)
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()
        budget_manager._get_daily_usage = AsyncMock(return_value={"2024-01-15": {"cost": 0.08, "tokens": 175, "requests": 2}})

        result = await budget_manager.get_user_usage("user-123", days=30)

        assert result["user_id"] == "user-123"
        assert result["total_cost"] == 0.08
        assert result["total_tokens"] == 175
        assert result["total_requests"] == 2
        assert "openai" in result["provider_breakdown"]
        assert "anthropic" in result["provider_breakdown"]
        assert result["provider_breakdown"]["openai"]["cost"] == 0.05
        assert result["provider_breakdown"]["anthropic"]["cost"] == 0.03

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_get_system_usage_success(self, mock_get_db_manager):
        """Test successful system usage retrieval."""
        mock_db_manager = Mock()
        mock_usage_records = [
            {
                "user_id": "user-123",
                "provider": "openai",
                "operation": "completion",
                "cost": 0.05,
                "tokens_used": 100,
                "timestamp": "2024-01-15T10:00:00Z",
            },
            {
                "user_id": "user-456",
                "provider": "openai",
                "operation": "completion",
                "cost": 0.03,
                "tokens_used": 75,
                "timestamp": "2024-01-15T11:00:00Z",
            },
        ]
        mock_db_manager.query_items = AsyncMock(return_value=mock_usage_records)
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()
        budget_manager._get_daily_usage = AsyncMock(return_value={"2024-01-15": {"cost": 0.08, "tokens": 175, "requests": 2}})

        result = await budget_manager.get_system_usage(days=30)

        assert result["total_cost"] == 0.08
        assert result["total_tokens"] == 175
        assert result["total_requests"] == 2
        assert result["unique_users"] == 2
        assert "openai" in result["provider_breakdown"]
        assert len(result["top_users"]) == 2

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_check_user_budget_within_limit(self, mock_get_db_manager):
        """Test user budget check within limit."""
        mock_db_manager = Mock()
        mock_db_manager.query_items = AsyncMock(return_value=[])  # No budget config found
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()
        budget_manager.get_user_usage = AsyncMock(return_value={"total_cost": 50.0})

        result = await budget_manager.check_user_budget("user-123", additional_cost=10.0)

        assert result["user_id"] == "user-123"
        assert result["current_cost"] == 50.0
        assert result["budget_limit"] == 100.0
        assert result["remaining_budget"] == 40.0
        assert result["projected_cost"] == 60.0
        assert result["within_budget"] is True
        assert result["utilization_percent"] == 60.0

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_check_user_budget_over_limit(self, mock_get_db_manager):
        """Test user budget check over limit."""
        mock_db_manager = Mock()
        mock_db_manager.query_items = AsyncMock(return_value=[])  # No budget config found
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()
        budget_manager.get_user_usage = AsyncMock(return_value={"total_cost": 95.0})

        result = await budget_manager.check_user_budget("user-123", additional_cost=10.0)

        assert result["projected_cost"] == 105.0
        assert result["within_budget"] is False
        assert result["utilization_percent"] == 105.0

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_check_provider_budget_success(self, mock_get_db_manager):
        """Test provider budget check."""
        mock_db_manager = Mock()
        mock_usage_records = [{"cost": 100.0}, {"cost": 50.0}]
        mock_db_manager.query_items = AsyncMock(return_value=mock_usage_records)
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()

        result = await budget_manager.check_provider_budget(LLMProvider.OPENAI, additional_cost=25.0)

        assert result["provider"] == LLMProvider.OPENAI
        assert result["current_cost"] == 150.0
        assert result["budget_limit"] == 500.0
        assert result["projected_cost"] == 175.0
        assert result["within_budget"] is True
        assert result["utilization_percent"] == 35.0

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_check_provider_budget_over_limit(self, mock_get_db_manager):
        """Test provider budget check over limit."""
        mock_db_manager = Mock()
        mock_usage_records = [{"cost": 400.0}, {"cost": 150.0}]
        mock_db_manager.query_items = AsyncMock(return_value=mock_usage_records)
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()

        result = await budget_manager.check_provider_budget(LLMProvider.OPENAI, additional_cost=0.0)

        assert result["current_cost"] == 550.0
        assert result["within_budget"] is False
        assert result["utilization_percent"] == pytest.approx(110.0, rel=1e-9)

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_get_budget_alerts_critical(self, mock_get_db_manager):
        """Test budget alerts with critical thresholds."""
        budget_manager = BudgetManager()

        # Mock system usage
        budget_manager.get_system_usage = AsyncMock(
            return_value={
                "top_users": [
                    {"user_id": "user-123", "cost": 95.0},
                    {"user_id": "user-456", "cost": 80.0},
                ]
            }
        )

        # Mock provider budget checks
        provider_budget_critical = {
            "utilization_percent": 95.0,
            "remaining_budget": 25.0,
        }
        provider_budget_warning = {
            "utilization_percent": 80.0,
            "remaining_budget": 100.0,
        }
        provider_budget_ok = {"utilization_percent": 50.0, "remaining_budget": 250.0}

        budget_manager.check_provider_budget = AsyncMock(
            side_effect=[
                provider_budget_critical,  # OPENAI
                provider_budget_warning,  # ANTHROPIC
                provider_budget_ok,  # GOOGLE
            ]
        )

        # Mock user budget checks
        user_budget_critical = {"utilization_percent": 95.0, "remaining_budget": 5.0}
        user_budget_ok = {"utilization_percent": 80.0, "remaining_budget": 20.0}

        budget_manager.check_user_budget = AsyncMock(
            side_effect=[user_budget_critical, user_budget_ok]  # user-123  # user-456
        )

        alerts = await budget_manager.get_budget_alerts()

        # Should have alerts for critical provider and critical user
        assert len(alerts) >= 2

        # Check for provider critical alert
        provider_alerts = [a for a in alerts if a["type"] == "provider_budget_critical"]
        assert len(provider_alerts) == 1
        assert provider_alerts[0]["provider"] == LLMProvider.OPENAI

        # Check for provider warning alert
        warning_alerts = [a for a in alerts if a["type"] == "provider_budget_warning"]
        assert len(warning_alerts) == 1
        assert warning_alerts[0]["provider"] == LLMProvider.ANTHROPIC

        # Check for user critical alert
        user_alerts = [a for a in alerts if a["type"] == "user_budget_critical"]
        assert len(user_alerts) == 1
        assert user_alerts[0]["user_id"] == "user-123"

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_get_budget_alerts_error_handling(self, mock_get_db_manager):
        """Test budget alerts error handling."""
        budget_manager = BudgetManager()
        budget_manager.get_system_usage = AsyncMock(side_effect=Exception("System error"))

        alerts = await budget_manager.get_budget_alerts()

        # Should return empty list on error
        assert alerts == []

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    async def test_get_daily_usage_aggregation(self):
        """Test daily usage aggregation."""
        budget_manager = BudgetManager()

        usage_records = [
            {"date": "2024-01-15", "cost": 0.05, "tokens_used": 100},
            {"date": "2024-01-15", "cost": 0.03, "tokens_used": 75},
            {"date": "2024-01-16", "cost": 0.04, "tokens_used": 80},
        ]

        result = await budget_manager._get_daily_usage(usage_records)

        assert "2024-01-15" in result
        assert "2024-01-16" in result
        assert result["2024-01-15"]["cost"] == 0.08
        assert result["2024-01-15"]["tokens"] == 175
        assert result["2024-01-15"]["requests"] == 2
        assert result["2024-01-16"]["cost"] == 0.04
        assert result["2024-01-16"]["tokens"] == 80
        assert result["2024-01-16"]["requests"] == 1

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    async def test_get_daily_usage_with_timestamp_fallback(self):
        """Test daily usage with timestamp fallback."""
        budget_manager = BudgetManager()

        usage_records = [{"timestamp": "2024-01-15T10:00:00Z", "cost": 0.05, "tokens_used": 100}]

        result = await budget_manager._get_daily_usage(usage_records)

        assert "2024-01-15" in result
        assert result["2024-01-15"]["cost"] == 0.05


class TestBudgetManagerEdgeCases:
    """Test suite for BudgetManager edge cases."""

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_get_user_usage_empty_records(self, mock_get_db_manager):
        """Test user usage with no records."""
        mock_db_manager = Mock()
        mock_db_manager.query_items = AsyncMock(return_value=[])
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()
        budget_manager._get_daily_usage = AsyncMock(return_value={})

        result = await budget_manager.get_user_usage("user-123", days=30)

        assert result["total_cost"] == 0
        assert result["total_tokens"] == 0
        assert result["total_requests"] == 0
        assert result["provider_breakdown"] == {}

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_check_provider_budget_unknown_provider(self, mock_get_db_manager):
        """Test provider budget check with unknown provider."""
        mock_db_manager = Mock()
        mock_db_manager.query_items = AsyncMock(return_value=[])
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()

        # Create a mock provider that's not in the budget limits
        with patch("api.shared.models.LLMProvider") as mock_provider:
            mock_provider.UNKNOWN = "unknown"

            result = await budget_manager.check_provider_budget("unknown", additional_cost=0.0)

            assert result["budget_limit"] == 500.0  # Default limit

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_get_system_usage_error(self, mock_get_db_manager):
        """Test system usage error handling."""
        mock_db_manager = Mock()
        mock_db_manager.query_items = AsyncMock(side_effect=Exception("Query error"))
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()

        # Error is caught and default response returned
        result = await budget_manager.get_system_usage(days=30)

        # Should return default error response
        assert result["total_cost"] == 0
        assert result["total_tokens"] == 0
        assert result["total_requests"] == 0


class TestGlobalFunctions:
    """Test suite for global budget functions."""

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_get_budget_manager_singleton(self):
        """Test that get_budget_manager returns singleton instance."""
        manager1 = get_budget_manager()
        manager2 = get_budget_manager()

        assert manager1 is manager2
        assert isinstance(manager1, BudgetManager)


class TestCostManagementFeatures:
    """Test suite for new cost management features."""

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_get_real_time_budget_status(self, mock_get_db_manager):
        """Test real-time budget status tracking."""
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()
        budget_manager.get_user_usage = AsyncMock(
            return_value={
                "total_cost": 75.0,
                "total_tokens": 1500,
                "total_requests": 30,
            }
        )

        result = await budget_manager.get_real_time_budget_status("user-123")

        assert result["user_id"] == "user-123"
        assert result["current_cost"] == 75.0
        assert result["budget_limit"] == 100.0
        assert result["remaining_budget"] == 25.0
        assert result["utilization_percent"] == 75.0
        assert result["status"] == "warning"  # > 70%
        assert "last_updated" in result

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_predict_monthly_costs(self, mock_get_db_manager):
        """Test monthly cost prediction."""
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()

        # Mock historical data for the last 7 days
        historical_usage = []
        base_date = datetime.now(timezone.utc) - timedelta(days=7)
        for i in range(7):
            date = base_date + timedelta(days=i)
            historical_usage.append(
                {
                    "user_id": "user-123",
                    "cost": 5.0 + (i * 0.5),  # Increasing trend
                    "date": date.strftime("%Y-%m-%d"),
                    "timestamp": date.isoformat(),
                }
            )

        mock_db_manager.query_items = AsyncMock(return_value=historical_usage)

        result = await budget_manager.predict_monthly_costs("user-123")

        assert result["user_id"] == "user-123"
        assert "predicted_monthly_cost" in result
        assert "trend" in result
        assert "confidence" in result
        assert result["trend"] == "increasing"
        assert result["predicted_monthly_cost"] > 150  # Should predict growth

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_estimate_operation_cost(self, mock_get_db_manager):
        """Test operation cost estimation."""
        budget_manager = BudgetManager()

        # Test different models and operations
        test_cases = [
            {
                "provider": LLMProvider.OPENAI,
                "model": "gpt-4",
                "operation": "completion",
                "input_tokens": 1000,
                "expected_output_tokens": 500,
                "expected_min_cost": 0.03,  # Should be reasonable for GPT-4
            },
            {
                "provider": LLMProvider.ANTHROPIC,
                "model": "claude-3",
                "operation": "completion",
                "input_tokens": 1000,
                "expected_output_tokens": 500,
                "expected_min_cost": 0.02,
            },
        ]

        for test_case in test_cases:
            result = await budget_manager.estimate_operation_cost(
                provider=test_case["provider"],
                model=test_case["model"],
                operation=test_case["operation"],
                input_tokens=test_case["input_tokens"],
                expected_output_tokens=test_case["expected_output_tokens"],
            )

            assert result["provider"] == test_case["provider"]
            assert result["model"] == test_case["model"]
            assert result["estimated_cost"] >= test_case["expected_min_cost"]
            assert "input_cost" in result
            assert "output_cost" in result
            assert "total_tokens" in result

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_automated_cost_controls(self, mock_get_db_manager):
        """Test automated cost control actions."""
        budget_manager = BudgetManager()

        # Test user budget enforcement
        budget_manager.get_user_usage = AsyncMock(return_value={"total_cost": 95.0})

        result = await budget_manager.check_and_enforce_budget("user-123", 10.0)

        assert result["action"] == "block"
        assert result["reason"] == "User budget limit exceeded"
        assert not result["allowed"]

        # Test provider budget enforcement
        mock_db_manager = Mock()
        mock_db_manager.query_items = AsyncMock(return_value=[{"cost": 480.0}])
        mock_get_db_manager.return_value = mock_db_manager

        result = await budget_manager.check_and_enforce_provider_budget(LLMProvider.OPENAI, 30.0)

        assert result["action"] == "warn"
        assert result["allowed"]
        assert "warning" in result["reason"]

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_budget_configuration_management(self, mock_get_db_manager):
        """Test budget configuration management."""
        mock_db_manager = Mock()
        mock_db_manager.create_item = AsyncMock()
        mock_db_manager.query_items = AsyncMock(return_value=[])
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()

        # Test setting user budget
        config = {
            "user_id": "user-123",
            "daily_limit": 25.0,
            "monthly_limit": 500.0,
            "alert_thresholds": [50, 75, 90],
            "auto_block": True,
        }

        result = await budget_manager.set_user_budget_config(config)

        assert result["user_id"] == "user-123"
        assert result["daily_limit"] == 25.0
        assert result["monthly_limit"] == 500.0
        assert result["auto_block"] is True
        # Expect 2 calls: one for budget config, one for usage metrics initialization
        assert mock_db_manager.create_item.call_count == 2

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_cost_analytics_dashboard_data(self, mock_get_db_manager):
        """Test cost analytics dashboard data generation."""
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager

        # Mock usage data for analytics
        usage_data = []
        for i in range(30):
            date = datetime.now(timezone.utc) - timedelta(days=i)
            usage_data.extend(
                [
                    {
                        "user_id": f"user-{j}",
                        "provider": "openai",
                        "cost": 2.0 + (i * 0.1),
                        "tokens_used": 400,
                        "date": date.strftime("%Y-%m-%d"),
                        "timestamp": date.isoformat(),
                    }
                    for j in range(1, 4)  # 3 users per day
                ]
            )

        mock_db_manager.query_items = AsyncMock(return_value=usage_data)

        budget_manager = BudgetManager()
        result = await budget_manager.get_cost_analytics_data(days=30)

        assert "total_cost" in result
        assert "daily_breakdown" in result
        assert "provider_breakdown" in result
        assert "user_breakdown" in result
        assert "cost_trends" in result
        assert len(result["daily_breakdown"]) <= 30
        assert result["total_cost"] > 0

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_anomaly_detection(self, mock_get_db_manager):
        """Test cost anomaly detection."""
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager

        # Create usage pattern with anomaly
        normal_usage = []
        anomaly_usage = []

        # Normal usage: $5/day for 28 days
        for i in range(28):
            date = datetime.now(timezone.utc) - timedelta(days=29 - i)
            normal_usage.append(
                {
                    "user_id": "user-123",
                    "cost": 5.0,
                    "date": date.strftime("%Y-%m-%d"),
                    "timestamp": date.isoformat(),
                }
            )

        # Anomaly: $50 in one day
        anomaly_date = datetime.now(timezone.utc) - timedelta(days=1)
        anomaly_usage.append(
            {
                "user_id": "user-123",
                "cost": 50.0,
                "date": anomaly_date.strftime("%Y-%m-%d"),
                "timestamp": anomaly_date.isoformat(),
            }
        )

        all_usage = normal_usage + anomaly_usage
        mock_db_manager.query_items = AsyncMock(return_value=all_usage)

        budget_manager = BudgetManager()
        result = await budget_manager.detect_cost_anomalies("user-123", days=30)

        assert len(result["anomalies"]) > 0
        assert result["anomalies"][0]["severity"] == "high"
        assert result["anomalies"][0]["cost"] == 50.0

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_multi_tier_budget_enforcement(self, mock_get_db_manager):
        """Test multi-tier budget enforcement."""
        budget_manager = BudgetManager()

        # Test tier-based limits
        test_cases = [
            {
                "user_tier": "basic",
                "current_usage": 40.0,
                "additional_cost": 5.0,
                "expected_action": "warn",  # 45.0 <= 50.0 but > 45.0 (90% of 50.0)
            },
            {
                "user_tier": "premium",
                "current_usage": 170.0,
                "additional_cost": 20.0,
                "expected_action": "warn",  # 190.0 <= 200.0 but > 180.0 (90% of 200.0)
            },
            {
                "user_tier": "basic",
                "current_usage": 48.0,
                "additional_cost": 5.0,
                "expected_action": "block",  # 53.0 > 50.0
            },
        ]

        for test_case in test_cases:
            budget_manager.get_user_usage = AsyncMock(return_value={"total_cost": test_case["current_usage"]})

            result = await budget_manager.check_tier_based_budget(
                user_id="user-123",
                user_tier=test_case["user_tier"],
                additional_cost=test_case["additional_cost"],
            )

            assert result["action"] == test_case["expected_action"]
            assert "tier_limit" in result
            assert "utilization_percent" in result

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_cost_optimization_suggestions(self, mock_get_db_manager):
        """Test cost optimization suggestions."""
        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager

        # Mock usage data showing expensive model usage
        usage_data = [
            {
                "user_id": "user-123",
                "provider": "openai",
                "cost": 2.0,
                "model": "gpt-4",
                "operation": "completion",
                "tokens_used": 500,
                "date": "2024-01-15",
            },
            {
                "user_id": "user-123",
                "provider": "openai",
                "cost": 0.5,
                "model": "gpt-3.5-turbo",
                "operation": "completion",
                "tokens_used": 500,
                "date": "2024-01-15",
            },
        ]

        mock_db_manager.query_items = AsyncMock(return_value=usage_data)

        budget_manager = BudgetManager()
        result = await budget_manager.get_cost_optimization_suggestions("user-123")

        assert "suggestions" in result
        assert len(result["suggestions"]) > 0
        assert "potential_savings" in result
        assert result["potential_savings"] > 0

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_real_time_cost_tracking_stream(self, mock_get_db_manager):
        """Test real-time cost tracking for streaming operations."""
        mock_db_manager = Mock()
        mock_db_manager.create_item = AsyncMock()
        mock_db_manager.update_item = AsyncMock()
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()

        # Simulate streaming operation with incremental costs
        operation_id = "op-123"

        # Start tracking
        result = await budget_manager.start_operation_tracking(
            operation_id=operation_id,
            user_id="user-123",
            provider=LLMProvider.OPENAI,
            model="gpt-4",
        )

        assert result["success"] is True
        assert result["operation_id"] == operation_id
        mock_db_manager.create_item.assert_called_once()

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_budget_alerts_with_notifications(self, mock_get_db_manager):
        """Test budget alerts with notification system."""
        budget_manager = BudgetManager()

        # Mock high usage scenario
        budget_manager.get_system_usage = AsyncMock(
            return_value={
                "top_users": [
                    {"user_id": "user-123", "cost": 95.0},
                    {"user_id": "user-456", "cost": 85.0},
                ]
            }
        )

        budget_manager.check_user_budget = AsyncMock(return_value={"utilization_percent": 95.0, "remaining_budget": 5.0})

        # Mock notification sending
        with patch("api.shared.budget.send_notification") as mock_send:
            mock_send.return_value = True

            alerts = await budget_manager.process_budget_alerts_with_notifications()

            assert len(alerts) > 0
            assert any(alert["type"] == "user_budget_critical" for alert in alerts)
            # Verify notifications were attempted
            assert mock_send.call_count >= len(alerts)

    @pytest.mark.asyncio
    async def test_cost_estimation_edge_cases(self):
        """Test cost estimation edge cases."""
        budget_manager = BudgetManager()

        # Test with zero tokens
        result = await budget_manager.estimate_operation_cost(
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            operation="completion",
            input_tokens=0,
            expected_output_tokens=0,
        )

        assert result["estimated_cost"] == 0.0

        # Test with unknown model (should use default rates)
        result = await budget_manager.estimate_operation_cost(
            provider=LLMProvider.OPENAI,
            model="unknown-model",
            operation="completion",
            input_tokens=1000,
            expected_output_tokens=500,
        )

        assert result["estimated_cost"] > 0.0
        assert "model" in result["warnings"]

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_budget_reset_and_rollover(self, mock_get_db_manager):
        """Test budget reset and rollover functionality."""
        mock_db_manager = Mock()
        mock_db_manager.create_item = AsyncMock()
        mock_db_manager.update_item = AsyncMock()
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()

        # Test monthly budget reset
        result = await budget_manager.reset_monthly_budgets()

        assert result["reset_count"] >= 0
        assert "reset_timestamp" in result

        # Test budget rollover for unused amounts
        rollover_result = await budget_manager.process_budget_rollover("user-123", 25.0)

        assert rollover_result["user_id"] == "user-123"
        assert rollover_result["rollover_amount"] == 25.0
        assert "new_budget_amount" in rollover_result
