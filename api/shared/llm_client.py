import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential


class LLMProvider:
    """Base class for LLM provider integrations."""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = False
        self.api_key: Optional[str] = None
        self.budget_limit: float = 0.0
        self.current_usage: float = 0.0
        self.priority: int = 1  # 1 = highest priority
        
    async def initialize(self, kv_client: SecretClient) -> bool:
        """Initialize the provider with configuration from Key Vault."""
        try:
            # Get API key from Key Vault
            secret_name = f"{self.name.lower()}-api-key"
            secret = kv_client.get_secret(secret_name)
            self.api_key = secret.value
            
            # Get configuration from Key Vault
            config_secret = kv_client.get_secret(f"{self.name.lower()}-config")
            if config_secret:
                import json
                config = json.loads(config_secret.value)
                self.budget_limit = config.get('budget_limit', 0.0)
                self.priority = config.get('priority', 1)
                self.enabled = config.get('enabled', False)
            
            return True
            
        except Exception as e:
            logging.warning(f"Failed to initialize {self.name} provider: {e}")
            return False
    
    async def check_budget(self) -> bool:
        """Check if the provider is within budget limits."""
        if self.budget_limit <= 0:
            return True  # No budget limit set
        return self.current_usage < self.budget_limit
    
    async def execute_prompt(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a prompt with this provider. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement execute_prompt")


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider implementation."""
    
    def __init__(self):
        super().__init__("OpenAI")
        self.model = "gpt-4"
        self.max_tokens = 2000
        self.temperature = 0.7
    
    async def execute_prompt(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a prompt using OpenAI GPT."""
        if not self.enabled or not await self.check_budget():
            raise Exception(f"{self.name} provider is disabled or over budget")
        
        try:
            # This is a placeholder - actual OpenAI integration would go here
            # For now, return a mock response
            return {
                "provider": self.name,
                "model": self.model,
                "response": f"Mock {self.name} response for: {prompt[:50]}...",
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": 100,
                    "total_tokens": len(prompt.split()) + 100
                },
                "cost": 0.02,  # Mock cost
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logging.error(f"OpenAI execution failed: {e}")
            raise


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation."""
    
    def __init__(self):
        super().__init__("Anthropic")
        self.model = "claude-3-sonnet-20240229"
        self.max_tokens = 2000
    
    async def execute_prompt(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a prompt using Anthropic Claude."""
        if not self.enabled or not await self.check_budget():
            raise Exception(f"{self.name} provider is disabled or over budget")
        
        try:
            # This is a placeholder - actual Anthropic integration would go here
            return {
                "provider": self.name,
                "model": self.model,
                "response": f"Mock {self.name} response for: {prompt[:50]}...",
                "usage": {
                    "input_tokens": len(prompt.split()),
                    "output_tokens": 100,
                    "total_tokens": len(prompt.split()) + 100
                },
                "cost": 0.015,  # Mock cost
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logging.error(f"Anthropic execution failed: {e}")
            raise


class GoogleProvider(LLMProvider):
    """Google Gemini provider implementation."""
    
    def __init__(self):
        super().__init__("Google")
        self.model = "gemini-pro"
        self.max_tokens = 2000
    
    async def execute_prompt(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a prompt using Google Gemini."""
        if not self.enabled or not await self.check_budget():
            raise Exception(f"{self.name} provider is disabled or over budget")
        
        try:
            # This is a placeholder - actual Google integration would go here
            return {
                "provider": self.name,
                "model": self.model,
                "response": f"Mock {self.name} response for: {prompt[:50]}...",
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": 100,
                    "total_tokens": len(prompt.split()) + 100
                },
                "cost": 0.01,  # Mock cost
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logging.error(f"Google execution failed: {e}")
            raise


class LLMManager:
    """Manages multiple LLM providers with admin controls."""
    
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "google": GoogleProvider()
        }
        self._kv_client: Optional[SecretClient] = None
        self._initialized = False
    
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
    
    async def initialize(self) -> bool:
        """Initialize all providers."""
        if self._initialized:
            return True
        
        try:
            kv_client = self.kv_client
            
            for provider in self.providers.values():
                await provider.initialize(kv_client)
            
            self._initialized = True
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize LLM Manager: {e}")
            return False
    
    async def get_available_providers(self) -> List[str]:
        """Get list of enabled and available providers."""
        if not await self.initialize():
            return []
        
        available = []
        for name, provider in self.providers.items():
            if provider.enabled and await provider.check_budget():
                available.append(name)
        
        # Sort by priority (lower number = higher priority)
        available.sort(key=lambda x: self.providers[x].priority)
        return available
    
    async def execute_prompt(self, provider_name: str, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a prompt with the specified provider."""
        if not await self.initialize():
            raise Exception("LLM Manager not initialized")
        
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        provider = self.providers[provider_name]
        if not provider.enabled:
            raise Exception(f"Provider {provider_name} is disabled")
        
        if not await provider.check_budget():
            raise Exception(f"Provider {provider_name} is over budget")
        
        result = await provider.execute_prompt(prompt, context or {})
        
        # Track usage
        if 'cost' in result:
            provider.current_usage += result['cost']
        
        return result
    
    async def execute_multi_llm(self, prompt: str, provider_names: List[str] = None, context: Dict[str, Any] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Execute a prompt across multiple LLM providers."""
        if provider_names is None:
            provider_names = await self.get_available_providers()
        
        results = []
        errors = []
        
        for provider_name in provider_names:
            try:
                result = await self.execute_prompt(provider_name, prompt, context)
                results.append(result)
            except Exception as e:
                error_info = {
                    "provider": provider_name,
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                errors.append(error_info)
                logging.warning(f"Provider {provider_name} failed: {e}")
        
        return {
            "results": results,
            "errors": errors,
            "total_providers": len(provider_names),
            "successful_providers": len(results),
            "failed_providers": len(errors)
        }
    
    async def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers."""
        if not await self.initialize():
            return {}
        
        status = {}
        for name, provider in self.providers.items():
            status[name] = {
                "enabled": provider.enabled,
                "budget_limit": provider.budget_limit,
                "current_usage": provider.current_usage,
                "budget_remaining": max(0, provider.budget_limit - provider.current_usage),
                "priority": provider.priority,
                "available": provider.enabled and await provider.check_budget()
            }
        
        return status


# Global LLM manager instance
llm_manager = LLMManager()


def get_llm_manager() -> LLMManager:
    """Get the global LLM manager instance."""
    return llm_manager


def get_llm_client(provider_name: str = "openai") -> LLMProvider:
    """Get an LLM client for the specified provider."""
    if provider_name not in llm_manager.providers:
        raise ValueError(f"Unknown provider: {provider_name}")
    return llm_manager.providers[provider_name]
