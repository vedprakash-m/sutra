"""
Unified Authentication Provider
Centralized authentication system for Sutra Multi-LLM Platform
Part of systematic resolution for authentication complexity
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from enum import Enum
import azure.functions as func

from .models import User, UserRole
from .auth_static_web_apps import StaticWebAppsAuthManager
from .auth_mocking import MockAuthManager
from .error_handling import SutraAPIError
from .error_handling import SutraAPIError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthEnvironment(Enum):
    """Authentication environments"""
    PRODUCTION = "production"
    DEVELOPMENT = "development"
    TESTING = "testing"

class AuthProvider(ABC):
    """Abstract base class for authentication providers"""

    @abstractmethod
    async def get_user_from_request(self, req: func.HttpRequest) -> Optional[User]:
        """Extract and validate user from request"""
        pass

    @abstractmethod
    async def validate_user_permissions(self, user: User, required_permissions: List[str]) -> bool:
        """Validate user has required permissions"""
        pass

    @abstractmethod
    async def refresh_user_session(self, user: User) -> Optional[User]:
        """Refresh user session if needed"""
        pass


# Adapter classes to bridge existing auth managers with the provider interface
class StaticWebAppsAuthProvider(AuthProvider):
    """Provider adapter for StaticWebAppsAuthManager"""

    def __init__(self):
        self.manager = StaticWebAppsAuthManager()

    async def get_user_from_request(self, req: func.HttpRequest) -> Optional[User]:
        return self.manager.get_user_from_headers(req)

    async def validate_user_permissions(self, user: User, required_permissions: List[str]) -> bool:
        # Basic permission validation - can be enhanced
        return user.role in [UserRole.ADMIN, UserRole.USER]

    async def refresh_user_session(self, user: User) -> Optional[User]:
        return user  # Static Web Apps handles session management


class MockAuthProvider(AuthProvider):
    """Provider adapter for MockAuthManager"""

    def __init__(self):
        self.manager = MockAuthManager()

    async def get_user_from_request(self, req: func.HttpRequest) -> Optional[User]:
        # Create a mock user for development/testing
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        return User(
            id=self.manager.user_id,
            email=self.manager.email,
            name=self.manager.name,
            role=self.manager.role,
            created_at=now,
            updated_at=now
        )

    async def validate_user_permissions(self, user: User, required_permissions: List[str]) -> bool:
        return True  # Mock allows all permissions

    async def refresh_user_session(self, user: User) -> Optional[User]:
        return user

class UnifiedAuthProvider:
    """
    Unified authentication provider that delegates to appropriate auth implementation
    based on environment and configuration
    """

    def __init__(self):
        self.environment = self._detect_environment()
        self.provider = self._create_provider()

        logger.info(f"Initialized UnifiedAuthProvider for {self.environment.value} environment")

    def _detect_environment(self) -> AuthEnvironment:
        """Detect the current environment"""
        # Check environment variables
        env = os.getenv('SUTRA_AUTH_ENV', '').lower()

        if env == 'production' or os.getenv('WEBSITE_SITE_NAME'):
            return AuthEnvironment.PRODUCTION
        elif env == 'testing' or os.getenv('PYTEST_CURRENT_TEST'):
            return AuthEnvironment.TESTING
        else:
            return AuthEnvironment.DEVELOPMENT

    def _create_provider(self) -> AuthProvider:
        """Create appropriate auth provider based on environment"""
        if self.environment == AuthEnvironment.PRODUCTION:
            return ProductionAuthProvider()
        elif self.environment == AuthEnvironment.TESTING:
            return TestingAuthProvider()
        else:
            return DevelopmentAuthProvider()

    async def get_user_from_request(self, req: func.HttpRequest) -> Optional[User]:
        """Get user from request using configured provider"""
        try:
            user = await self.provider.get_user_from_request(req)
            if user:
                logger.debug(f"Authenticated user: {user.email} ({user.role})")
            return user
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return None

    async def validate_user_permissions(self, user: User, required_permissions: List[str]) -> bool:
        """Validate user permissions"""
        return await self.provider.validate_user_permissions(user, required_permissions)

    async def require_authentication(self, req: func.HttpRequest) -> User:
        """Require authentication and return user or raise error"""
        user = await self.get_user_from_request(req)
        if not user:
            raise SutraError(
                error_type=ErrorType.AUTHENTICATION_ERROR,
                message="Authentication required",
                status_code=401
            )
        return user

    async def require_admin(self, req: func.HttpRequest) -> User:
        """Require admin role and return user or raise error"""
        user = await self.require_authentication(req)
        if user.role != UserRole.ADMIN:
            raise SutraError(
                error_type=ErrorType.AUTHORIZATION_ERROR,
                message="Admin role required",
                status_code=403
            )
        return user

    async def require_permissions(self, req: func.HttpRequest, permissions: List[str]) -> User:
        """Require specific permissions and return user or raise error"""
        user = await self.require_authentication(req)
        if not await self.validate_user_permissions(user, permissions):
            raise SutraError(
                error_type=ErrorType.AUTHORIZATION_ERROR,
                message=f"Required permissions: {', '.join(permissions)}",
                status_code=403
            )
        return user

class ProductionAuthProvider(AuthProvider):
    """Production authentication using Azure Static Web Apps"""

    def __init__(self):
        self.swa_provider = StaticWebAppsAuthProvider()

    async def get_user_from_request(self, req: func.HttpRequest) -> Optional[User]:
        """Get user from Azure Static Web Apps headers"""
        return self.swa_provider.get_user_from_headers(req)

    async def validate_user_permissions(self, user: User, required_permissions: List[str]) -> bool:
        """Validate permissions based on role and explicit permissions"""
        # Admin users have all permissions
        if user.role == UserRole.ADMIN:
            return True

        # Check explicit user permissions if available
        user_permissions = getattr(user, 'permissions', [])
        return all(perm in user_permissions for perm in required_permissions)

    async def refresh_user_session(self, user: User) -> Optional[User]:
        """Refresh session (not needed for Static Web Apps)"""
        return user

class DevelopmentAuthProvider(AuthProvider):
    """Development authentication with demo users and auto-injection"""

    def __init__(self):
        self.mock_provider = MockAuthProvider()

        # Demo users for development
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        self.demo_users = {
            'vedprakash.m@outlook.com': User(
                id='dev_admin_1',
                email='vedprakash.m@outlook.com',
                name='Ved Prakash (Admin)',
                role=UserRole.ADMIN,
                created_at=now,
                updated_at=now
            ),
            'demo.user@example.com': User(
                id='dev_user_1',
                email='demo.user@example.com',
                name='Demo User',
                role=UserRole.USER,
                created_at=now,
                updated_at=now
            ),
            'guest@example.com': User(
                id='dev_guest_1',
                email='guest@example.com',
                name='Guest User',
                role=UserRole.USER,  # Changed from GUEST as it doesn't exist in enum
                created_at=now,
                updated_at=now
            )
        }

    async def get_user_from_request(self, req: func.HttpRequest) -> Optional[User]:
        """Get user with demo user injection for development"""

        # First try to get user from headers (might be set by frontend)
        user_id_header = req.headers.get('x-ms-client-principal-id')
        user_email_header = req.headers.get('x-ms-client-principal-name')

        if user_email_header and user_email_header in self.demo_users:
            return self.demo_users[user_email_header]

        # Auto-inject admin user for specific demo endpoints
        path = req.url.lower()
        if any(path.endswith(endpoint) for endpoint in ['/admin', '/integrations', '/users']):
            return self.demo_users['vedprakash.m@outlook.com']

        # Default to demo user for other endpoints
        return self.demo_users['demo.user@example.com']

    async def validate_user_permissions(self, user: User, required_permissions: List[str]) -> bool:
        """Validate permissions with wildcard support"""
        user_permissions = getattr(user, 'permissions', [])

        # Check for wildcard permission
        if '*' in user_permissions:
            return True

        return all(perm in user_permissions for perm in required_permissions)

    async def refresh_user_session(self, user: User) -> Optional[User]:
        """Refresh session (always return user in development)"""
        return user

class TestingAuthProvider(AuthProvider):
    """Testing authentication with configurable mock users"""

    def __init__(self):
        self.mock_provider = MockAuthProvider()
        self._current_user: Optional[User] = None

    def set_test_user(self, user: Optional[User]):
        """Set current test user (for test setup)"""
        self._current_user = user

    async def get_user_from_request(self, req: func.HttpRequest) -> Optional[User]:
        """Return configured test user"""
        return self._current_user

    async def validate_user_permissions(self, user: User, required_permissions: List[str]) -> bool:
        """Always validate permissions for testing"""
        user_permissions = getattr(user, 'permissions', [])
        if '*' in user_permissions or user.role == UserRole.ADMIN:
            return True
        return all(perm in user_permissions for perm in required_permissions)

    async def refresh_user_session(self, user: User) -> Optional[User]:
        """Return user as-is for testing"""
        return user

# Singleton instance
_unified_auth_provider: Optional[UnifiedAuthProvider] = None

def get_auth_provider() -> UnifiedAuthProvider:
    """Get the singleton unified auth provider"""
    global _unified_auth_provider
    if _unified_auth_provider is None:
        _unified_auth_provider = UnifiedAuthProvider()
    return _unified_auth_provider

# Convenience functions for backward compatibility
async def get_user_from_request(req: func.HttpRequest) -> Optional[User]:
    """Get authenticated user from request"""
    return await get_auth_provider().get_user_from_request(req)

async def require_authentication(req: func.HttpRequest) -> User:
    """Require authentication"""
    return await get_auth_provider().require_authentication(req)

async def require_admin(req: func.HttpRequest) -> User:
    """Require admin role"""
    return await get_auth_provider().require_admin(req)

async def require_permissions(req: func.HttpRequest, permissions: List[str]) -> User:
    """Require specific permissions"""
    return await get_auth_provider().require_permissions(req, permissions)

# Authentication decorator
def auth_required(permissions: Optional[List[str]] = None, admin_only: bool = False):
    """
    Decorator for functions that require authentication

    Args:
        permissions: List of required permissions
        admin_only: Whether admin role is required

    Usage:
        @auth_required()
        async def my_function(req, user):
            pass
    """
    def decorator(func):
        async def wrapper(req: func.HttpRequest, *args, **kwargs):
            try:
                if admin_only:
                    user = await require_admin(req)
                elif permissions:
                    user = await require_permissions(req, permissions)
                else:
                    user = await require_authentication(req)

                # Add user to kwargs for the function
                kwargs['user'] = user
                return await func(req, *args, **kwargs)

            except SutraAPIError:
                raise
            except Exception as e:
                logger.error(f"Authentication decorator error: {str(e)}")
                raise SutraAPIError(f"Authentication failed: {str(e)}", 401)

        return wrapper
    return decorator

# Migration utilities for existing code
class LegacyAuthBridge:
    """Bridge to help migrate from old auth functions to unified auth"""

    @staticmethod
    async def get_user_from_headers(req: func.HttpRequest) -> Optional[User]:
        """Legacy function bridge"""
        return await get_user_from_request(req)

    @staticmethod
    def get_user_role(user_id: str) -> UserRole:
        """Legacy function bridge - simplified"""
        # This is a simplified bridge - in production you'd look up the user
        if user_id in ['dev_admin_1', 'admin_user']:
            return UserRole.ADMIN
        return UserRole.USER

# Export public interface
__all__ = [
    'UnifiedAuthProvider',
    'AuthProvider',
    'AuthEnvironment',
    'get_auth_provider',
    'get_user_from_request',
    'require_authentication',
    'require_admin',
    'require_permissions',
    'auth_required',
    'LegacyAuthBridge'
]
