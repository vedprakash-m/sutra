"""
Tests for cost_management_api - Budget and cost tracking endpoints
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

import azure.functions as func
from api.cost_management_api import main
from api.shared.budget import BudgetManager
from api.shared.models import LLMProvider, User, UserRole


class TestCostManagementAPI:
    """Test suite for cost management API endpoints."""

    @pytest.fixture
    def mock_budget_manager(self):
        """Create a mock budget manager."""
        manager = Mock(spec=BudgetManager)
        return manager

    @pytest.mark.asyncio
    @patch("api.cost_management_api.get_enhanced_budget_manager")
    @patch("api.cost_management_api.get_current_user")
    async def test_get_budget_status_success(self, mock_get_user, mock_get_manager, mock_budget_manager):
        """Test successful budget status retrieval."""
        # Setup mocks
        mock_user = User(
            id="user-123",
            email="test@example.com",
            name="Test User",
            role=UserRole.USER,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_get_user.return_value = mock_user
        mock_get_manager.return_value = mock_budget_manager

        mock_budget_manager.get_real_time_usage = AsyncMock(return_value={
            "current_spend": 75.0,
            "execution_count": 50,
            "budget_utilization": 37.5,
            "alerts_triggered": []
        })
        # Create a mock BudgetConfig object
        mock_budget_config = Mock()
        mock_budget_config.budget_amount = 200.0
        mock_budget_config.budget_period = "monthly"
        mock_budget_config.alert_thresholds = [50, 75, 90, 95]
        mock_budget_manager.get_budget_config = AsyncMock(return_value=mock_budget_config)

        # Create request
        req = func.HttpRequest(
            method="GET",
            url="http://localhost:7071/api/cost-management/budget/usage",
            headers={"Content-Type": "application/json"},
            body=b""
        )

        # Call function
        response = await main(req)

        # Assertions
        assert response.status_code == 200
        response_data = json.loads(response.get_body().decode())
        assert response_data["entity_id"] == "user-123"
        assert response_data["current_spend"] == 75.0
        assert response_data["execution_count"] == 50
        assert response_data["budget_utilization"] == 37.5
        assert response_data["budget_amount"] == 200.0
        assert response_data["remaining_budget"] == 125.0  # 200 - 75

    @pytest.mark.asyncio
    @patch("api.cost_management_api.get_enhanced_budget_manager")
    @patch("api.cost_management_api.get_current_user")
    async def test_get_usage_analytics_success(self, mock_get_user, mock_get_manager, mock_budget_manager):
        """Test successful usage analytics retrieval."""
        # Setup mocks
        mock_user = User(
            id="user-123",
            email="admin@example.com",
            name="Admin User",
            role=UserRole.ADMIN,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_get_user.return_value = mock_user
        mock_get_manager.return_value = mock_budget_manager

        mock_budget_manager.get_cost_analytics_data = AsyncMock(return_value={
            "total_cost": 1500.0,
            "daily_breakdown": {"2024-01-15": {"cost": 50.0, "tokens": 1000}},
            "provider_breakdown": {"openai": {"cost": 800.0, "percentage": 53.3}},
            "user_breakdown": [{"user_id": "user-123", "cost": 300.0}],
            "cost_trends": {"trend": "stable", "change_percent": 2.1}
        })

        # Create request
        req = func.HttpRequest(
            method="GET",
            url="http://localhost:7071/api/cost-management/analytics?days=30",
            headers={"Content-Type": "application/json"},
            body=b""
        )

        # Call function
        response = await main(req)

        # Assertions
        assert response.status_code == 200
        response_data = json.loads(response.get_body().decode())
        assert "system_overview" in response_data
        assert "top_users" in response_data
        assert "model_usage" in response_data
        assert "budget_alerts" in response_data
        assert "cost_trends" in response_data
        assert response_data["system_overview"]["total_spend"] == 1250.50

    @pytest.mark.asyncio
    @patch("api.cost_management_api.get_enhanced_budget_manager")
    @patch("api.cost_management_api.get_current_user")
    async def test_cost_prediction_success(self, mock_get_user, mock_get_manager, mock_budget_manager):
        """Test successful cost prediction."""
        # Setup mocks
        mock_user = User(
            id="user-123",
            email="test@example.com",
            name="Test User",
            role=UserRole.USER,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_get_user.return_value = mock_user
        mock_get_manager.return_value = mock_budget_manager

        mock_budget_manager.generate_cost_predictions = AsyncMock(return_value={
            "user_id": "user-123",
            "predicted_monthly_cost": 180.0,
            "trend": "increasing",
            "confidence": 0.85,
            "prediction_date": datetime.now(timezone.utc).isoformat()
        })

        # Create request
        req = func.HttpRequest(
            method="GET",
            url="http://localhost:7071/api/cost-management/budget/predictions/user-123",
            headers={"Content-Type": "application/json"},
            body=b""
        )

        # Call function
        response = await main(req)

        # Assertions
        assert response.status_code == 200
        response_data = json.loads(response.get_body().decode())
        assert response_data["predicted_monthly_cost"] == 180.0
        assert response_data["trend"] == "increasing"
        assert response_data["confidence"] == 0.85

    @pytest.mark.asyncio
    @patch("api.cost_management_api.get_enhanced_budget_manager")
    @patch("api.cost_management_api.get_current_user")
    async def test_cost_estimation_success(self, mock_get_user, mock_get_manager, mock_budget_manager):
        """Test successful cost estimation."""
        # Setup mocks
        mock_user = User(
            id="user-123",
            email="test@example.com",
            name="Test User",
            role=UserRole.USER,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_get_user.return_value = mock_user
        mock_get_manager.return_value = mock_budget_manager

        mock_budget_manager.estimate_execution_cost = AsyncMock(return_value={
            "model": "gpt-4",
            "estimated_cost": 0.045,
            "input_cost": 0.030,
            "output_cost": 0.015,
            "total_tokens": 1500
        })
        mock_budget_manager.check_pre_execution_budget = AsyncMock(return_value={
            "within_budget": True,
            "remaining_budget": 125.0,
            "budget_limit": 200.0
        })

        # Create request body
        request_body = {
            "model": "gpt-4",
            "prompt": "Hello, how are you?",
            "max_tokens": 500
        }

        req = func.HttpRequest(
            method="POST",
            url="http://localhost:7071/api/cost-management/estimate",
            headers={"Content-Type": "application/json"},
            body=json.dumps(request_body).encode()
        )

        # Call function
        response = await main(req)

        # Assertions
        assert response.status_code == 200
        response_data = json.loads(response.get_body().decode())
        assert response_data["estimated_cost"] == 0.045
        assert response_data["model"] == "gpt-4"
        assert "budget_check" in response_data
        assert response_data["budget_check"]["within_budget"] == True

    @pytest.mark.asyncio
    @patch("api.cost_management_api.get_enhanced_budget_manager")
    @patch("api.cost_management_api.get_current_user")
    async def test_budget_configuration_update(self, mock_get_user, mock_get_manager, mock_budget_manager):
        """Test budget configuration update."""
        # Setup mocks
        mock_user = User(
            id="user-123",
            email="admin@example.com",
            name="Admin User",
            role=UserRole.ADMIN,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_get_user.return_value = mock_user
        mock_get_manager.return_value = mock_budget_manager

        mock_budget_manager.create_budget_config = AsyncMock(return_value=Mock(
            id="budget_user-123_2024-01-01",
            entity_type="user",
            entity_id="user-123",
            budget_amount=500.0,
            budget_period="monthly",
            alert_thresholds=[50, 75, 90]
        ))

        # Create request body
        request_body = {
            "entity_type": "user",
            "entity_id": "user-123",
            "budget_amount": 500.0,
            "budget_period": "monthly",
            "alert_thresholds": [50, 75, 90]
        }

        req = func.HttpRequest(
            method="POST",
            url="http://localhost:7071/api/cost-management/budget/config",
            headers={"Content-Type": "application/json"},
            body=json.dumps(request_body).encode()
        )

        # Call function
        response = await main(req)

        # Assertions
        assert response.status_code == 201
        response_data = json.loads(response.get_body().decode())
        assert response_data["success"] == True
        assert "budget_config" in response_data

    @pytest.mark.asyncio
    @patch("api.cost_management_api.get_enhanced_budget_manager")
    @patch("api.cost_management_api.get_current_user")
    async def test_alerts_retrieval(self, mock_get_user, mock_get_manager, mock_budget_manager):
        """Test budget alerts retrieval."""
        # Setup mocks
        mock_user = User(
            id="user-123",
            email="admin@example.com",
            name="Admin User",
            role=UserRole.ADMIN,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_get_user.return_value = mock_user
        mock_get_manager.return_value = mock_budget_manager

        mock_budget_manager.get_budget_alerts = AsyncMock(return_value=[
            {
                "type": "user_budget_critical",
                "user_id": "user-456",
                "utilization_percent": 95.0,
                "remaining_budget": 5.0,
                "severity": "critical",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            {
                "type": "provider_budget_warning",
                "provider": LLMProvider.OPENAI,
                "utilization_percent": 80.0,
                "remaining_budget": 100.0,
                "severity": "warning",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ])

        # Create request
        req = func.HttpRequest(
            method="GET",
            url="http://localhost:7071/api/cost-management/analytics",
            headers={"Content-Type": "application/json"},
            body=b""
        )

        # Call function
        response = await main(req)

        # Assertions
        assert response.status_code == 200
        response_data = json.loads(response.get_body().decode())
        assert "system_overview" in response_data
        assert "budget_alerts" in response_data
        assert response_data["budget_alerts"]["active_alerts"] == 3

    @pytest.mark.asyncio
    @patch("api.cost_management_api.get_current_user")
    async def test_unauthorized_access(self, mock_get_user):
        """Test unauthorized access to admin endpoints."""
        # Setup mocks - regular user trying to access admin endpoint
        mock_user = User(
            id="user-123",
            email="test@example.com",
            name="Test User",
            role=UserRole.USER,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_get_user.return_value = mock_user

        # Create request for admin endpoint
        req = func.HttpRequest(
            method="GET",
            url="http://localhost:7071/api/cost-management/analytics",
            headers={"Content-Type": "application/json"},
            body=b""
        )

        # Call function
        response = await main(req)

        # Assertions
        assert response.status_code == 403
        response_data = json.loads(response.get_body().decode())
        assert "admin access required" in response_data["error"].lower()

    @pytest.mark.asyncio
    async def test_missing_authentication(self):
        """Test request without authentication."""
        # Create request without user context
        req = func.HttpRequest(
            method="GET",
            url="http://localhost:7071/api/cost-management/budget/status",
            headers={"Content-Type": "application/json"},
            body=b""
        )

        # Call function
        response = await main(req)

        # Assertions
        assert response.status_code == 401

    @pytest.mark.asyncio
    @patch("api.cost_management_api.get_enhanced_budget_manager")
    @patch("api.cost_management_api.get_current_user")
    async def test_invalid_request_data(self, mock_get_user, mock_get_manager, mock_budget_manager):
        """Test handling of invalid request data."""
        # Setup mocks
        mock_user = User(
            id="user-123",
            email="test@example.com",
            name="Test User",
            role=UserRole.USER,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_get_user.return_value = mock_user
        mock_get_manager.return_value = mock_budget_manager

        # Create request with invalid JSON
        req = func.HttpRequest(
            method="POST",
            url="http://localhost:7071/api/cost-management/estimate",
            headers={"Content-Type": "application/json"},
            body=b"invalid json"
        )

        # Call function
        response = await main(req)

        # Assertions
        assert response.status_code == 500  # JSON parsing error causes 500
        response_data = json.loads(response.get_body().decode())
        assert "error" in response_data

    @pytest.mark.asyncio
    @patch("api.cost_management_api.get_enhanced_budget_manager")
    @patch("api.cost_management_api.get_current_user")
    async def test_budget_manager_error_handling(self, mock_get_user, mock_get_manager, mock_budget_manager):
        """Test error handling when budget manager fails."""
        # Setup mocks
        mock_user = User(
            id="user-123",
            email="test@example.com",
            name="Test User",
            role=UserRole.USER,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_get_user.return_value = mock_user
        mock_get_manager.return_value = mock_budget_manager

        # Make budget manager throw exception
        mock_budget_manager.get_real_time_usage = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        # Create request
        req = func.HttpRequest(
            method="GET",
            url="http://localhost:7071/api/cost-management/budget/usage",
            headers={"Content-Type": "application/json"},
            body=b""
        )

        # Call function
        response = await main(req)

        # Assertions
        assert response.status_code == 500
        response_data = json.loads(response.get_body().decode())
        assert "error" in response_data

    @pytest.mark.skip(reason="Optimization endpoint not implemented yet")
    @pytest.mark.asyncio
    @patch("api.cost_management_api.get_enhanced_budget_manager")
    @patch("api.cost_management_api.get_current_user")
    async def test_optimization_suggestions(self, mock_get_user, mock_get_manager, mock_budget_manager):
        """Test cost optimization suggestions endpoint."""
        # Setup mocks
        mock_user = User(
            id="user-123",
            email="test@example.com",
            name="Test User",
            role=UserRole.USER,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_get_user.return_value = mock_user
        mock_get_manager.return_value = mock_budget_manager

        mock_budget_manager.get_cost_optimization_suggestions = AsyncMock(return_value={
            "user_id": "user-123",
            "suggestions": [
                {
                    "type": "model_optimization",
                    "current_model": "gpt-4",
                    "suggested_model": "gpt-3.5-turbo",
                    "potential_savings": 15.50,
                    "impact": "medium"
                },
                {
                    "type": "usage_pattern",
                    "description": "Consider batching similar requests",
                    "potential_savings": 8.25,
                    "impact": "low"
                }
            ],
            "potential_savings": 23.75,
            "analysis_date": datetime.now(timezone.utc).isoformat()
        })

        # Create request
        req = func.HttpRequest(
            method="GET",
            url="http://localhost:7071/api/cost-management/optimization",
            headers={"Content-Type": "application/json"},
            body=b""
        )

        # Call function
        response = await main(req)

        # Assertions
        assert response.status_code == 200
        response_data = json.loads(response.get_body().decode())
        assert len(response_data["suggestions"]) == 2
        assert response_data["potential_savings"] == 23.75

    @pytest.mark.skip(reason="Anomaly detection endpoint not implemented yet")
    @pytest.mark.asyncio
    @patch("api.cost_management_api.get_enhanced_budget_manager")
    @patch("api.cost_management_api.get_current_user")
    async def test_anomaly_detection_endpoint(self, mock_get_user, mock_get_manager, mock_budget_manager):
        """Test anomaly detection endpoint."""
        # Setup mocks
        mock_user = User(
            id="user-123",
            email="test@example.com",
            name="Test User",
            role=UserRole.USER,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_get_user.return_value = mock_user
        mock_get_manager.return_value = mock_budget_manager

        mock_budget_manager.detect_cost_anomalies = AsyncMock(return_value={
            "user_id": "user-123",
            "anomalies": [
                {
                    "date": "2024-01-15",
                    "cost": 50.0,
                    "expected_cost": 5.0,
                    "deviation": 900.0,
                    "severity": "high",
                    "reason": "Unusual spike in API usage"
                }
            ],
            "analysis_period": 30,
            "detection_date": datetime.now(timezone.utc).isoformat()
        })

        # Create request
        req = func.HttpRequest(
            method="GET",
            url="http://localhost:7071/api/cost-management/anomalies?days=30",
            headers={"Content-Type": "application/json"},
            body=b""
        )

        # Call function
        response = await main(req)

        # Assertions
        assert response.status_code == 200
        response_data = json.loads(response.get_body().decode())
        assert len(response_data["anomalies"]) == 1
        assert response_data["anomalies"][0]["severity"] == "high"
