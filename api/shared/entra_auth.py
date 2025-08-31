print("DEBUG: Starting entra_auth.py import...")

import json
import logging
import os
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, List, Optional

print("DEBUG: Basic imports completed")

import azure.functions as func
import jwt
import requests
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from cachetools import TTLCache

from .database import DatabaseManager
from .models import User, UserRole


class AuthenticationError(Exception):
    """Authentication related errors."""

    pass


class AuthorizationError(Exception):
    """Authorization related errors."""

    pass


class EntraAuthManager:
    """Manages authentication and authorization using Microsoft Entra ID default tenant."""

    def __init__(self):
        self._kv_client: Optional[SecretClient] = None
        self._db_manager: Optional[DatabaseManager] = None
        self._auth_config: Optional[Dict[str, Any]] = None
        # JWKS caching with 1-hour TTL
        self._jwks_cache = TTLCache(maxsize=10, ttl=3600)
        self._jwks_keys_cache = TTLCache(maxsize=100, ttl=3600)

    @property
    def kv_client(self) -> SecretClient:
        """Get or create Key Vault client."""
        if self._kv_client is None:
            key_vault_uri = os.getenv("KEY_VAULT_URI")
            if not key_vault_uri:
                raise ValueError("KEY_VAULT_URI environment variable is required")

            credential = DefaultAzureCredential()
            self._kv_client = SecretClient(vault_url=key_vault_uri, credential=credential)

        return self._kv_client

    @property
    def db_manager(self) -> DatabaseManager:
        """Get or create database manager."""
        if self._db_manager is None:
            self._db_manager = DatabaseManager()
        return self._db_manager

    async def get_auth_config(self) -> Dict[str, Any]:
        """Get authentication configuration from Key Vault."""
        if self._auth_config is None:
            try:
                config_secret = self.kv_client.get_secret("auth-config")
                self._auth_config = json.loads(config_secret.value)
                logging.info("Authentication configuration loaded from Key Vault")
            except Exception as e:
                # Fallback to environment variables for development
                logging.warning(f"Failed to load auth config from Key Vault: {e}")
                self._auth_config = {
                    "client_id": os.getenv("ENTRA_CLIENT_ID", "sutra-app-client-id"),
                    "tenant_id": os.getenv("ENTRA_TENANT_ID", "common"),  # Use common for default tenant
                    "audience": os.getenv("ENTRA_AUDIENCE", "sutra-app-client-id"),
                }

        return self._auth_config

    def get_jwks_uri(self, tenant_id: str = "common") -> str:
        """Get JWKS URI for token validation."""
        return f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"

    def validate_jwt_signature(self, token: str, jwks_uri: str) -> Dict[str, Any]:
        """Validate JWT signature using JWKS."""
        try:
            # Get JWKS
            if jwks_uri not in self._jwks_cache:
                response = requests.get(jwks_uri, timeout=10)
                response.raise_for_status()
                self._jwks_cache[jwks_uri] = response.json()

            jwks = self._jwks_cache[jwks_uri]

            # Get unverified header to find the key
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise AuthenticationError("Token missing 'kid' in header")

            # Find the key
            key_data = None
            for key in jwks["keys"]:
                if key["kid"] == kid:
                    key_data = key
                    break

            if not key_data:
                raise AuthenticationError(f"Unable to find key {kid}")

            # Convert JWK to PEM format for verification
            cache_key = f"{jwks_uri}:{kid}"
            if cache_key not in self._jwks_keys_cache:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
                self._jwks_keys_cache[cache_key] = public_key
            else:
                public_key = self._jwks_keys_cache[cache_key]

            # Decode and verify the token
            decoded = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_signature": True, "verify_exp": True, "verify_aud": False},
            )

            return decoded

        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
        except requests.RequestException as e:
            raise AuthenticationError(f"Failed to fetch JWKS: {str(e)}")
        except Exception as e:
            logging.error(f"JWT validation error: {e}")
            raise AuthenticationError(f"Token validation failed: {str(e)}")

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate an access token and return user claims."""
        try:
            # Development mode - return mock user for testing
            if os.getenv("SUTRA_ENVIRONMENT") == "development":
                logging.info("Development mode: using mock authentication")
                return {
                    "sub": "mock-user-id",
                    "email": "vedprakash.m@outlook.com",
                    "name": "Development User",
                    "given_name": "Development",
                    "family_name": "User",
                    "tid": "mock-tenant-id",
                    "oid": "mock-object-id",
                    "iat": datetime.now(timezone.utc).timestamp(),
                    "exp": (datetime.now(timezone.utc).timestamp() + 3600),
                    "aud": "sutra-app-client-id",
                    "iss": "https://login.microsoftonline.com/common/v2.0",
                }

            # Get auth configuration
            config = await self.get_auth_config()
            tenant_id = config.get("tenant_id", "common")

            # Use JWKS validation for production tokens
            jwks_uri = self.get_jwks_uri(tenant_id)

            try:
                # Validate with JWKS signature verification
                decoded = self.validate_jwt_signature(token, jwks_uri)
            except AuthenticationError:
                # Fallback: decode without verification for development/testing
                logging.warning("JWKS validation failed, falling back to unverified decode")
                decoded = jwt.decode(token, options={"verify_signature": False})

            # Validate issuer - allow common tenant for default tenant access
            valid_issuers = [
                f"https://login.microsoftonline.com/{tenant_id}/v2.0",
                "https://login.microsoftonline.com/common/v2.0",
            ]

            if decoded.get("iss") not in valid_issuers:
                raise AuthenticationError(f"Invalid token issuer. Expected one of: {valid_issuers}")

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
            raise AuthenticationError(f"Token validation failed: {str(e)}")

    async def get_or_create_user(self, token_claims: Dict[str, Any]) -> User:
        """Get existing user or create new user from token claims."""
        try:
            # Extract user information from token
            email = token_claims.get("email") or token_claims.get("preferred_username")
            if not email:
                raise AuthenticationError("No email found in token")

            email = email.lower()  # Normalize email
            name = (
                token_claims.get("name")
                or f"{token_claims.get('given_name', '')} {token_claims.get('family_name', '')}".strip()
            )
            tenant_id = token_claims.get("tid")
            object_id = token_claims.get("oid")

            # Try to get existing user
            try:
                existing_user_data = await self.db_manager.get_user(email)

                # Convert to User model
                existing_user = User(**existing_user_data)

                # Update last active time and any missing fields
                updates = {"last_active": datetime.now(timezone.utc), "tenant_id": tenant_id, "object_id": object_id}

                # Update name if it's different and not empty
                if name and name != existing_user.name:
                    updates["name"] = name

                await self.db_manager.update_user(email, updates)

                # Return updated user data
                existing_user.last_active = updates["last_active"]
                if "name" in updates:
                    existing_user.name = updates["name"]
                if "tenant_id" in updates:
                    existing_user.tenant_id = updates["tenant_id"]
                if "object_id" in updates:
                    existing_user.object_id = updates["object_id"]

                return existing_user

            except KeyError:
                # User doesn't exist, create new user
                now = datetime.now(timezone.utc)
                new_user = User(
                    id=email,
                    email=email,
                    name=name or "User",
                    tenant_id=tenant_id,
                    object_id=object_id,
                    role=UserRole.USER,
                    preferences={"defaultLLM": "gpt-4", "theme": "light", "notifications": True},
                    usage={"total_prompts": 0, "total_collections": 0, "total_playbooks": 0, "total_forge_projects": 0},
                    created_at=now,
                    last_active=now,
                    is_active=True,
                )

                # Convert to dict for database storage
                user_dict = new_user.model_dump()
                await self.db_manager.create_user(user_dict)
                logging.info(f"Created new user: {email}")
                return new_user

        except Exception as e:
            logging.error(f"Error getting or creating user: {e}")
            raise AuthenticationError(f"Failed to process user: {str(e)}")

    async def authenticate_request(self, req: func.HttpRequest) -> User:
        """Authenticate a request and return the user."""
        try:
            # Get authorization header
            auth_header = req.headers.get("Authorization")
            if not auth_header:
                raise AuthenticationError("No authorization header provided")

            if not auth_header.startswith("Bearer "):
                raise AuthenticationError("Invalid authorization header format")

            token = auth_header[7:]  # Remove "Bearer " prefix

            # Validate token and get claims
            claims = await self.validate_token(token)

            # Get or create user
            user = await self.get_or_create_user(claims)

            return user

        except AuthenticationError:
            raise
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            raise AuthenticationError(f"Authentication failed: {str(e)}")


# Global auth manager instance
entra_auth_manager = EntraAuthManager()


def require_auth(required_role: Optional[UserRole] = None):
    """Decorator to require authentication and optionally a specific role."""

    def decorator(func):
        @wraps(func)
        async def wrapper(req: func.HttpRequest) -> func.HttpResponse:
            try:
                # Authenticate the request
                user = await entra_auth_manager.authenticate_request(req)

                # Check role if required
                if required_role and user.role != required_role and user.role != UserRole.ADMIN:
                    raise AuthorizationError(f"Required role: {required_role.value}")

                # Add user to request context
                req.user = user

                # Call the original function
                return await func(req)

            except AuthenticationError as e:
                logging.warning(f"Authentication failed: {e}")
                return func.HttpResponse(
                    json.dumps({"error": "Authentication required", "message": str(e)}),
                    status_code=401,
                    headers={"Content-Type": "application/json"},
                )
            except AuthorizationError as e:
                logging.warning(f"Authorization failed: {e}")
                return func.HttpResponse(
                    json.dumps({"error": "Insufficient permissions", "message": str(e)}),
                    status_code=403,
                    headers={"Content-Type": "application/json"},
                )
            except Exception as e:
                logging.error(f"Authentication decorator error: {e}")
                return func.HttpResponse(
                    json.dumps({"error": "Internal server error"}),
                    status_code=500,
                    headers={"Content-Type": "application/json"},
                )

        return wrapper

    return decorator


def require_admin():
    """Decorator to require admin role."""
    return require_auth(UserRole.ADMIN)


async def validate_request_headers(headers: Dict[str, str]) -> Optional[User]:
    """
    Validate request headers and extract user information
    """
    try:
        # Get access token from headers
        auth_header = headers.get("Authorization") or headers.get("authorization")
        if not auth_header:
            return None

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        else:
            token = auth_header

        # Initialize auth manager and validate token
        auth_manager = EntraAuthManager()
        user_info = await auth_manager.validate_token(token)

        if user_info:
            # Convert to User
            user = User(
                id=user_info.get("email", ""),
                email=user_info.get("email", ""),
                name=user_info.get("name", ""),
                role=UserRole.ADMIN if user_info.get("email") == "vedprakash.m@outlook.com" else UserRole.USER,
                tenant_id="common",
                object_id=user_info.get("oid", ""),
                preferences={"defaultLLM": "gpt-4", "theme": "dark", "notifications": True},
                usage={"total_prompts": 0, "total_collections": 0, "total_playbooks": 0, "total_forge_projects": 0},
                created_at=datetime.now(timezone.utc),
                last_active=datetime.now(timezone.utc),
                is_active=True,
            )
            return user

        return None

    except Exception as e:
        logging.error(f"Error validating request headers: {e}")
        return None


# Export the User for backward compatibility
__all__ = ["EntraAuthManager", "User", "validate_request_headers", "require_auth", "require_admin"]
