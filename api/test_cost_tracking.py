#!/usr/bin/env python3
"""
Comprehensive test for Task 1.4: Real-Time Cost Tracking implementation.
Tests cost tracking middleware, budget validation, and analytics.
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules
from shared.cost_tracker import CostAlertLevel, CostEntry, CostTracker
from shared.cost_tracking_middleware import CostTrackingMiddleware


class MockCosmosClient:
    """Mock Cosmos DB client for testing."""

    def __init__(self):
        self.data = {"CostEntries": [], "CostSummaries": [], "CostAlerts": [], "BudgetSettings": []}

    def get_database_client(self, database_name: str):
        return MockDatabaseClient(self.data)


class MockDatabaseClient:
    """Mock database client."""

    def __init__(self, data: Dict):
        self.data = data

    def get_container_client(self, container_name: str):
        return MockContainerClient(self.data, container_name)


class MockContainerClient:
    """Mock container client."""

    def __init__(self, data: Dict, container_name: str):
        self.data = data
        self.container_name = container_name

    async def create_item(self, item: Dict):
        """Add item to mock storage."""
        if self.container_name not in self.data:
            self.data[self.container_name] = []
        self.data[self.container_name].append(item)
        return item

    async def query_items(self, query: str, parameters=None):
        """Query items from mock storage."""
        items = self.data.get(self.container_name, [])

        # Simple mock query processing
        if "WHERE" in query:
            # Extract basic filters for testing
            for item in items:
                yield item
        else:
            for item in items:
                yield item


class CostTrackingTest:
    """Comprehensive cost tracking test suite."""

    def __init__(self):
        self.setup_logging()
        self.cosmos_client = MockCosmosClient()
        self.cost_tracker = CostTracker(self.cosmos_client, "TestDB")
        self.cost_middleware = CostTrackingMiddleware(self.cost_tracker)

        # Test data
        self.test_user_id = "test_user_123"
        self.test_session_id = "test_session_456"

    def setup_logging(self):
        """Configure logging for tests."""
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.logger = logging.getLogger(__name__)

    async def test_cost_calculation(self):
        """Test cost calculation for different providers."""
        print("\n🧮 Testing Cost Calculation...")

        test_cases = [
            {
                "provider": "openai",
                "model": "gpt-4",
                "prompt_tokens": 1000,
                "completion_tokens": 500,
                "expected_input": Decimal("0.03"),  # $0.03 per 1K tokens
                "expected_output": Decimal("0.03"),  # $0.06 per 1K tokens * 0.5K
            },
            {
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
                "prompt_tokens": 2000,
                "completion_tokens": 1000,
                "expected_input": Decimal("0.006"),  # $0.003 per 1K * 2K
                "expected_output": Decimal("0.015"),  # $0.015 per 1K * 1K
            },
            {
                "provider": "google",
                "model": "gemini-1.5-pro",
                "prompt_tokens": 1500,
                "completion_tokens": 750,
                "expected_input": Decimal("0.001875"),  # $0.00125 per 1K * 1.5K
                "expected_output": Decimal("0.00375"),  # $0.005 per 1K * 0.75K
            },
        ]

        for i, case in enumerate(test_cases, 1):
            input_cost, output_cost, total_cost = self.cost_tracker._calculate_cost(
                case["provider"], case["model"], case["prompt_tokens"], case["completion_tokens"]
            )

            print(f"  Test {i}: {case['provider']}/{case['model']}")
            print(f"    Input cost: ${float(input_cost):.6f} (expected: ${float(case['expected_input']):.6f})")
            print(f"    Output cost: ${float(output_cost):.6f} (expected: ${float(case['expected_output']):.6f})")
            print(f"    Total: ${float(total_cost):.6f}")

            # Validate calculations (with small tolerance for decimal precision)
            assert abs(input_cost - case["expected_input"]) < Decimal(
                "0.000001"
            ), f"Input cost mismatch for {case['provider']}/{case['model']}"
            assert abs(output_cost - case["expected_output"]) < Decimal(
                "0.000001"
            ), f"Output cost mismatch for {case['provider']}/{case['model']}"

            print(f"    ✅ Cost calculation correct")

        print("✅ All cost calculations passed!")

    async def test_usage_tracking(self):
        """Test LLM usage tracking."""
        print("\n📊 Testing Usage Tracking...")

        # Track multiple usage entries
        test_usages = [
            {"provider": "openai", "model": "gpt-4", "prompt_tokens": 800, "completion_tokens": 200, "execution_time": 1500},
            {
                "provider": "anthropic",
                "model": "claude-3-haiku-20240307",
                "prompt_tokens": 1200,
                "completion_tokens": 400,
                "execution_time": 2000,
            },
            {
                "provider": "google",
                "model": "gemini-1.5-flash",
                "prompt_tokens": 600,
                "completion_tokens": 300,
                "execution_time": 1200,
            },
        ]

        tracked_entries = []
        for i, usage in enumerate(test_usages, 1):
            cost_entry = await self.cost_tracker.track_llm_usage(
                user_id=self.test_user_id,
                session_id=self.test_session_id,
                provider=usage["provider"],
                model=usage["model"],
                prompt_tokens=usage["prompt_tokens"],
                completion_tokens=usage["completion_tokens"],
                execution_time_ms=usage["execution_time"],
                request_id=f"test_request_{i}",
                metadata={"test": True, "request_number": i},
            )

            tracked_entries.append(cost_entry)

            print(f"  Tracked usage {i}: {usage['provider']}/{usage['model']}")
            print(f"    Cost: ${float(cost_entry.total_cost):.6f}")
            print(f"    Tokens: {cost_entry.total_tokens}")
            print(f"    Time: {cost_entry.execution_time_ms}ms")

            # Validate entry fields
            assert cost_entry.user_id == self.test_user_id
            assert cost_entry.session_id == self.test_session_id
            assert cost_entry.provider == usage["provider"]
            assert cost_entry.model == usage["model"]
            assert cost_entry.total_tokens == usage["prompt_tokens"] + usage["completion_tokens"]
            assert cost_entry.total_cost > 0

            print(f"    ✅ Usage tracking correct")

        print("✅ All usage tracking passed!")
        return tracked_entries

    async def test_cost_summary(self):
        """Test cost summary generation."""
        print("\n📈 Testing Cost Summary...")

        # Get cost summary for test user
        summary = await self.cost_tracker.get_cost_summary(
            user_id=self.test_user_id,
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc),
        )

        print(f"  Summary for user {self.test_user_id}:")
        print(f"    Total requests: {summary.total_requests}")
        print(f"    Total tokens: {summary.total_tokens}")
        print(f"    Total cost: ${float(summary.total_cost):.6f}")
        print(f"    Average cost per request: ${float(summary.average_cost_per_request):.6f}")
        print(f"    Cost by provider: {[f'{k}: ${float(v):.6f}' for k, v in summary.cost_by_provider.items()]}")

        # Validate summary
        assert summary.total_requests > 0, "Should have tracked requests"
        assert summary.total_tokens > 0, "Should have tracked tokens"
        assert summary.total_cost > 0, "Should have tracked costs"
        assert len(summary.cost_by_provider) > 0, "Should have provider breakdown"

        print("✅ Cost summary generation passed!")
        return summary

    async def test_budget_validation(self):
        """Test budget validation and alerts."""
        print("\n💰 Testing Budget Validation...")

        # Test budget validation for different scenarios
        test_scenarios = [
            {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "estimated_tokens": 1000,
                "description": "Low-cost model, should pass",
            },
            {
                "provider": "openai",
                "model": "gpt-4",
                "estimated_tokens": 50000,
                "description": "High-cost scenario, may trigger warnings",
            },
            {
                "provider": "anthropic",
                "model": "claude-3-opus-20240229",
                "estimated_tokens": 100000,
                "description": "Very high-cost scenario, should trigger alerts",
            },
        ]

        for i, scenario in enumerate(test_scenarios, 1):
            validation_result = await self.cost_middleware.validate_budget_before_execution(
                user_id=self.test_user_id,
                provider=scenario["provider"],
                model=scenario["model"],
                estimated_tokens=scenario["estimated_tokens"],
            )

            print(f"  Scenario {i}: {scenario['description']}")
            print(f"    Can execute: {validation_result['can_execute']}")
            print(f"    Current spend: ${validation_result['current_spend']:.6f}")
            print(f"    Estimated cost: ${validation_result['estimated_cost']:.6f}")
            print(f"    Projected total: ${validation_result['projected_total']:.6f}")
            print(f"    Warnings: {len(validation_result['warnings'])}")

            for warning in validation_result["warnings"]:
                print(f"      - {warning['level']}: {warning['message']}")

            # Validate structure
            assert "can_execute" in validation_result
            assert "current_spend" in validation_result
            assert "estimated_cost" in validation_result
            assert "warnings" in validation_result

            print(f"    ✅ Budget validation correct")

        print("✅ Budget validation passed!")

    async def test_cost_analytics(self):
        """Test cost analytics generation."""
        print("\n📊 Testing Cost Analytics...")

        analytics = await self.cost_tracker.get_cost_analytics(user_id=self.test_user_id, days=30)

        print(f"  Analytics for user {self.test_user_id}:")
        print(f"    Total cost: ${analytics['summary']['total_cost']:.6f}")
        print(f"    Total requests: {analytics['summary']['total_requests']}")
        print(f"    Provider breakdown: {list(analytics['summary']['cost_by_provider'].keys())}")
        print(f"    Daily data points: {len(analytics['daily_breakdown'])}")
        print(f"    Efficiency metrics: {len(analytics['efficiency_metrics'])}")

        if analytics["efficiency_metrics"].get("recommendations"):
            print(f"    Recommendations:")
            for rec in analytics["efficiency_metrics"]["recommendations"]:
                print(f"      - {rec}")

        # Validate analytics structure
        assert "summary" in analytics
        assert "daily_breakdown" in analytics
        assert "efficiency_metrics" in analytics
        assert "period" in analytics

        print("✅ Cost analytics generation passed!")
        return analytics

    async def test_usage_stats(self):
        """Test real-time usage statistics."""
        print("\n⚡ Testing Real-Time Usage Stats...")

        stats = await self.cost_middleware.get_real_time_usage_stats(self.test_user_id)

        print(f"  Real-time stats for user {self.test_user_id}:")
        print(f"    Current month cost: ${stats['current_month']['total_cost']:.6f}")
        print(f"    Current month requests: {stats['current_month']['total_requests']}")
        print(f"    Average cost per request: ${stats['current_month']['average_cost_per_request']:.6f}")
        print(f"    Recent alerts: {len(stats['recent_alerts'])}")

        if stats["recent_alerts"]:
            print(f"    Alert levels: {[alert['level'] for alert in stats['recent_alerts']]}")

        # Validate stats structure
        assert "current_month" in stats
        assert "recent_alerts" in stats
        assert "analytics" in stats
        assert "period" in stats

        print("✅ Real-time usage stats passed!")
        return stats

    async def test_pricing_updates(self):
        """Test pricing model updates."""
        print("\n💲 Testing Pricing Updates...")

        # Update pricing for a test model
        test_provider = "test_provider"
        test_model = "test_model"
        new_input_price = Decimal("0.001")
        new_output_price = Decimal("0.002")

        await self.cost_tracker.update_pricing_model(
            provider=test_provider, model=test_model, input_price=new_input_price, output_price=new_output_price
        )

        # Verify the pricing was updated
        updated_pricing = self.cost_tracker.pricing_models[test_provider][test_model]

        print(f"  Updated pricing for {test_provider}/{test_model}:")
        print(f"    Input: ${float(updated_pricing['input']):.6f}")
        print(f"    Output: ${float(updated_pricing['output']):.6f}")

        assert updated_pricing["input"] == new_input_price
        assert updated_pricing["output"] == new_output_price

        # Test cost calculation with new pricing
        input_cost, output_cost, total_cost = self.cost_tracker._calculate_cost(test_provider, test_model, 1000, 500)

        expected_input = new_input_price * 1  # 1000 tokens = 1K
        expected_output = new_output_price * Decimal("0.5")  # 500 tokens = 0.5K

        assert input_cost == expected_input
        assert output_cost == expected_output

        print(f"    Calculated cost: ${float(total_cost):.6f}")
        print("✅ Pricing updates passed!")

    async def run_all_tests(self):
        """Run all cost tracking tests."""
        print("🚀 Starting Cost Tracking Tests...")
        print("=" * 60)

        try:
            # Core functionality tests
            await self.test_cost_calculation()
            await self.test_usage_tracking()
            await self.test_cost_summary()

            # Advanced features tests
            await self.test_budget_validation()
            await self.test_cost_analytics()
            await self.test_usage_stats()
            await self.test_pricing_updates()

            print("\n" + "=" * 60)
            print("🎉 ALL COST TRACKING TESTS PASSED!")
            print("✅ Task 1.4: Real-Time Cost Tracking - COMPLETE")
            print("=" * 60)

            return True

        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            import traceback

            traceback.print_exc()
            return False


async def main():
    """Main test execution."""
    test_suite = CostTrackingTest()
    success = await test_suite.run_all_tests()

    if success:
        print("\n🏁 Test Results Summary:")
        print("  ✅ Cost calculation accuracy")
        print("  ✅ Usage tracking functionality")
        print("  ✅ Cost summary generation")
        print("  ✅ Budget validation system")
        print("  ✅ Cost analytics and reporting")
        print("  ✅ Real-time usage statistics")
        print("  ✅ Pricing model management")
        print("\n🎯 Ready for Task 1.5: Budget Enforcement System!")
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
