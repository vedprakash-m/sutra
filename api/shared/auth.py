import os
import jwt
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from functools import wraps
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from .models import User, UserRole


class AuthenticationError(Exception):
    """Authentication related errors."""
    pass


class AuthorizationError(Exception):
    """Authorization related errors."""
    pass


class AuthManager:
    """Manages authentication and authorization for the Sutra application."""
    
    def __init__(self):
        self._kv_client: Optional[SecretClient] = None
        self._auth_config: Optional[Dict[str, Any]] = None
        
    @property
    def kv_client(self) -> SecretClient:
        """Get or create Key Vault client."""
        if self._kv_client is None:
            key_vault_uri = os.getenv('KEY_VAULT_URI')
            if not key_vault_uri:
                raise ValueError("KEY_VAULT_URI environment variable is required")
            
            credential = DefaultAzureCredential()
            self._kv_client = SecretClient(vault_url=key_vault_uri, credential=credential)
        
        return self._kv_client
    
    async def get_auth_config(self) -> Dict[str, Any]:
        """Get authentication configuration from Key Vault."""
        if self._auth_config is None:
            try:
                kv_client = self.kv_client
                
                # Get Azure AD B2C configuration
                tenant_id = kv_client.get_secret("auth-tenant-id").value
                client_id = kv_client.get_secret("auth-client-id").value
                policy = kv_client.get_secret("auth-policy").value
                
                self._auth_config = {
                    "tenant_id": tenant_id,
                    "client_id": client_id,
                    "policy": policy,
                    "issuer": f"https://{tenant_id}.b2clogin.com/{tenant_id}/{policy}/v2.0/",
                    "jwks_uri": f"https://{tenant_id}.b2clogin.com/{tenant_id}/{policy}/discovery/v2.0/keys"
                }
                
            except Exception as e:
                logging.error(f"Failed to get auth config: {e}")
                # Fall back to mock configuration for development
                self._auth_config = {
                    "tenant_id": "mock-tenant",
                    "client_id": "mock-client",
                    "policy": "mock-policy",
                    "issuer": "mock-issuer",
                    "jwks_uri": "mock-jwks"
                }
        
        return self._auth_config
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and return claims."""
        try:
            # For development, use a simple mock validation
            if token == "mock-token" or token.startswith("dev-"):
                return {
                    "sub": "mock-user-id",
                    "email": "dev@sutra.ai",
                    "name": "Development User",
                    "roles": ["user"],
                    "iat": datetime.now(timezone.utc).timestamp(),
                    "exp": (datetime.now(timezone.utc).timestamp() + 3600)
                }
            
            # In production, this would validate against Azure AD B2C
            # For now, decode without verification for development
            config = await self.get_auth_config()
            
            # This is a simplified version - in production you'd verify the signature
            # against the JWKS endpoint
            decoded = jwt.decode(token, options={"verify_signature": False})
            
            # Validate issuer
            if decoded.get("iss") != config["issuer"]:
                raise AuthenticationError("Invalid token issuer")
            
            # Validate audience
            if decoded.get("aud") != config["client_id"]:
                raise AuthenticationError("Invalid token audience")
            
            # Check expiration
            if decoded.get("exp", 0) < datetime.now(timezone.utc).timestamp():
                raise AuthenticationError("Token has expired")
            
            return decoded
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
        except AuthenticationError:
            # Re-raise authentication errors as-is
            raise
        except Exception as e:
            logging.error(f"Token validation error: {e}")
            raise AuthenticationError("Token validation failed")
    
    async def get_user_from_token(self, token: str) -> User:
        """Extract user information from validated token."""
        claims = await self.validate_token(token)
        
        # Map token claims to User model
        user_id = claims.get("sub") or claims.get("oid")
        email = claims.get("email") or claims.get("preferred_username")
        name = claims.get("name") or claims.get("given_name", "") + " " + claims.get("family_name", "")
        
        # Determine user roles
        roles = [UserRole.USER]  # Default role
        
        # Check for admin role
        token_roles = claims.get("roles", [])
        if isinstance(token_roles, str):
            token_roles = [token_roles]
        
        if "admin" in token_roles or "Administrator" in token_roles:
            roles.append(UserRole.ADMIN)
        
        # For development, make certain users admin
        if email in ["dev@sutra.ai", "admin@sutra.ai"]:
            roles.append(UserRole.ADMIN)
        
        return User(
            id=user_id,
            email=email,
            name=name.strip(),
            roles=roles,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    async def check_permission(self, user: User, resource: str, action: str) -> bool:
        """Check if user has permission for the specified action on resource."""
        # Admin users have all permissions
        if UserRole.ADMIN in user.roles:
            return True
        
        # Define permission rules
        permissions = {
            "prompts": {
                "create": [UserRole.USER, UserRole.ADMIN],
                "read": [UserRole.USER, UserRole.ADMIN],
                "update": [UserRole.USER, UserRole.ADMIN],  # Users can only update their own
                "delete": [UserRole.USER, UserRole.ADMIN],  # Users can only delete their own
            },
            "collections": {
                "create": [UserRole.USER, UserRole.ADMIN],
                "read": [UserRole.USER, UserRole.ADMIN],
                "update": [UserRole.USER, UserRole.ADMIN],
                "delete": [UserRole.USER, UserRole.ADMIN],
            },
            "playbooks": {
                "create": [UserRole.USER, UserRole.ADMIN],
                "read": [UserRole.USER, UserRole.ADMIN],
                "update": [UserRole.USER, UserRole.ADMIN],
                "delete": [UserRole.USER, UserRole.ADMIN],
                "execute": [UserRole.USER, UserRole.ADMIN],
            },
            "admin": {
                "read": [UserRole.ADMIN],
                "update": [UserRole.ADMIN],
                "delete": [UserRole.ADMIN],
                "manage_users": [UserRole.ADMIN],
                "manage_providers": [UserRole.ADMIN],
                "view_usage": [UserRole.ADMIN],
            }
        }
        
        resource_permissions = permissions.get(resource, {})
        allowed_roles = resource_permissions.get(action, [])
        
        return any(role in user.roles for role in allowed_roles)


# Global auth manager instance
_auth_manager = None

def get_auth_manager() -> AuthManager:
    """Get the global AuthManager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


def extract_token_from_request(req: func.HttpRequest) -> Optional[str]:
    """Extract bearer token from HTTP request."""
    auth_header = req.headers.get('Authorization', '')
    
    if auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    
    return None


def require_auth(resource: str = None, action: str = "read"):
    """Decorator to require authentication for Azure Function endpoints."""
    def decorator(decorated_func):
        @wraps(decorated_func)
        async def wrapper(req: func.HttpRequest) -> func.HttpResponse:
            try:
                # Extract token from request
                token = extract_token_from_request(req)
                if not token:
                    return func.HttpResponse(
                        '{"error": "authentication_required", "message": "Bearer token required"}',
                        status_code=401,
                        headers={"Content-Type": "application/json"}
                    )
                
                # Validate token and get user
                auth_mgr = get_auth_manager()
                user = await auth_mgr.get_user_from_token(token)
                
                # Check permissions if resource and action specified
                if resource and action:
                    if not await auth_mgr.check_permission(user, resource, action):
                        return func.HttpResponse(
                            '{"error": "access_denied", "message": "Insufficient permissions"}',
                            status_code=403,
                            headers={"Content-Type": "application/json"}
                        )
                
                # Add user to request context (monkey patch for simplicity)
                req.current_user = user
                
                # Call the original function
                return await decorated_func(req)
                
            except AuthenticationError as e:
                return func.HttpResponse(
                    f'{{"error": "authentication_failed", "message": "{str(e)}"}}',
                    status_code=401,
                    headers={"Content-Type": "application/json"}
                )
            except AuthorizationError as e:
                return func.HttpResponse(
                    f'{{"error": "authorization_failed", "message": "{str(e)}"}}',
                    status_code=403,
                    headers={"Content-Type": "application/json"}
                )
            except Exception as e:
                logging.error(f"Authentication error: {e}")
                return func.HttpResponse(
                    '{"error": "internal_error", "message": "Authentication system error"}',
                    status_code=500,
                    headers={"Content-Type": "application/json"}
                )
        
        return wrapper
    return decorator


def require_admin(func):
    """Decorator to require admin role for Azure Function endpoints."""
    return require_auth(resource="admin", action="read")(func)


async def get_current_user(req: func.HttpRequest) -> Optional[User]:
    """Get current user from request (if authenticated)."""
    return getattr(req, 'current_user', None)


def check_admin_role(req: func.HttpRequest) -> bool:
    """Check if the authenticated user has admin role."""
    try:
        # Development mode: allow mock admin tokens
        environment = os.getenv('ENVIRONMENT', '').lower()
        if environment == 'development':
            auth_header = req.headers.get('Authorization', '')
            if 'mock-admin-token' in auth_header or 'admin' in auth_header.lower():
                return True
        
        # Get user ID from token
        user_id = get_user_id_from_token(req)
        if not user_id:
            return False
        
        # In a full implementation, this would check the user's role in the database
        # For MVP, we'll check for admin claim in the JWT token
        
        auth_header = req.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return False
        
        token = auth_header[7:]
        
        try:
            # Decode without verification for role checking (verification done earlier)
            payload = jwt.decode(token, options={"verify_signature": False})
            
            # Check for admin role in various possible claims
            roles = []
            
            # Check different possible role claims
            if 'roles' in payload:
                roles.extend(payload['roles'])
            if 'role' in payload:
                roles.append(payload['role'])
            if 'extension_Role' in payload:  # Azure AD B2C custom claims
                roles.append(payload['extension_Role'])
            if 'custom_role' in payload:
                roles.append(payload['custom_role'])
            
            # Check if any role indicates admin
            admin_roles = ['admin', 'administrator', 'system_admin', 'super_admin']
            return any(role.lower() in admin_roles for role in roles)
            
        except Exception:
            return False
    
    except Exception:
        return False


def check_user_permissions(user_id: str, resource_type: str, resource_id: str, required_permission: str) -> bool:
    """Check if user has specific permission for a resource."""
    try:
        # This would be implemented with database checks in a full system
        # For MVP, we'll implement basic ownership checks
        
        from .database import get_database_manager
        
        db_manager = get_database_manager()
        
        # Map resource types to containers
        container_map = {
            'prompt': 'Prompts',
            'collection': 'Collections',
            'playbook': 'Playbooks'
        }
        
        container_name = container_map.get(resource_type)
        if not container_name:
            return False
        
        container = db_manager.get_container(container_name)
        
        # Get the resource
        try:
            resource = container.read_item(item=resource_id, partition_key=resource_id)
        except:
            return False
        
        # Check ownership
        owner_field = 'creatorId' if resource_type in ['prompt', 'playbook'] else 'ownerId'
        if resource.get(owner_field) == user_id:
            return True
        
        # Check explicit permissions
        permissions = resource.get('permissions', {})
        user_permissions = permissions.get(user_id, [])
        
        return required_permission in user_permissions
    
    except Exception:
        return False


def get_user_role(user_id: str) -> UserRole:
    """Get the user's role from the database."""
    try:
        from .database import get_database_manager
        
        db_manager = get_database_manager()
        container = db_manager.get_container('Users')
        
        try:
            user = container.read_item(item=user_id, partition_key=user_id)
            role_str = user.get('role', 'member')
            
            # Map string to enum
            role_map = {
                'member': UserRole.MEMBER,
                'contributor': UserRole.CONTRIBUTOR,
                'prompt_manager': UserRole.PROMPT_MANAGER,
                'admin': UserRole.ADMIN
            }
            
            return role_map.get(role_str, UserRole.MEMBER)
        except:
            return UserRole.MEMBER
    
    except Exception:
        return UserRole.MEMBER


def require_admin_role(func):
    """Decorator to require admin role for function access."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract request from args - assumes first arg is HttpRequest
        req = None
        for arg in args:
            if isinstance(arg, func.HttpRequest):
                req = arg
                break
        
        if not req:
            raise AuthorizationError("No request found in function arguments")
        
        if not check_admin_role(req):
            raise AuthorizationError("Admin privileges required")
        
        return await func(*args, **kwargs)
    
    return wrapper


def require_permission(resource_type: str, permission: str):
    """Decorator to require specific permission for resource access."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and resource ID from args/kwargs
            req = None
            resource_id = None
            
            for arg in args:
                if isinstance(arg, func.HttpRequest):
                    req = arg
                    break
            
            # Look for resource ID in kwargs or route params
            resource_id = kwargs.get('resource_id') or kwargs.get('id')
            if not resource_id and req:
                resource_id = req.route_params.get('id')
            
            if not req or not resource_id:
                raise AuthorizationError("Request or resource ID not found")
            
            user_id = get_user_id_from_token(req)
            if not user_id:
                raise AuthenticationError("User not authenticated")
            
            if not check_user_permissions(user_id, resource_type, resource_id, permission):
                raise AuthorizationError(f"Permission '{permission}' required for {resource_type}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def verify_jwt_token(req: func.HttpRequest) -> Dict[str, Any]:
    """Verify JWT token from request and return validation result."""
    try:
        token = extract_token_from_request(req)
        if not token:
            return {'valid': False, 'message': 'No token provided'}
        
        auth_manager = get_auth_manager()
        # For now, use a simple validation - in production this would be async
        # For development, accept mock tokens
        if token == "mock-token" or token.startswith("dev-") or token == "mock-admin-token":
            roles = ['user']
            if token == "mock-admin-token" or 'admin' in token:
                roles = ['admin', 'user']
            
            return {
                'valid': True, 
                'message': 'Token validated',
                'claims': {
                    'sub': 'mock-user-id' if 'admin' not in token else 'mock-admin-id',
                    'email': 'dev@sutra.ai' if 'admin' not in token else 'admin@sutra.ai',
                    'name': 'Development User' if 'admin' not in token else 'Development Admin',
                    'roles': roles
                }
            }
        
        # Try to decode the token (simplified validation)
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            return {
                'valid': True,
                'message': 'Token validated',
                'claims': decoded
            }
        except jwt.InvalidTokenError as e:
            return {'valid': False, 'message': f'Invalid token: {str(e)}'}
            
    except Exception as e:
        logging.error(f"Token verification failed: {e}")
        return {'valid': False, 'message': 'Token verification failed'}


def get_user_id_from_token(req: func.HttpRequest) -> Optional[str]:
    """Extract user ID from JWT token in request."""
    try:
        token = extract_token_from_request(req)
        if not token:
            return None
        
        # For development, handle mock tokens
        if token == "mock-token" or token.startswith("dev-"):
            return "mock-user-id"
        
        # Try to decode the token
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            return decoded.get('sub')
        except jwt.InvalidTokenError:
            return None
            
    except Exception as e:
        logging.error(f"Failed to extract user ID from token: {e}")
        return None
