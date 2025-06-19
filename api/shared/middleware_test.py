"""
Tests for the middleware module.
"""

import pytest
import json
import time
import os
from unittest.mock import Mock, patch, MagicMock
import azure.functions as func
from api.shared.middleware import (
    RateLimiter,
    get_client_ip,
    security_headers,
    rate_limit_middleware,
    validate_cors_origin,
    enhanced_security_middleware,
    create_health_response,
    rate_limiter,
)


class TestRateLimiter:
    """Test cases for the RateLimiter class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.rate_limiter = RateLimiter()

    def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization with default values."""
        limiter = RateLimiter()
        assert limiter.max_requests == 100  # Default value
        assert limiter.time_window == 60
        assert limiter.cleanup_interval == 300
        assert len(limiter.clients) == 0

    def test_rate_limiter_initialization_with_env(self):
        """Test RateLimiter initialization with environment variable."""
        with patch.dict(os.environ, {"SUTRA_MAX_REQUESTS_PER_MINUTE": "50"}):
            limiter = RateLimiter()
            assert limiter.max_requests == 50

    def test_is_allowed_new_client(self):
        """Test that new client is allowed."""
        is_allowed, rate_info = self.rate_limiter.is_allowed("192.168.1.1")

        assert is_allowed is True
        assert rate_info["limit"] == 100
        assert rate_info["remaining"] == 99
        assert "reset_time" in rate_info
        assert rate_info["retry_after"] is None

    def test_is_allowed_multiple_requests(self):
        """Test multiple requests from same client."""
        client_ip = "192.168.1.1"

        # First request
        is_allowed, rate_info = self.rate_limiter.is_allowed(client_ip)
        assert is_allowed is True
        assert rate_info["remaining"] == 99

        # Second request
        is_allowed, rate_info = self.rate_limiter.is_allowed(client_ip)
        assert is_allowed is True
        assert rate_info["remaining"] == 98

    def test_is_allowed_rate_limit_exceeded(self):
        """Test rate limit exceeded scenario."""
        client_ip = "192.168.1.1"

        # Simulate reaching rate limit
        for i in range(100):
            is_allowed, _ = self.rate_limiter.is_allowed(client_ip)
            assert is_allowed is True

        # Next request should be denied
        is_allowed, rate_info = self.rate_limiter.is_allowed(client_ip)
        assert is_allowed is False
        assert rate_info["remaining"] == 0
        assert rate_info["retry_after"] == 60

    def test_is_allowed_time_window_expiry(self):
        """Test that old requests are cleaned up after time window."""
        client_ip = "192.168.1.1"

        # Mock time to simulate old requests
        with patch("time.time") as mock_time:
            # Set initial time
            mock_time.return_value = 1000

            # Add some requests
            for i in range(5):
                self.rate_limiter.is_allowed(client_ip)

            # Advance time beyond window
            mock_time.return_value = 1070  # 70 seconds later

            # Check that old requests are cleaned up
            is_allowed, rate_info = self.rate_limiter.is_allowed(client_ip)
            assert is_allowed is True
            assert rate_info["remaining"] == 99  # Should be back to almost full

    def test_cleanup_old_entries(self):
        """Test cleanup of old entries."""
        with patch("time.time") as mock_time:
            mock_time.return_value = 1000

            # Add requests for multiple clients
            self.rate_limiter.is_allowed("192.168.1.1")
            self.rate_limiter.is_allowed("192.168.1.2")

            # Advance time to trigger cleanup
            mock_time.return_value = 1500  # 500 seconds later

            with patch("api.shared.middleware.logger") as mock_logger:
                # This should trigger cleanup
                self.rate_limiter._cleanup_old_entries(1500)

                # Verify cleanup was logged
                mock_logger.info.assert_called_once()
                assert "Rate limiter cleanup" in mock_logger.info.call_args[0][0]


class TestUtilityFunctions:
    """Test cases for utility functions."""

    def test_get_client_ip_x_forwarded_for(self):
        """Test getting client IP from X-Forwarded-For header."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}

        ip = get_client_ip(req)
        assert ip == "192.168.1.1"

    def test_get_client_ip_x_real_ip(self):
        """Test getting client IP from X-Real-IP header."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"X-Real-IP": "192.168.1.2"}

        ip = get_client_ip(req)
        assert ip == "192.168.1.2"

    def test_get_client_ip_cf_connecting_ip(self):
        """Test getting client IP from Cloudflare header."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"CF-Connecting-IP": "192.168.1.3"}

        ip = get_client_ip(req)
        assert ip == "192.168.1.3"

    def test_get_client_ip_azure_header(self):
        """Test getting client IP from Azure header."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"X-Azure-ClientIP": "192.168.1.4"}

        ip = get_client_ip(req)
        assert ip == "192.168.1.4"

    def test_get_client_ip_fallback(self):
        """Test fallback when no forwarded headers present."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {}

        ip = get_client_ip(req)
        assert ip == "unknown"

    def test_get_client_ip_fallback_with_client_ip(self):
        """Test fallback to X-Client-IP."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"X-Client-IP": "192.168.1.5"}

        ip = get_client_ip(req)
        assert ip == "192.168.1.5"

    def test_security_headers(self):
        """Test security headers generation."""
        headers = security_headers()

        expected_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "X-API-Version": "1.0.0",
            "X-Architecture": "no-gateway-direct",
        }

        assert headers == expected_headers


class TestCORSValidation:
    """Test cases for CORS validation."""

    def test_validate_cors_origin_allowed(self):
        """Test CORS validation with allowed origin."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"Origin": "https://sutra-web.azurestaticapps.net"}

        assert validate_cors_origin(req) is True

    def test_validate_cors_origin_localhost_dev(self):
        """Test CORS validation with localhost development origin."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"Origin": "https://localhost:5173"}

        assert validate_cors_origin(req) is True

    def test_validate_cors_origin_localhost_3000(self):
        """Test CORS validation with localhost:3000."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"Origin": "https://localhost:3000"}

        assert validate_cors_origin(req) is True

    def test_validate_cors_origin_custom_domain(self):
        """Test CORS validation with custom domain from environment."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"Origin": "https://custom.example.com"}

        with patch.dict(os.environ, {"SUTRA_CUSTOM_DOMAIN": "custom.example.com"}):
            assert validate_cors_origin(req) is True

    def test_validate_cors_origin_no_origin(self):
        """Test CORS validation with no Origin header."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {}

        assert validate_cors_origin(req) is True

    def test_validate_cors_origin_disallowed(self):
        """Test CORS validation with disallowed origin."""
        req = Mock(spec=func.HttpRequest)
        req.headers = {"Origin": "https://malicious.com"}

        assert validate_cors_origin(req) is False


class TestRateLimitMiddleware:
    """Test cases for rate limit middleware."""

    def test_rate_limit_middleware_success(self):
        """Test rate limit middleware with allowed request."""

        # Mock function to wrap
        @rate_limit_middleware
        def test_function(req):
            return func.HttpResponse("OK", status_code=200)

        # Mock request
        req = Mock(spec=func.HttpRequest)
        req.headers = {"X-Forwarded-For": "192.168.1.1"}
        req.method = "GET"
        req.url = "https://test.com/api/test"

        with patch("api.shared.middleware.logger") as mock_logger:
            response = test_function(req)

            assert response.status_code == 200
            assert response.get_body().decode() == "OK"

            # Verify logging
            mock_logger.info.assert_called_once()
            assert "Request from 192.168.1.1" in mock_logger.info.call_args[0][0]

    def test_rate_limit_middleware_rate_limited(self):
        """Test rate limit middleware when rate limit is exceeded."""
        # Create a rate limiter with low limit for testing
        with patch("api.shared.middleware.rate_limiter") as mock_limiter:
            mock_limiter.is_allowed.return_value = (
                False,
                {
                    "limit": 10,
                    "remaining": 0,
                    "reset_time": int(time.time() + 60),
                    "retry_after": 60,
                },
            )

            @rate_limit_middleware
            def test_function(req):
                return func.HttpResponse("OK", status_code=200)

            req = Mock(spec=func.HttpRequest)
            req.headers = {"X-Forwarded-For": "192.168.1.1"}

            with patch("api.shared.middleware.logger") as mock_logger:
                response = test_function(req)

                assert response.status_code == 429
                assert "Rate limit exceeded" in response.get_body().decode()

                # Verify warning logging
                mock_logger.warning.assert_called_once()
                assert (
                    "Rate limit exceeded for IP" in mock_logger.warning.call_args[0][0]
                )

    def test_rate_limit_middleware_exception(self):
        """Test rate limit middleware when an exception occurs."""

        @rate_limit_middleware
        def test_function(req):
            return func.HttpResponse("OK", status_code=200)

        req = Mock(spec=func.HttpRequest)
        req.headers = {}

        # Mock get_client_ip to raise an exception
        with patch(
            "api.shared.middleware.get_client_ip", side_effect=Exception("IP error")
        ), patch("api.shared.middleware.logger") as mock_logger:
            response = test_function(req)

            # Should still execute the function despite middleware error
            assert response.status_code == 200

            # Verify error logging
            mock_logger.error.assert_called_once()
            assert "Rate limiting middleware error" in mock_logger.error.call_args[0][0]


class TestEnhancedSecurityMiddleware:
    """Test cases for enhanced security middleware."""

    def test_enhanced_security_middleware_success(self):
        """Test enhanced security middleware with valid request."""

        @enhanced_security_middleware
        def test_function(req):
            return func.HttpResponse("OK", status_code=200)

        req = Mock(spec=func.HttpRequest)
        req.headers = {"Origin": "https://sutra-web.azurestaticapps.net"}

        with patch(
            "api.shared.middleware.rate_limit_middleware"
        ) as mock_rate_middleware:
            # Make rate_limit_middleware return the original function
            mock_rate_middleware.side_effect = lambda f: f

            response = test_function(req)
            assert response.status_code == 200

    def test_enhanced_security_middleware_cors_violation(self):
        """Test enhanced security middleware with CORS violation."""

        @enhanced_security_middleware
        def test_function(req):
            return func.HttpResponse("OK", status_code=200)

        req = Mock(spec=func.HttpRequest)
        req.headers = {"Origin": "https://malicious.com"}

        with patch("api.shared.middleware.logger") as mock_logger:
            response = test_function(req)

            assert response.status_code == 403
            response_data = json.loads(response.get_body().decode())
            assert response_data["error"] == "CORS policy violation"

            # Verify warning logging
            mock_logger.warning.assert_called_once()
            assert "CORS violation from origin" in mock_logger.warning.call_args[0][0]

    def test_enhanced_security_middleware_exception(self):
        """Test enhanced security middleware when CORS validation throws exception."""

        @enhanced_security_middleware
        def test_function(req):
            return func.HttpResponse("OK", status_code=200)

        req = Mock(spec=func.HttpRequest)
        req.headers = {}

        with patch(
            "api.shared.middleware.validate_cors_origin",
            side_effect=Exception("CORS error"),
        ), patch(
            "api.shared.middleware.rate_limit_middleware"
        ) as mock_rate_middleware, patch(
            "api.shared.middleware.logger"
        ) as mock_logger:
            # Make rate_limit_middleware return the original function
            mock_rate_middleware.side_effect = lambda f: f

            response = test_function(req)

            # Should fall back to basic rate limiting
            assert response.status_code == 200

            # Verify error logging
            mock_logger.error.assert_called_once()
            assert "Security middleware error" in mock_logger.error.call_args[0][0]


class TestCreateHealthResponse:
    """Test cases for create_health_response function."""

    def test_create_health_response_default(self):
        """Test health response creation with default environment."""
        with patch("api.shared.middleware.rate_limiter") as mock_limiter:
            mock_limiter.clients = {"192.168.1.1": []}
            mock_limiter.max_requests = 100

            response = create_health_response()

            assert response.status_code == 200
            assert response.mimetype == "application/json"

            # Parse response data
            response_data = json.loads(response.get_body().decode())
            assert response_data["status"] == "healthy"
            assert response_data["version"] == "1.0.0"
            assert response_data["architecture"] == "no-gateway-direct"
            assert response_data["environment"] == "development"
            assert "timestamp" in response_data
            assert "rate_limiter" in response_data

    def test_create_health_response_production_env(self):
        """Test health response with production environment."""
        with patch.dict(os.environ, {"SUTRA_ENVIRONMENT": "production"}), patch(
            "api.shared.middleware.rate_limiter"
        ) as mock_limiter:
            mock_limiter.clients = {}
            mock_limiter.max_requests = 100

            response = create_health_response()
            response_data = json.loads(response.get_body().decode())

            assert response_data["environment"] == "production"

    def test_create_health_response_rate_limiter_info(self):
        """Test health response includes rate limiter information."""
        with patch("api.shared.middleware.rate_limiter") as mock_limiter:
            # Simulate multiple active clients
            mock_limiter.clients = {
                "192.168.1.1": [time.time()],
                "192.168.1.2": [time.time()],
                "192.168.1.3": [time.time()],
            }
            mock_limiter.max_requests = 50

            response = create_health_response()
            response_data = json.loads(response.get_body().decode())

            assert response_data["rate_limiter"]["active_clients"] == 3
            assert response_data["rate_limiter"]["max_requests_per_minute"] == 50

    def test_create_health_response_headers(self):
        """Test health response includes security headers."""
        with patch("api.shared.middleware.rate_limiter") as mock_limiter:
            mock_limiter.clients = {}
            mock_limiter.max_requests = 100

            response = create_health_response()

            # Check that security headers are applied
            assert "X-Content-Type-Options" in response.headers
            assert "X-Frame-Options" in response.headers
            assert response.headers["X-API-Version"] == "1.0.0"
