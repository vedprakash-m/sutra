"""
Tests for budget.py module - Budget tracking and limits
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from api.shared.budget import BudgetManager, get_budget_manager
from api.shared.models import UsageRecord, LLMProvider


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
        budget_manager._get_daily_usage = AsyncMock(
            return_value={"2024-01-15": {"cost": 0.08, "tokens": 175, "requests": 2}}
        )

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
        budget_manager._get_daily_usage = AsyncMock(
            return_value={"2024-01-15": {"cost": 0.08, "tokens": 175, "requests": 2}}
        )

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
        budget_manager = BudgetManager()
        budget_manager.get_user_usage = AsyncMock(return_value={"total_cost": 50.0})

        result = await budget_manager.check_user_budget(
            "user-123", additional_cost=10.0
        )

        assert result["user_id"] == "user-123"
        assert result["current_cost"] == 50.0
        assert result["budget_limit"] == 100.0
        assert result["remaining_budget"] == 50.0
        assert result["projected_cost"] == 60.0
        assert result["within_budget"] is True
        assert result["utilization_percent"] == 60.0

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_check_user_budget_over_limit(self, mock_get_db_manager):
        """Test user budget check over limit."""
        budget_manager = BudgetManager()
        budget_manager.get_user_usage = AsyncMock(return_value={"total_cost": 95.0})

        result = await budget_manager.check_user_budget(
            "user-123", additional_cost=10.0
        )

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

        result = await budget_manager.check_provider_budget(
            LLMProvider.OPENAI, additional_cost=25.0
        )

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

        result = await budget_manager.check_provider_budget(
            LLMProvider.OPENAI, additional_cost=0.0
        )

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
        budget_manager.get_system_usage = AsyncMock(
            side_effect=Exception("System error")
        )

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

        usage_records = [
            {"timestamp": "2024-01-15T10:00:00Z", "cost": 0.05, "tokens_used": 100}
        ]

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

            result = await budget_manager.check_provider_budget(
                "unknown", additional_cost=0.0
            )

            assert result["budget_limit"] == 100.0  # Default limit

    @pytest.mark.asyncio
    @patch("api.shared.budget.get_database_manager")
    async def test_get_system_usage_error(self, mock_get_db_manager):
        """Test system usage error handling."""
        mock_db_manager = Mock()
        mock_db_manager.query_items = AsyncMock(side_effect=Exception("Query error"))
        mock_get_db_manager.return_value = mock_db_manager

        budget_manager = BudgetManager()

        with pytest.raises(Exception, match="Query error"):
            await budget_manager.get_system_usage(days=30)


class TestGlobalFunctions:
    """Test suite for global budget functions."""

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_get_budget_manager_singleton(self):
        """Test that get_budget_manager returns singleton instance."""
        manager1 = get_budget_manager()
        manager2 = get_budget_manager()

        assert manager1 is manager2
        assert isinstance(manager1, BudgetManager)
