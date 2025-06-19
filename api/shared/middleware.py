"""
Rate limiting and security middleware for Sutra API (No-Gateway Architecture)
Provides basic protection against abuse for small team deployment
"""

import os
import time
import logging
from typing import Dict, Optional, Tuple, Any
from functools import wraps
from collections import defaultdict, deque
import azure.functions as func
import json


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter for small team deployment."""
    
    def __init__(self):
        # Store request timestamps by client IP
        self.clients: Dict[str, deque] = defaultdict(lambda: deque())
        # Configuration from environment variables
        self.max_requests = int(os.getenv('SUTRA_MAX_REQUESTS_PER_MINUTE', '100'))
        self.time_window = 60  # 1 minute window
        self.cleanup_interval = 300  # Clean up old entries every 5 minutes
        self.last_cleanup = time.time()
    
    def is_allowed(self, client_ip: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed for the client IP.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        current_time = time.time()
        
        # Cleanup old entries periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries(current_time)
        
        # Get client's request history
        client_requests = self.clients[client_ip]
        
        # Remove requests outside the time window
        while client_requests and current_time - client_requests[0] > self.time_window:
            client_requests.popleft()
        
        # Check if client has exceeded rate limit
        current_count = len(client_requests)
        is_allowed = current_count < self.max_requests
        
        if is_allowed:
            # Add current request timestamp
            client_requests.append(current_time)
        
        # Prepare rate limit info
        rate_limit_info = {
            'limit': self.max_requests,
            'remaining': max(0, self.max_requests - current_count - (1 if is_allowed else 0)),
            'reset_time': int(current_time + self.time_window),
            'retry_after': self.time_window if not is_allowed else None
        }
        
        return is_allowed, rate_limit_info
    
    def _cleanup_old_entries(self, current_time: float):
        """Remove old client entries to prevent memory growth."""
        clients_to_remove = []
        
        for client_ip, requests in self.clients.items():
            # Remove old requests
            while requests and current_time - requests[0] > self.time_window * 2:
                requests.popleft()
            
            # Mark empty clients for removal
            if not requests:
                clients_to_remove.append(client_ip)
        
        # Remove empty client entries
        for client_ip in clients_to_remove:
            del self.clients[client_ip]
        
        self.last_cleanup = current_time
        logger.info(f"Rate limiter cleanup: removed {len(clients_to_remove)} inactive clients")


# Global rate limiter instance
rate_limiter = RateLimiter()


def get_client_ip(req: func.HttpRequest) -> str:
    """Extract client IP from request headers."""
    # Check for forwarded IP headers (Static Web App, CDN, proxy)
    forwarded_headers = [
        'X-Forwarded-For',
        'X-Real-IP',
        'X-Client-IP',
        'CF-Connecting-IP',  # Cloudflare
        'X-Azure-ClientIP'   # Azure
    ]
    
    for header in forwarded_headers:
        ip = req.headers.get(header)
        if ip:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return ip.split(',')[0].strip()
    
    # Fallback to default (may not be accurate in Azure Functions)
    return req.headers.get('X-Client-IP', 'unknown')


def security_headers() -> Dict[str, str]:
    """Get security headers for responses."""
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'X-API-Version': '1.0.0',
        'X-Architecture': 'no-gateway-direct'
    }


def rate_limit_middleware(f):
    """
    Decorator to apply rate limiting to Azure Function endpoints.
    
    Usage:
        @rate_limit_middleware
        def main(req: func.HttpRequest) -> func.HttpResponse:
            # Your function logic here
    """
    @wraps(f)
    def wrapper(req: func.HttpRequest) -> func.HttpResponse:
        try:
            # Get client IP
            client_ip = get_client_ip(req)
            
            # Check rate limit
            is_allowed, rate_info = rate_limiter.is_allowed(client_ip)
            
            # Prepare response headers
            headers = security_headers()
            headers.update({
                'X-RateLimit-Limit': str(rate_info['limit']),
                'X-RateLimit-Remaining': str(rate_info['remaining']),
                'X-RateLimit-Reset': str(rate_info['reset_time'])
            })
            
            if not is_allowed:
                # Rate limit exceeded
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                
                headers['Retry-After'] = str(rate_info['retry_after'])
                
                error_response = {
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Limit: {rate_info["limit"]} requests per minute.',
                    'retry_after': rate_info['retry_after'],
                    'timestamp': time.time()
                }
                
                return func.HttpResponse(
                    json.dumps(error_response),
                    status_code=429,
                    headers=headers,
                    mimetype='application/json'
                )
            
            # Rate limit check passed, execute the function
            response = f(req)
            
            # Add security and rate limit headers to successful responses
            if hasattr(response, 'headers'):
                for key, value in headers.items():
                    response.headers[key] = value
            
            # Log successful request
            logger.info(f"Request from {client_ip}: {req.method} {req.url}")
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting middleware error: {str(e)}")
            # In case of middleware error, allow the request but log the issue
            return f(req)
    
    return wrapper


def validate_cors_origin(req: func.HttpRequest) -> bool:
    """
    Validate CORS origin for additional security.
    
    Args:
        req: HTTP request object
        
    Returns:
        True if origin is allowed, False otherwise
    """
    origin = req.headers.get('Origin', '')
    
    # Allowed origins (should match Static Web App CORS configuration)
    allowed_origins = [
        'https://sutra-web.azurestaticapps.net',
        'https://localhost:5173',  # Development
        'https://localhost:3000',  # Development alternative
    ]
    
    # Add custom domain if configured
    custom_domain = os.getenv('SUTRA_CUSTOM_DOMAIN')
    if custom_domain:
        allowed_origins.append(f'https://{custom_domain}')
    
    # Allow requests without Origin header (e.g., direct API calls)
    if not origin:
        return True
    
    return origin in allowed_origins


def enhanced_security_middleware(f):
    """
    Enhanced security middleware that combines rate limiting with additional checks.
    
    Usage:
        @enhanced_security_middleware
        def main(req: func.HttpRequest) -> func.HttpResponse:
            # Your function logic here
    """
    @wraps(f)
    def wrapper(req: func.HttpRequest) -> func.HttpResponse:
        try:
            # CORS validation
            if not validate_cors_origin(req):
                logger.warning(f"CORS violation from origin: {req.headers.get('Origin')}")
                return func.HttpResponse(
                    json.dumps({'error': 'CORS policy violation'}),
                    status_code=403,
                    headers=security_headers(),
                    mimetype='application/json'
                )
            
            # Apply rate limiting
            return rate_limit_middleware(f)(req)
            
        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            # In case of middleware error, apply basic rate limiting
            return rate_limit_middleware(f)(req)
    
    return wrapper


# Health check function with monitoring
def create_health_response() -> func.HttpResponse:
    """Create a standardized health check response."""
    health_data = {
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0',
        'architecture': 'no-gateway-direct',
        'environment': os.getenv('SUTRA_ENVIRONMENT', 'development'),
        'rate_limiter': {
            'active_clients': len(rate_limiter.clients),
            'max_requests_per_minute': rate_limiter.max_requests
        }
    }
    
    return func.HttpResponse(
        json.dumps(health_data),
        status_code=200,
        headers=security_headers(),
        mimetype='application/json'
    )
