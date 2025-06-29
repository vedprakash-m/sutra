"""
Microsoft Entra ID Authentication Module
Provides JWT token validation with JWKS caching and VedUser standard compliance
"""

import json
import time
from typing import Optional, Dict, Any, List
from cachetools import TTLCache
import jwt
import requests
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class VedUser(BaseModel):
    """VedUser Standard - Unified user object across all Vedprakash applications"""
    id: str
    email: str
    name: str
    role: str  # 'user', 'admin', 'guest'
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    tenant: Optional[Dict[str, str]] = None
    cross_app_roles: Optional[Dict[str, List[str]]] = None

class JWKSCache:
    """JWKS caching for efficient token validation"""

    def __init__(self, cache_ttl: int = 3600):  # 1 hour default
        self.cache = TTLCache(maxsize=10, ttl=cache_ttl)
        self.jwks_endpoints = {
            'common': 'https://login.microsoftonline.com/common/discovery/v2.0/keys',
            'consumers': 'https://login.microsoftonline.com/consumers/discovery/v2.0/keys'
        }

    def get_jwks(self, tenant_id: str = 'common') -> Dict[str, Any]:
        """Get JWKS from cache or fetch from Microsoft"""
        cache_key = f"jwks_{tenant_id}"

        if cache_key in self.cache:
            logger.debug(f"JWKS cache hit for tenant: {tenant_id}")
            return self.cache[cache_key]

        # Determine JWKS endpoint
        if tenant_id in self.jwks_endpoints:
            jwks_url = self.jwks_endpoints[tenant_id]
        else:
            jwks_url = f'https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys'

        try:
            logger.info(f"Fetching JWKS from: {jwks_url}")
            response = requests.get(jwks_url, timeout=10)
            response.raise_for_status()

            jwks = response.json()
            self.cache[cache_key] = jwks
            logger.info(f"JWKS cached for tenant: {tenant_id}")
            return jwks

        except Exception as e:
            logger.error(f"Failed to fetch JWKS for tenant {tenant_id}: {e}")
            raise

    def get_signing_key(self, token_kid: str, tenant_id: str = 'common') -> Optional[str]:
        """Get signing key for token validation"""
        try:
            jwks = self.get_jwks(tenant_id)

            for key in jwks.get('keys', []):
                if key.get('kid') == token_kid:
                    # Convert JWK to PEM format
                    from jwt.algorithms import RSAAlgorithm
                    public_key = RSAAlgorithm.from_jwk(json.dumps(key))
                    return public_key

            logger.warning(f"No signing key found for kid: {token_kid}")
            return None

        except Exception as e:
            logger.error(f"Error getting signing key: {e}")
            return None

class EntraIdAuth:
    """Microsoft Entra ID authentication handler"""

    def __init__(self, tenant_id: str = 'common', client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.jwks_cache = JWKSCache()

        # Valid issuers for token validation
        self.valid_issuers = [
            f'https://login.microsoftonline.com/{tenant_id}/v2.0',
            f'https://sts.windows.net/{tenant_id}/',
            'https://login.microsoftonline.com/common/v2.0',
        ]

    def validate_token(self, token: str) -> Optional[VedUser]:
        """Validate Microsoft Entra ID JWT token and return VedUser"""
        try:
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')

            if not kid:
                logger.error("Token missing kid in header")
                return None

            # Get signing key
            signing_key = self.jwks_cache.get_signing_key(kid, self.tenant_id)
            if not signing_key:
                logger.error(f"No signing key found for kid: {kid}")
                return None

            # Validate and decode token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer=self.valid_issuers,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": self.client_id is not None,
                    "verify_iss": True,
                }
            )

            # Extract user information
            return self._create_ved_user_from_token(payload)

        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None

    def _create_ved_user_from_token(self, payload: Dict[str, Any]) -> VedUser:
        """Create VedUser from JWT token payload"""
        # Extract user information from token claims
        user_id = payload.get('oid') or payload.get('sub')
        email = payload.get('email') or payload.get('preferred_username') or payload.get('upn')
        name = payload.get('name', '')
        given_name = payload.get('given_name')
        family_name = payload.get('family_name')

        # If no name, construct from email
        if not name and email:
            name = email.split('@')[0].replace('.', ' ').replace('_', ' ').title()

        # Determine user role
        role = self._determine_user_role(email, payload)

        # Extract tenant information
        tenant_info = {
            'id': payload.get('tid', ''),
            'name': payload.get('tenant_name', 'Microsoft Entra ID')
        }

        return VedUser(
            id=user_id,
            email=email,
            name=name,
            role=role,
            given_name=given_name,
            family_name=family_name,
            tenant=tenant_info,
            created_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            updated_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        )

    def _determine_user_role(self, email: str, payload: Dict[str, Any]) -> str:
        """Determine user role from token claims and business logic"""
        # Check for roles in token
        roles = payload.get('roles', [])
        app_roles = payload.get('app_roles', [])

        if 'admin' in roles or 'admin' in app_roles:
            return 'admin'

        # Check for specific admin users
        admin_emails = [
            'vedprakash.m@outlook.com',
            # Add other admin emails here
        ]

        if email in admin_emails:
            return 'admin'

        return 'user'

# Global instance for reuse
_entra_auth_instance: Optional[EntraIdAuth] = None

def get_entra_auth(tenant_id: str = 'common', client_id: Optional[str] = None) -> EntraIdAuth:
    """Get or create EntraIdAuth instance (singleton pattern)"""
    global _entra_auth_instance

    if _entra_auth_instance is None:
        _entra_auth_instance = EntraIdAuth(tenant_id, client_id)

    return _entra_auth_instance

def validate_bearer_token(authorization_header: str) -> Optional[VedUser]:
    """Validate Bearer token from Authorization header"""
    if not authorization_header or not authorization_header.startswith('Bearer '):
        return None

    token = authorization_header[7:]  # Remove 'Bearer ' prefix
    auth = get_entra_auth()
    return auth.validate_token(token)

def validate_request_headers(headers: Dict[str, str]) -> Optional[VedUser]:
    """Validate authentication from request headers (supports multiple auth methods)"""
    # Try Bearer token first (MSAL authentication)
    auth_header = headers.get('Authorization') or headers.get('authorization')
    if auth_header:
        user = validate_bearer_token(auth_header)
        if user:
            logger.info(f"✅ Entra ID authentication successful: {user.email}")
            return user

    # Fallback to Azure Static Web Apps authentication
    principal_header = headers.get('x-ms-client-principal')
    if principal_header:
        try:
            import base64
            principal_data = json.loads(base64.b64decode(principal_header))

            user_id = principal_data.get('userId')
            email = principal_data.get('userDetails')
            roles = principal_data.get('userRoles', [])

            if user_id and email:
                role = 'admin' if 'admin' in roles or email == 'vedprakash.m@outlook.com' else 'user'

                ved_user = VedUser(
                    id=user_id,
                    email=email,
                    name=email.split('@')[0].title(),
                    role=role,
                    created_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    updated_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                )

                logger.info(f"✅ SWA authentication successful: {ved_user.email}")
                return ved_user

        except Exception as e:
            logger.error(f"SWA auth validation error: {e}")

    logger.warning("❌ No valid authentication found in request headers")
    return None
