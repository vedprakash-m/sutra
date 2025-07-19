"""
Tests for llm_client.py module - LLM provider integrations and management
"""

import json
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from api.shared.llm_client import (
    AnthropicProvider,
    BaseLLMProvider,
    GoogleProvider,
    LLMManager,
    LLMProvider,
    LLMResponse,
    OpenAIProvider,
    TokenUsage,
    get_llm_client,
    get_llm_manager,
)


class TestLLMProvider(BaseLLMProvider):
    """Simple test implementation of LLMProvider for testing."""

    def __init__(self, name: str = "TestProvider"):
        super().__init__(name)

    @property
    def provider_name(self) -> str:
        return self.name

    def _get_available_models(self):
        return {"test-model": {"name": "test-model", "cost_per_1k_tokens": 0.01}}

    async def _execute_request(self, model: str, messages: list, **kwargs):
        return LLMResponse(
            content="Test response",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            model=model,
            provider=self.name,
        )


class TestLLMProviderBase:
    """Test suite for LLMProvider base class."""

    def test_init(self):
        """Test LLMProvider initialization."""
        provider = TestLLMProvider("TestProvider")

        assert provider.name == "TestProvider"
        assert provider.enabled is False
        assert provider.api_key is None
        assert provider.budget_limit == 0.0
        assert provider.current_usage == 0.0
        assert provider.priority == 1

    @pytest.mark.asyncio
    @patch("api.shared.llm_client.SecretClient")
    async def test_initialize_success(self, mock_secret_client):
        """Test successful provider initialization."""
        # Mock Key Vault responses
        mock_kv_client = Mock()
        mock_api_secret = Mock()
        mock_api_secret.value = "test-api-key"
        mock_config_secret = Mock()
        mock_config_secret.value = json.dumps({"budget_limit": 100.0, "priority": 2, "enabled": True})

        mock_kv_client.get_secret.side_effect = [mock_api_secret, mock_config_secret]

        provider = TestLLMProvider("TestProvider")
        result = await provider.initialize(mock_kv_client)

        assert result is True
        assert provider.api_key == "test-api-key"  # pragma: allowlist secret
        assert provider.budget_limit == 100.0
        assert provider.priority == 2
        assert provider.enabled is True

    @pytest.mark.asyncio
    @patch("api.shared.llm_client.SecretClient")
    async def test_initialize_api_key_only(self, mock_secret_client):
        """Test initialization with API key but no config."""
        mock_kv_client = Mock()
        mock_api_secret = Mock()
        mock_api_secret.value = "test-api-key"

        mock_kv_client.get_secret.side_effect = [mock_api_secret, None]

        provider = TestLLMProvider("TestProvider")
        result = await provider.initialize(mock_kv_client)

        assert result is True
        assert provider.api_key == "test-api-key"
        assert provider.budget_limit == 0.0
        assert provider.enabled is False

    @pytest.mark.asyncio
    async def test_initialize_failure(self):
        """Test initialization failure."""
        mock_kv_client = Mock()
        mock_kv_client.get_secret.side_effect = Exception("Key Vault error")

        provider = TestLLMProvider("TestProvider")
        result = await provider.initialize(mock_kv_client)

        assert result is False
        assert provider.api_key is None

    @pytest.mark.asyncio
    async def test_check_budget_no_limit(self):
        """Test budget check with no limit set."""
        provider = TestLLMProvider("TestProvider")
        provider.budget_limit = 0.0
        provider.current_usage = 50.0

        result = await provider.check_budget()
        assert result is True

    @pytest.mark.asyncio
    async def test_check_budget_within_limit(self):
        """Test budget check within limit."""
        provider = TestLLMProvider("TestProvider")
        provider.budget_limit = 100.0
        provider.current_usage = 50.0

        result = await provider.check_budget()
        assert result is True

    @pytest.mark.asyncio
    async def test_check_budget_over_limit(self):
        """Test budget check over limit."""
        provider = TestLLMProvider("TestProvider")
        provider.budget_limit = 100.0
        provider.current_usage = 150.0

        result = await provider.check_budget()
        assert result is False

    @pytest.mark.asyncio
    async def test_execute_prompt_not_implemented(self):
        """Test that base provider execute_prompt raises RuntimeError when not initialized."""
        provider = TestLLMProvider("TestProvider")

        with pytest.raises(RuntimeError, match="TestProvider provider not initialized"):
            await provider.execute_prompt("test prompt", {})


class TestOpenAIProvider:
    """Test suite for OpenAIProvider."""

    def test_init(self):
        """Test OpenAIProvider initialization."""
        provider = OpenAIProvider()

        assert provider.name == "OpenAI"
        assert provider.provider_name == "OpenAI"
        # OpenAI provider doesn't have a default model, models are selected per request
        available_models = provider._get_available_models()
        assert "gpt-4" in available_models

    @pytest.mark.asyncio
    async def test_execute_prompt_success(self):
        """Test successful prompt execution."""
        provider = OpenAIProvider()
        provider.enabled = True
        provider.budget_limit = 100.0
        provider.current_usage = 50.0

        result = await provider.execute_prompt("Hello, world!", {"user_id": "123"})

        assert result["provider"] == "OpenAI"
        assert result["model"] == "gpt-4"
        assert "Mock OpenAI response" in result["response"]
        assert "usage" in result
        assert "cost" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_execute_prompt_disabled(self):
        """Test prompt execution when provider is disabled."""
        provider = OpenAIProvider()
        provider.enabled = False

        with pytest.raises(Exception, match="disabled or over budget"):
            await provider.execute_prompt("Hello, world!", {})

    @pytest.mark.asyncio
    async def test_execute_prompt_over_budget(self):
        """Test prompt execution when over budget."""
        provider = OpenAIProvider()
        provider.enabled = True
        provider.budget_limit = 100.0
        provider.current_usage = 150.0

        with pytest.raises(Exception, match="disabled or over budget"):
            await provider.execute_prompt("Hello, world!", {})


class TestAnthropicProvider:
    """Test suite for AnthropicProvider."""

    def test_init(self):
        """Test AnthropicProvider initialization."""
        provider = AnthropicProvider()

        assert provider.name == "Anthropic"
        assert provider.model == "claude-3-sonnet-20240229"
        assert provider.max_tokens == 2000

    @pytest.mark.asyncio
    async def test_execute_prompt_success(self):
        """Test successful prompt execution."""
        provider = AnthropicProvider()
        provider.enabled = True
        provider.budget_limit = 100.0
        provider.current_usage = 50.0

        result = await provider.execute_prompt("Hello, world!", {"user_id": "123"})

        assert result["provider"] == "Anthropic"
        assert result["model"] == "claude-3-sonnet-20240229"
        assert "Mock Anthropic response" in result["response"]
        assert "usage" in result
        assert result["usage"]["input_tokens"] == 2  # "Hello, world!" split by spaces
        assert result["cost"] == 0.015


class TestGoogleProvider:
    """Test suite for GoogleProvider."""

    def test_init(self):
        """Test GoogleProvider initialization."""
        provider = GoogleProvider()

        assert provider.name == "Google"
        assert provider.model == "gemini-pro"
        assert provider.max_tokens == 2000

    @pytest.mark.asyncio
    async def test_execute_prompt_success(self):
        """Test successful prompt execution."""
        provider = GoogleProvider()
        provider.enabled = True
        provider.budget_limit = 100.0
        provider.current_usage = 50.0

        result = await provider.execute_prompt("Hello, world!", {"user_id": "123"})

        assert result["provider"] == "Google"
        assert result["model"] == "gemini-pro"
        assert "Mock Google response" in result["response"]
        assert result["cost"] == 0.01


class TestLLMManager:
    """Test suite for LLMManager."""

    def test_init(self):
        """Test LLMManager initialization."""
        manager = LLMManager()

        assert "openai" in manager.providers
        assert "anthropic" in manager.providers
        assert "google" in manager.providers
        assert manager._initialized is False

    @patch.dict(os.environ, {"KEY_VAULT_URI": "https://test-vault.vault.azure.net/"})
    @patch("api.shared.llm_client.DefaultAzureCredential")
    @patch("api.shared.llm_client.SecretClient")
    def test_kv_client_property(self, mock_secret_client, mock_credential):
        """Test Key Vault client property."""
        manager = LLMManager()

        client = manager.kv_client

        assert client is not None
        mock_secret_client.assert_called_once()
        mock_credential.assert_called_once()

    def test_kv_client_property_no_uri(self):
        """Test Key Vault client property without URI."""
        with patch.dict(os.environ, {}, clear=True):
            manager = LLMManager()

            with pytest.raises(ValueError, match="KEY_VAULT_URI environment variable is required"):
                _ = manager.kv_client

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"KEY_VAULT_URI": "https://test-vault.vault.azure.net/"})
    @patch("api.shared.llm_client.DefaultAzureCredential")
    @patch("api.shared.llm_client.SecretClient")
    async def test_initialize_success(self, mock_secret_client, mock_credential):
        """Test successful LLM manager initialization."""
        # Mock all provider initializations to succeed
        manager = LLMManager()

        # Mock the kv_client property by setting _kv_client directly
        mock_kv_instance = Mock()
        manager._kv_client = mock_kv_instance

        for provider in manager.providers.values():
            provider.initialize = AsyncMock(return_value=True)

        result = await manager.initialize()

        assert result is True
        assert manager._initialized is True

    @pytest.mark.asyncio
    @patch.dict(os.environ, {}, clear=True)
    async def test_initialize_failure(self):
        """Test LLM manager initialization failure."""
        manager = LLMManager()

        # No KEY_VAULT_URI set, should fail
        result = await manager.initialize()

        assert result is False
        assert manager._initialized is False

    @pytest.mark.asyncio
    async def test_get_available_providers(self):
        """Test getting available providers."""
        manager = LLMManager()
        manager.initialize = AsyncMock(return_value=True)

        # Set up providers with different states
        manager.providers["openai"].enabled = True
        manager.providers["openai"].budget_limit = 100.0
        manager.providers["openai"].current_usage = 50.0
        manager.providers["openai"].priority = 2

        manager.providers["anthropic"].enabled = True
        manager.providers["anthropic"].budget_limit = 100.0
        manager.providers["anthropic"].current_usage = 50.0
        manager.providers["anthropic"].priority = 1

        manager.providers["google"].enabled = False

        available = await manager.get_available_providers()

        # Should return enabled providers within budget, sorted by priority
        assert available == ["anthropic", "openai"]  # anthropic has priority 1

    @pytest.mark.asyncio
    async def test_execute_prompt_success(self):
        """Test successful prompt execution."""
        manager = LLMManager()
        manager.initialize = AsyncMock(return_value=True)

        # Mock provider with proper attributes
        mock_provider = Mock()
        mock_provider.enabled = True
        mock_provider.current_usage = 0.0  # Start with 0
        mock_provider.check_budget = AsyncMock(return_value=True)
        mock_provider.execute_prompt = AsyncMock(return_value={"response": "Test response", "cost": 0.02})
        manager.providers["openai"] = mock_provider

        result = await manager.execute_prompt("openai", "Hello!", {"user": "123"})

        assert result["response"] == "Test response"
        assert mock_provider.current_usage == 0.02

    @pytest.mark.asyncio
    async def test_execute_prompt_unknown_provider(self):
        """Test prompt execution with unknown provider."""
        manager = LLMManager()
        manager.initialize = AsyncMock(return_value=True)

        with pytest.raises(ValueError, match="Unknown provider: unknown"):
            await manager.execute_prompt("unknown", "Hello!", {})

    @pytest.mark.asyncio
    async def test_execute_prompt_disabled_provider(self):
        """Test prompt execution with disabled provider."""
        manager = LLMManager()
        manager.initialize = AsyncMock(return_value=True)

        manager.providers["openai"].enabled = False

        with pytest.raises(Exception, match="Provider openai is disabled"):
            await manager.execute_prompt("openai", "Hello!", {})

    @pytest.mark.asyncio
    async def test_execute_multi_llm_success(self):
        """Test multi-LLM execution success."""
        manager = LLMManager()
        manager.get_available_providers = AsyncMock(return_value=["openai", "anthropic"])
        manager.execute_prompt = AsyncMock(
            side_effect=[
                {"provider": "openai", "response": "OpenAI response"},
                {"provider": "anthropic", "response": "Anthropic response"},
            ]
        )

        result = await manager.execute_multi_llm("Hello!")

        assert len(result["results"]) == 2
        assert len(result["errors"]) == 0
        assert result["successful_providers"] == 2
        assert result["failed_providers"] == 0

    @pytest.mark.asyncio
    async def test_execute_multi_llm_with_failures(self):
        """Test multi-LLM execution with some failures."""
        manager = LLMManager()
        manager.get_available_providers = AsyncMock(return_value=["openai", "anthropic"])
        manager.execute_prompt = AsyncMock(
            side_effect=[
                {"provider": "openai", "response": "OpenAI response"},
                Exception("Anthropic failed"),
            ]
        )

        result = await manager.execute_multi_llm("Hello!")

        assert len(result["results"]) == 1
        assert len(result["errors"]) == 1
        assert result["successful_providers"] == 1
        assert result["failed_providers"] == 1
        assert result["errors"][0]["provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_get_provider_status(self):
        """Test getting provider status."""
        manager = LLMManager()
        manager.initialize = AsyncMock(return_value=True)

        # Set up provider states
        manager.providers["openai"].enabled = True
        manager.providers["openai"].budget_limit = 100.0
        manager.providers["openai"].current_usage = 75.0
        manager.providers["openai"].priority = 1

        status = await manager.get_provider_status()

        assert "openai" in status
        assert status["openai"]["enabled"] is True
        assert status["openai"]["budget_limit"] == 100.0
        assert status["openai"]["current_usage"] == 75.0
        assert status["openai"]["budget_remaining"] == 25.0
        assert status["openai"]["priority"] == 1
        assert status["openai"]["available"] is True


class TestLLMManagerEdgeCases:
    """Test edge cases and error conditions for LLMManager."""

    @pytest.mark.asyncio
    async def test_get_available_providers_not_initialized(self):
        """Test getting available providers when not initialized."""
        manager = LLMManager()
        manager.initialize = AsyncMock(return_value=False)

        available = await manager.get_available_providers()
        assert available == []

    @pytest.mark.asyncio
    async def test_execute_prompt_not_initialized(self):
        """Test prompt execution when not initialized."""
        manager = LLMManager()
        manager.initialize = AsyncMock(return_value=False)

        with pytest.raises(Exception, match="LLM Manager not initialized"):
            await manager.execute_prompt("openai", "Hello!", {})

    @pytest.mark.asyncio
    async def test_get_provider_status_not_initialized(self):
        """Test getting provider status when not initialized."""
        manager = LLMManager()
        manager.initialize = AsyncMock(return_value=False)

        status = await manager.get_provider_status()
        assert status == {}


class TestGlobalFunctions:
    """Test global functions."""

    def test_get_llm_manager(self):
        """Test getting global LLM manager."""
        manager1 = get_llm_manager()
        manager2 = get_llm_manager()

        # Should return the same instance
        assert manager1 is manager2

    def test_get_llm_client(self):
        """Test getting LLM client for specific provider."""
        client = get_llm_client("openai")
        assert isinstance(client, OpenAIProvider)
        assert client.name == "OpenAI"

    def test_get_llm_client_unknown_provider(self):
        """Test getting LLM client for unknown provider."""
        with pytest.raises(ValueError, match="Unknown provider: unknown"):
            get_llm_client("unknown")
