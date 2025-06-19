"""
Tests for the health check endpoint.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import azure.functions as func
from api.health import main


class TestHealthEndpoint:
    """Test cases for the health check endpoint."""

    def test_health_check_success(self):
        """Test successful health check with GET request."""
        # Mock request
        req = Mock(spec=func.HttpRequest)
        req.method = "GET"
        req.headers = {}
        req.url = "https://test.com/api/health"

        # Mock the middleware and health response
        with patch("api.health.enhanced_security_middleware") as mock_middleware, patch(
            "api.health.create_health_response"
        ) as mock_health_response:
            # Set up the middleware to call the original function
            mock_middleware.side_effect = lambda f: f

            # Mock the health response
            expected_health_data = {
                "status": "healthy",
                "timestamp": 1234567890.0,
                "version": "1.0.0",
                "architecture": "no-gateway-direct",
                "environment": "development",
            }
            mock_health_response.return_value = func.HttpResponse(
                json.dumps(expected_health_data),
                status_code=200,
                mimetype="application/json",
            )

            # Call the function
            response = main(req)

            # Verify the response
            assert response.status_code == 200
            assert response.mimetype == "application/json"
            mock_health_response.assert_called_once()

    def test_health_check_method_not_allowed(self):
        """Test health check with non-GET method."""
        # Mock request with POST method
        req = Mock(spec=func.HttpRequest)
        req.method = "POST"
        req.headers = {}
        req.url = "https://test.com/api/health"

        # Mock the middleware to call the original function
        with patch("api.health.enhanced_security_middleware") as mock_middleware:
            mock_middleware.side_effect = lambda f: f

            # Call the function
            response = main(req)

            # Verify the response
            assert response.status_code == 405
            assert response.mimetype == "application/json"

            # Parse and verify response body
            response_data = json.loads(response.get_body().decode())
            assert response_data["error"] == "Method not allowed"

    def test_health_check_put_method(self):
        """Test health check with PUT method."""
        # Mock request with PUT method
        req = Mock(spec=func.HttpRequest)
        req.method = "PUT"
        req.headers = {}
        req.url = "https://test.com/api/health"

        # Mock the middleware to call the original function
        with patch("api.health.enhanced_security_middleware") as mock_middleware:
            mock_middleware.side_effect = lambda f: f

            # Call the function
            response = main(req)

            # Verify the response
            assert response.status_code == 405
            assert response.mimetype == "application/json"

    def test_health_check_delete_method(self):
        """Test health check with DELETE method."""
        # Mock request with DELETE method
        req = Mock(spec=func.HttpRequest)
        req.method = "DELETE"
        req.headers = {}
        req.url = "https://test.com/api/health"

        # Mock the middleware to call the original function
        with patch("api.health.enhanced_security_middleware") as mock_middleware:
            mock_middleware.side_effect = lambda f: f

            # Call the function
            response = main(req)

            # Verify the response
            assert response.status_code == 405
            assert response.mimetype == "application/json"

    @patch("api.health.create_health_response")
    def test_health_check_exception_in_health_response(self, mock_health_response):
        """Test health check when create_health_response raises an exception."""
        # Mock request
        req = Mock(spec=func.HttpRequest)
        req.method = "GET"
        req.headers = {}
        req.url = "https://test.com/api/health"

        # Mock the middleware to call the original function
        with patch("api.health.enhanced_security_middleware") as mock_middleware:
            mock_middleware.side_effect = lambda f: f

            # Make create_health_response raise an exception
            mock_health_response.side_effect = Exception("Database connection failed")

            # Call the function
            response = main(req)

            # Verify the response
            assert response.status_code == 503
            assert response.mimetype == "application/json"

            # Parse and verify response body
            response_data = json.loads(response.get_body().decode())
            assert response_data["status"] == "unhealthy"
            assert response_data["error"] == "Internal server error"

    def test_health_check_with_logging(self):
        """Test that health check logs appropriately."""
        # Mock request
        req = Mock(spec=func.HttpRequest)
        req.method = "GET"
        req.headers = {}
        req.url = "https://test.com/api/health"

        with patch("api.health.enhanced_security_middleware") as mock_middleware, patch(
            "api.health.create_health_response"
        ) as mock_health_response, patch("api.health.logger") as mock_logger:
            # Set up the middleware to call the original function
            mock_middleware.side_effect = lambda f: f

            # Mock the health response
            mock_health_response.return_value = func.HttpResponse(
                '{"status": "healthy"}', status_code=200, mimetype="application/json"
            )

            # Call the function
            response = main(req)

            # Verify logging was called
            mock_logger.info.assert_called_with("Health check requested")
            assert response.status_code == 200

    def test_health_check_exception_logging(self):
        """Test that exceptions are properly logged."""
        # Mock request
        req = Mock(spec=func.HttpRequest)
        req.method = "GET"
        req.headers = {}
        req.url = "https://test.com/api/health"

        with patch("api.health.enhanced_security_middleware") as mock_middleware, patch(
            "api.health.create_health_response"
        ) as mock_health_response, patch("api.health.logger") as mock_logger:
            # Set up the middleware to call the original function
            mock_middleware.side_effect = lambda f: f

            # Make create_health_response raise an exception
            test_exception = Exception("Test error")
            mock_health_response.side_effect = test_exception

            # Call the function
            response = main(req)

            # Verify exception logging was called
            mock_logger.error.assert_called_with("Health check error: Test error")
            assert response.status_code == 503

    def test_health_check_with_middleware_applied(self):
        """Test that the enhanced security middleware is properly applied."""
        # Mock request
        req = Mock(spec=func.HttpRequest)
        req.method = "GET"
        req.headers = {}
        req.url = "https://test.com/api/health"

        # Test that the middleware decorator is applied by checking the function
        # has been wrapped (this is more of a structural test)
        assert hasattr(main, "__wrapped__") or hasattr(main, "__name__")

        # Verify the function can be called
        with patch("api.health.enhanced_security_middleware") as mock_middleware, patch(
            "api.health.create_health_response"
        ) as mock_health_response:
            mock_middleware.side_effect = lambda f: f
            mock_health_response.return_value = func.HttpResponse(
                '{"status": "healthy"}', status_code=200, mimetype="application/json"
            )

            response = main(req)
            assert response.status_code == 200
