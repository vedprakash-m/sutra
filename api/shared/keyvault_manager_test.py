"""Tests for Azure Key Vault Manager."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from shared.keyvault_manager import KeyVaultManager, get_keyvault_manager


class TestKeyVaultManager:
    """Tests for KeyVaultManager class."""

    def test_generate_secret_name(self):
        """Test secret name generation format."""
        manager = KeyVaultManager(key_vault_uri="https://test-vault.vault.azure.net")

        # Test with standard user ID and provider
        secret_name = manager._generate_secret_name("12345678-1234-1234-1234-123456789012", "openai")
        assert secret_name.startswith("sutra-llm-")
        assert "openai" in secret_name
        assert len(secret_name) <= 127  # Key Vault name limit

    def test_generate_secret_name_with_underscores(self):
        """Test secret name generation replaces underscores with dashes."""
        manager = KeyVaultManager(key_vault_uri="https://test-vault.vault.azure.net")

        secret_name = manager._generate_secret_name("user123", "custom_provider")
        assert "_" not in secret_name
        assert "custom-provider" in secret_name

    @patch("shared.keyvault_manager.SecretClient")
    @patch("shared.keyvault_manager.DefaultAzureCredential")
    def test_kv_client_initialization(self, mock_credential, mock_secret_client):
        """Test Key Vault client is initialized on first access."""
        manager = KeyVaultManager(key_vault_uri="https://test-vault.vault.azure.net")

        # Access kv_client property
        _ = manager.kv_client

        # Verify credential and client were created
        mock_credential.assert_called_once()
        mock_secret_client.assert_called_once()

    def test_kv_client_raises_without_uri(self):
        """Test that accessing kv_client without URI raises ValueError."""
        manager = KeyVaultManager(key_vault_uri=None)

        with patch.dict("os.environ", {"KEY_VAULT_URI": "", "KEY_VAULT_URL": ""}, clear=False):
            # Clear any cached values
            manager._key_vault_uri = None
            with pytest.raises(ValueError, match="KEY_VAULT_URI or KEY_VAULT_URL"):
                _ = manager.kv_client

    @pytest.mark.asyncio
    @patch("shared.keyvault_manager.SecretClient")
    @patch("shared.keyvault_manager.DefaultAzureCredential")
    async def test_store_api_key(self, mock_credential, mock_secret_client):
        """Test storing API key in Key Vault."""
        mock_client = MagicMock()
        mock_secret_client.return_value = mock_client

        manager = KeyVaultManager(key_vault_uri="https://test-vault.vault.azure.net")

        result = await manager.store_api_key("user-123", "openai", "sk-test-key")

        # Verify set_secret was called with correct parameters
        mock_client.set_secret.assert_called_once()
        call_args = mock_client.set_secret.call_args
        assert "sutra-llm" in call_args.kwargs.get("name", call_args.args[0] if call_args.args else "")

        # Verify return value is a secret name
        assert result.startswith("sutra-llm-")

    @pytest.mark.asyncio
    @patch("shared.keyvault_manager.SecretClient")
    @patch("shared.keyvault_manager.DefaultAzureCredential")
    async def test_get_api_key_found(self, mock_credential, mock_secret_client):
        """Test retrieving existing API key."""
        mock_client = MagicMock()
        mock_secret = MagicMock()
        mock_secret.value = "sk-test-key"
        mock_client.get_secret.return_value = mock_secret
        mock_secret_client.return_value = mock_client

        manager = KeyVaultManager(key_vault_uri="https://test-vault.vault.azure.net")

        result = await manager.get_api_key("user-123", "openai")

        assert result == "sk-test-key"

    @pytest.mark.asyncio
    @patch("shared.keyvault_manager.SecretClient")
    @patch("shared.keyvault_manager.DefaultAzureCredential")
    async def test_get_api_key_not_found(self, mock_credential, mock_secret_client):
        """Test retrieving non-existent API key returns None."""
        mock_client = MagicMock()
        mock_client.get_secret.side_effect = ResourceNotFoundError("Secret not found")
        mock_secret_client.return_value = mock_client

        manager = KeyVaultManager(key_vault_uri="https://test-vault.vault.azure.net")

        result = await manager.get_api_key("user-123", "openai")

        assert result is None

    @pytest.mark.asyncio
    @patch("shared.keyvault_manager.SecretClient")
    @patch("shared.keyvault_manager.DefaultAzureCredential")
    async def test_delete_api_key_success(self, mock_credential, mock_secret_client):
        """Test deleting API key from Key Vault."""
        mock_client = MagicMock()
        mock_poller = MagicMock()
        mock_client.begin_delete_secret.return_value = mock_poller
        mock_secret_client.return_value = mock_client

        manager = KeyVaultManager(key_vault_uri="https://test-vault.vault.azure.net")

        result = await manager.delete_api_key("user-123", "openai")

        assert result is True
        mock_poller.wait.assert_called_once()

    @pytest.mark.asyncio
    @patch("shared.keyvault_manager.SecretClient")
    @patch("shared.keyvault_manager.DefaultAzureCredential")
    async def test_delete_api_key_not_found(self, mock_credential, mock_secret_client):
        """Test deleting non-existent API key returns True."""
        mock_client = MagicMock()
        mock_client.begin_delete_secret.side_effect = ResourceNotFoundError("Secret not found")
        mock_secret_client.return_value = mock_client

        manager = KeyVaultManager(key_vault_uri="https://test-vault.vault.azure.net")

        result = await manager.delete_api_key("user-123", "openai")

        assert result is True

    @patch("shared.keyvault_manager.SecretClient")
    @patch("shared.keyvault_manager.DefaultAzureCredential")
    def test_key_vault_available_true(self, mock_credential, mock_secret_client):
        """Test key_vault_available returns True when configured."""
        manager = KeyVaultManager(key_vault_uri="https://test-vault.vault.azure.net")

        assert manager.key_vault_available() is True

    def test_key_vault_available_false_no_uri(self):
        """Test key_vault_available returns False without URI."""
        manager = KeyVaultManager(key_vault_uri=None)
        manager._key_vault_uri = None

        assert manager.key_vault_available() is False


class TestGetKeyvaultManager:
    """Tests for singleton get_keyvault_manager function."""

    @patch("shared.keyvault_manager._keyvault_manager", None)
    def test_creates_singleton_instance(self):
        """Test that get_keyvault_manager creates singleton."""
        import shared.keyvault_manager as module

        module._keyvault_manager = None

        manager1 = get_keyvault_manager()
        manager2 = get_keyvault_manager()

        assert manager1 is manager2
