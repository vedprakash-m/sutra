"""Azure Key Vault Manager for Sutra API Key Storage.

Provides secure storage and retrieval of LLM API keys using Azure Key Vault.
"""

import logging
import os
from typing import Optional

from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

logger = logging.getLogger("sutra.keyvault")


class KeyVaultManager:
    """Manages API key storage in Azure Key Vault."""

    def __init__(self, key_vault_uri: Optional[str] = None):
        """Initialize Key Vault manager.

        Args:
            key_vault_uri: Azure Key Vault URI. If not provided, uses environment variable.
        """
        self._kv_client: Optional[SecretClient] = None
        self._key_vault_uri = key_vault_uri or os.getenv("KEY_VAULT_URI") or os.getenv("KEY_VAULT_URL")

    @property
    def kv_client(self) -> SecretClient:
        """Get or create Key Vault client."""
        if self._kv_client is None:
            if not self._key_vault_uri:
                raise ValueError("KEY_VAULT_URI or KEY_VAULT_URL environment variable is required")

            credential = DefaultAzureCredential()
            self._kv_client = SecretClient(vault_url=self._key_vault_uri, credential=credential)
            logger.info(f"Initialized Key Vault client for {self._key_vault_uri}")

        return self._kv_client

    def _generate_secret_name(self, user_id: str, provider: str) -> str:
        """Generate a unique secret name for storing API key.

        Format: sutra-llm-{user_id_hash}-{provider}

        Args:
            user_id: User's unique identifier
            provider: LLM provider name (openai, anthropic, google)

        Returns:
            Secret name suitable for Key Vault
        """
        # Use last 8 chars of user_id to keep name manageable
        user_hash = user_id.replace("-", "")[-8:]
        # Key Vault secret names can only contain alphanumeric characters and dashes
        provider_clean = provider.lower().replace("_", "-")
        return f"sutra-llm-{user_hash}-{provider_clean}"

    async def store_api_key(self, user_id: str, provider: str, api_key: str) -> str:
        """Store an API key securely in Key Vault.

        Args:
            user_id: User's unique identifier
            provider: LLM provider name
            api_key: The API key to store

        Returns:
            Reference key to retrieve the stored secret

        Raises:
            HttpResponseError: If Key Vault operation fails
        """
        secret_name = self._generate_secret_name(user_id, provider)

        try:
            # Store the secret with metadata
            self.kv_client.set_secret(
                name=secret_name, value=api_key, tags={"user_id": user_id, "provider": provider, "app": "sutra"}
            )
            logger.info(f"Stored API key for user {user_id}, provider {provider}")
            return secret_name

        except HttpResponseError as e:
            logger.error(f"Failed to store API key in Key Vault: {e}")
            raise

    async def get_api_key(self, user_id: str, provider: str) -> Optional[str]:
        """Retrieve an API key from Key Vault.

        Args:
            user_id: User's unique identifier
            provider: LLM provider name

        Returns:
            The API key if found, None otherwise
        """
        secret_name = self._generate_secret_name(user_id, provider)

        try:
            secret = self.kv_client.get_secret(secret_name)
            logger.info(f"Retrieved API key for user {user_id}, provider {provider}")
            return secret.value

        except ResourceNotFoundError:
            logger.warning(f"API key not found for user {user_id}, provider {provider}")
            return None
        except HttpResponseError as e:
            logger.error(f"Failed to retrieve API key from Key Vault: {e}")
            raise

    async def delete_api_key(self, user_id: str, provider: str) -> bool:
        """Delete an API key from Key Vault.

        Args:
            user_id: User's unique identifier
            provider: LLM provider name

        Returns:
            True if deletion was successful or key didn't exist
        """
        secret_name = self._generate_secret_name(user_id, provider)

        try:
            # Begin soft delete
            poller = self.kv_client.begin_delete_secret(secret_name)
            # Wait for deletion to complete
            poller.wait()
            logger.info(f"Deleted API key for user {user_id}, provider {provider}")
            return True

        except ResourceNotFoundError:
            logger.info(f"API key already deleted for user {user_id}, provider {provider}")
            return True
        except HttpResponseError as e:
            logger.error(f"Failed to delete API key from Key Vault: {e}")
            raise

    async def update_api_key(self, user_id: str, provider: str, api_key: str) -> str:
        """Update an existing API key in Key Vault.

        Args:
            user_id: User's unique identifier
            provider: LLM provider name
            api_key: The new API key

        Returns:
            Reference key to retrieve the stored secret
        """
        # Key Vault set_secret will overwrite existing secrets
        return await self.store_api_key(user_id, provider, api_key)

    def key_vault_available(self) -> bool:
        """Check if Key Vault is configured and accessible.

        Returns:
            True if Key Vault is available, False otherwise
        """
        if not self._key_vault_uri:
            return False

        try:
            # Try to list secrets (just to verify connection)
            # This will fail early if credentials are invalid
            _ = self.kv_client
            return True
        except Exception as e:
            logger.warning(f"Key Vault not available: {e}")
            return False


# Singleton instance
_keyvault_manager: Optional[KeyVaultManager] = None


def get_keyvault_manager() -> KeyVaultManager:
    """Get or create the singleton KeyVaultManager instance."""
    global _keyvault_manager
    if _keyvault_manager is None:
        _keyvault_manager = KeyVaultManager()
    return _keyvault_manager
