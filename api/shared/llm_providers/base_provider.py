"""Base LLM Provider for Sutra Multi-LLM Prompt Studio."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, AsyncGenerator, Union
from dataclasses import dataclass, field
from enum import Enum

from azure.keyvault.secrets import SecretClient


class ModelCapability(Enum):
    """Capabilities that a model can support."""
    TEXT_GENERATION = "text_generation"
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    IMAGE_ANALYSIS = "image_analysis"
    CODE_GENERATION = "code_generation"
    JSON_MODE = "json_mode"


@dataclass
class TokenUsage:
    """Token usage information for an LLM request."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = self.prompt_tokens + self.completion_tokens


@dataclass
class ModelInfo:
    """Information about an LLM model."""
    name: str
    display_name: str
    max_tokens: int
    cost_per_input_token: float  # Cost per 1K input tokens
    cost_per_output_token: float  # Cost per 1K output tokens
    capabilities: List[ModelCapability] = field(default_factory=list)
    context_window: int = 4096
    supports_streaming: bool = True


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    provider: str
    model: str
    response: str
    usage: TokenUsage
    cost: float
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    
    @classmethod
    def create(cls, provider: str, model: str, response: str, usage: TokenUsage, 
               cost: float, metadata: Optional[Dict[str, Any]] = None, 
               finish_reason: Optional[str] = None) -> 'LLMResponse':
        """Create a new LLM response with current timestamp."""
        return cls(
            provider=provider,
            model=model, 
            response=response,
            usage=usage,
            cost=cost,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
            finish_reason=finish_reason
        )


class BaseLLMProvider(ABC):
    """Base class for all LLM provider integrations."""

    def __init__(self, name: str):
        self.name = name
        self.enabled = False
        self.api_key: Optional[str] = None
        self.budget_limit: float = 0.0
        self.current_usage: float = 0.0
        self.priority: int = 1  # 1 = highest priority
        self.models: Dict[str, ModelInfo] = {}
        self.default_model: Optional[str] = None
        self._initialized = False
        self.logger = logging.getLogger(f"sutra.llm.{name.lower()}")

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the official provider name."""
        pass

    @abstractmethod
    def _get_available_models(self) -> Dict[str, ModelInfo]:
        """Get available models for this provider. Override in subclasses."""
        pass

    @abstractmethod
    async def _execute_request(
        self, 
        prompt: str, 
        model: str, 
        context: Dict[str, Any],
        stream: bool = False
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """Execute the actual API request. Override in subclasses."""
        pass

    async def initialize(self, kv_client: SecretClient) -> bool:
        """Initialize the provider with configuration from Key Vault."""
        if self._initialized:
            return True

        try:
            # Get API key from Key Vault
            secret_name = f"{self.name.lower()}-api-key"
            try:
                secret = kv_client.get_secret(secret_name)
                self.api_key = secret.value
            except Exception as e:
                self.logger.warning(f"Could not get API key for {self.name}: {e}")
                return False

            # Get configuration from Key Vault
            try:
                config_secret = kv_client.get_secret(f"{self.name.lower()}-config")
                if config_secret:
                    import json
                    config = json.loads(config_secret.value)
                    self.budget_limit = config.get("budget_limit", 100.0)  # Default $100
                    self.priority = config.get("priority", 1)
                    self.enabled = config.get("enabled", True)
                    self.default_model = config.get("default_model")
            except Exception:
                # Use defaults if config not found
                self.budget_limit = 100.0
                self.priority = 1
                self.enabled = True

            # Load available models
            self.models = self._get_available_models()
            if not self.default_model and self.models:
                self.default_model = list(self.models.keys())[0]

            self._initialized = True
            self.logger.info(f"Initialized {self.name} provider with {len(self.models)} models")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize {self.name} provider: {e}")
            return False

    async def check_budget(self, estimated_cost: float = 0.0) -> bool:
        """Check if the provider is within budget limits."""
        if self.budget_limit <= 0:
            return True  # No budget limit set
        
        projected_usage = self.current_usage + estimated_cost
        return projected_usage < self.budget_limit

    def estimate_cost(self, prompt: str, model: Optional[str] = None, max_tokens: Optional[int] = None) -> float:
        """Estimate the cost of a request before execution."""
        if not model:
            model = self.default_model
        
        if not model or model not in self.models:
            return 0.0

        model_info = self.models[model]
        
        # Rough token estimation (1 token ≈ 4 characters for English text)
        input_tokens = len(prompt) // 4
        output_tokens = max_tokens or (model_info.max_tokens // 4)
        
        input_cost = (input_tokens / 1000) * model_info.cost_per_input_token
        output_cost = (output_tokens / 1000) * model_info.cost_per_output_token
        
        return input_cost + output_cost

    async def execute_prompt(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        stream: bool = False,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """Execute a prompt with this provider."""
        if not self._initialized:
            raise RuntimeError(f"{self.name} provider not initialized")

        if not self.enabled:
            raise RuntimeError(f"{self.name} provider is disabled")

        # Use default model if none specified
        if not model:
            model = self.default_model
        
        if not model or model not in self.models:
            raise ValueError(f"Invalid model {model} for {self.name}")

        # Estimate cost and check budget
        estimated_cost = self.estimate_cost(prompt, model, max_tokens)
        if not await self.check_budget(estimated_cost):
            raise RuntimeError(f"{self.name} provider would exceed budget limit")

        # Prepare context
        execution_context = {
            **(context or {}),
            "model": model,
            "max_tokens": max_tokens or self.models[model].max_tokens,
            "temperature": temperature,
            "provider": self.name
        }

        try:
            # Execute the request
            result = await self._execute_request(prompt, model, execution_context, stream)
            
            # Track usage for non-streaming responses
            if isinstance(result, LLMResponse):
                self.current_usage += result.cost
                self.logger.info(f"Executed {model} request, cost: ${result.cost:.4f}, total usage: ${self.current_usage:.4f}")
            
            return result

        except Exception as e:
            self.logger.error(f"{self.name} execution failed: {e}")
            raise RuntimeError(f"{self.name} provider execution failed: {str(e)}")

    def get_models(self) -> Dict[str, ModelInfo]:
        """Get available models for this provider."""
        return self.models.copy()

    def get_status(self) -> Dict[str, Any]:
        """Get current provider status."""
        return {
            "name": self.name,
            "provider": self.provider_name,
            "enabled": self.enabled,
            "initialized": self._initialized,
            "budget_limit": self.budget_limit,
            "current_usage": self.current_usage,
            "budget_remaining": max(0, self.budget_limit - self.current_usage),
            "budget_percentage": (self.current_usage / self.budget_limit * 100) if self.budget_limit > 0 else 0,
            "priority": self.priority,
            "available": self.enabled and self._initialized,
            "models": {name: {
                "display_name": info.display_name,
                "max_tokens": info.max_tokens,
                "capabilities": [cap.value for cap in info.capabilities],
                "cost_per_1k_input": info.cost_per_input_token,
                "cost_per_1k_output": info.cost_per_output_token
            } for name, info in self.models.items()},
            "default_model": self.default_model
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the provider."""
        health = {
            "provider": self.name,
            "status": "unknown",
            "initialized": self._initialized,
            "enabled": self.enabled,
            "api_key_configured": bool(self.api_key),
            "models_loaded": len(self.models),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if not self._initialized:
            health["status"] = "not_initialized"
            return health

        if not self.enabled:
            health["status"] = "disabled"
            return health

        if not self.api_key:
            health["status"] = "missing_api_key"
            return health

        try:
            # Try a minimal request to test connectivity
            test_prompt = "Hello"
            response = await self.execute_prompt(test_prompt, {"test": True})
            if isinstance(response, LLMResponse) and response.response:
                health["status"] = "healthy"
            else:
                health["status"] = "unhealthy"
        except Exception as e:
            health["status"] = "error"
            health["error"] = str(e)

        return health
