"""Enhanced LLM Client for Sutra Multi-LLM Prompt Studio with Real API Integration and Cost Tracking."""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, AsyncGenerator

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.cosmos.aio import CosmosClient

from .llm_providers import (
    BaseLLMProvider,
    OpenAIProvider,
    AnthropicProvider,
    GoogleProvider,
    LLMResponse,
    TokenUsage
)
from .cost_tracker import CostTracker
from .cost_tracking_middleware import CostTrackingMiddleware, get_cost_tracking_middleware
from .budget_manager import BudgetManager, get_budget_manager, BudgetValidationError


class LLMManager:
    """Enhanced LLM Manager with real provider integrations and cost tracking."""

    def __init__(self, cosmos_client: Optional[CosmosClient] = None, database_name: str = "SutraDB"):
        self.providers: Dict[str, BaseLLMProvider] = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "google": GoogleProvider(),
        }
        self._kv_client: Optional[SecretClient] = None
        self._initialized = False
        self.logger = logging.getLogger("sutra.llm_manager")
        
        # Cost tracking components
        self.cost_tracker: Optional[CostTracker] = None
        self.cost_middleware: Optional[CostTrackingMiddleware] = None
        
        # Budget management
        self.budget_manager: Optional[BudgetManager] = None
        
        if cosmos_client:
            self.cost_tracker = CostTracker(cosmos_client, database_name)
            self.cost_middleware = CostTrackingMiddleware(self.cost_tracker)
            # Set global middleware instance
            get_cost_tracking_middleware(self.cost_tracker)

            if self.cost_tracker:
                self.budget_manager = BudgetManager(cosmos_client, database_name, self.cost_tracker)
                # Set global budget manager instance
                get_budget_manager(cosmos_client, database_name, self.cost_tracker)

    @property
    def kv_client(self) -> SecretClient:
        """Get or create Key Vault client."""
        if self._kv_client is None:
            key_vault_uri = os.getenv("KEY_VAULT_URI") or os.getenv("KEY_VAULT_URL")
            if not key_vault_uri:
                raise ValueError("KEY_VAULT_URI or KEY_VAULT_URL environment variable is required")

            credential = DefaultAzureCredential()
            self._kv_client = SecretClient(vault_url=key_vault_uri, credential=credential)

        return self._kv_client

    async def initialize(self) -> bool:
        """Initialize all providers."""
        if self._initialized:
            return True

        try:
            kv_client = self.kv_client
            
            initialization_results = {}
            for name, provider in self.providers.items():
                try:
                    result = await provider.initialize(kv_client)
                    initialization_results[name] = result
                    if result:
                        self.logger.info(f"Successfully initialized {name} provider")
                    else:
                        self.logger.warning(f"Failed to initialize {name} provider")
                except Exception as e:
                    self.logger.error(f"Error initializing {name} provider: {e}")
                    initialization_results[name] = False

            # Consider it successful if at least one provider initialized
            self._initialized = any(initialization_results.values())
            
            if self._initialized:
                self.logger.info(f"LLM Manager initialized with {sum(initialization_results.values())} providers")
            else:
                self.logger.error("Failed to initialize any LLM providers")
            
            return self._initialized

        except Exception as e:
            self.logger.error(f"Failed to initialize LLM Manager: {e}")
            return False

    async def get_available_providers(self) -> List[str]:
        """Get list of enabled and available providers."""
        if not await self.initialize():
            return []

        available = []
        for name, provider in self.providers.items():
            if provider.enabled and provider._initialized and await provider.check_budget():
                available.append(name)

        # Sort by priority (lower number = higher priority)
        available.sort(key=lambda x: self.providers[x].priority)
        return available

    async def execute_prompt(
        self, 
        provider_name: str, 
        prompt: str, 
        context: Dict[str, Any] = None,
        model: str = None,
        stream: bool = False,
        **kwargs
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """Execute a prompt with the specified provider."""
        if not await self.initialize():
            raise RuntimeError("LLM Manager not initialized")

        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")

        provider = self.providers[provider_name]
        if not provider.enabled:
            raise RuntimeError(f"Provider {provider_name} is disabled")

        if not provider._initialized:
            raise RuntimeError(f"Provider {provider_name} not initialized")

        # Execute the prompt
        return await provider.execute_prompt(
            prompt=prompt, 
            context=context or {}, 
            model=model,
            stream=stream,
            **kwargs
        )

    async def execute_multi_llm(
        self,
        prompt: str,
        provider_names: List[str] = None,
        context: Dict[str, Any] = None,
        model_preferences: Dict[str, str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a prompt across multiple LLM providers."""
        if provider_names is None:
            provider_names = await self.get_available_providers()

        if not provider_names:
            raise RuntimeError("No available providers for multi-LLM execution")

        results = []
        errors = []

        for provider_name in provider_names:
            try:
                model = None
                if model_preferences and provider_name in model_preferences:
                    model = model_preferences[provider_name]
                
                result = await self.execute_prompt(
                    provider_name, 
                    prompt, 
                    context, 
                    model=model,
                    **kwargs
                )
                
                if isinstance(result, LLMResponse):
                    results.append(result)
                else:
                    # Handle streaming responses by collecting them
                    collected = ""
                    async for chunk in result:
                        collected += chunk
                    # Create a mock response for streaming
                    from .llm_providers.base_provider import TokenUsage
                    usage = TokenUsage(
                        prompt_tokens=len(prompt.split()),
                        completion_tokens=len(collected.split()),
                    )
                    mock_response = LLMResponse.create(
                        provider=provider_name,
                        model=model or "unknown",
                        response=collected,
                        usage=usage,
                        cost=0.0  # Streaming cost tracking would need to be implemented separately
                    )
                    results.append(mock_response)
                    
            except Exception as e:
                error_info = {
                    "provider": provider_name,
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                errors.append(error_info)
                self.logger.warning(f"Provider {provider_name} failed: {e}")

        return {
            "results": results,
            "errors": errors,
            "total_providers": len(provider_names),
            "successful_providers": len(results),
            "failed_providers": len(errors),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def execute_prompt_with_cost_tracking(
        self,
        provider_name: str,
        prompt: str,
        user_id: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        stream: bool = False,
        validate_budget: bool = True,
        **kwargs
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """
        Execute a prompt with automatic cost tracking and budget validation.
        
        Args:
            provider_name: LLM provider to use
            prompt: Prompt to execute
            user_id: User identifier for cost tracking
            session_id: Session identifier (optional)
            context: Execution context
            model: Specific model to use
            stream: Whether to stream response
            validate_budget: Whether to validate budget before execution
            **kwargs: Additional provider-specific arguments
            
        Returns:
            LLM response or streaming generator
        """
        if not await self.initialize():
            raise RuntimeError("LLM Manager not initialized")

        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")

        provider = self.providers[provider_name]
        if not provider.enabled:
            raise RuntimeError(f"Provider {provider_name} is disabled")

        if not provider._initialized:
            raise RuntimeError(f"Provider {provider_name} not initialized")

        # Budget validation if cost tracking is enabled
        if validate_budget and self.cost_middleware:
            # Estimate token count for budget validation
            estimated_tokens = len(prompt.split()) * 1.3  # Rough estimation
            
            validation_result = await self.cost_middleware.validate_budget_before_execution(
                user_id=user_id,
                provider=provider_name,
                model=model or provider.models[0]["id"] if provider.models else "unknown",
                estimated_tokens=int(estimated_tokens)
            )
            
            if not validation_result["can_execute"]:
                raise BudgetValidationError(
                    message=validation_result["warnings"][0]["message"] if validation_result["warnings"] else "Budget exceeded",
                    current_spend=validation_result["current_spend"],
                    estimated_cost=validation_result["estimated_cost"],
                    limit=validation_result["budget_limits"].get("emergency", 0)
                )
            
            # Log warnings if any
            for warning in validation_result["warnings"]:
                self.logger.warning(f"Budget warning: {warning['message']}")

        # Execute with cost tracking if middleware is available
        if self.cost_middleware:
            @self.cost_middleware.track_llm_execution(user_id=user_id, session_id=session_id)
            async def tracked_execution():
                return await provider.execute_prompt(
                    prompt=prompt,
                    context=context or {},
                    model=model,
                    stream=stream,
                    **kwargs
                )
            
            return await tracked_execution()
        else:
            # Fallback to regular execution
            return await provider.execute_prompt(
                prompt=prompt, 
                context=context or {}, 
                model=model,
                stream=stream,
                **kwargs
            )

    async def get_cost_summary(self, user_id: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get cost summary for a user."""
        if not self.cost_tracker:
            return None
        
        return await self.cost_tracker.get_cost_analytics(user_id=user_id, days=days)

    async def get_real_time_usage(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get real-time usage statistics for a user."""
        if not self.cost_middleware:
            return None
        
        return await self.cost_middleware.get_real_time_usage_stats(user_id)

    async def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers."""
        if not await self.initialize():
            return {}

        status = {}
        for name, provider in self.providers.items():
            status[name] = provider.get_status()

        return status

    async def health_check(self) -> Dict[str, Any]:
        """Perform health checks on all providers."""
        if not await self.initialize():
            return {"status": "error", "error": "Manager not initialized"}

        health_results = {}
        overall_status = "healthy"
        
        for name, provider in self.providers.items():
            try:
                health = await provider.health_check()
                health_results[name] = health
                
                if health["status"] != "healthy":
                    overall_status = "degraded"
                    
            except Exception as e:
                health_results[name] = {
                    "provider": name,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                overall_status = "degraded"

        return {
            "overall_status": overall_status,
            "providers": health_results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "manager_initialized": self._initialized
        }

    def get_provider(self, provider_name: str) -> BaseLLMProvider:
        """Get a specific provider instance."""
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        return self.providers[provider_name]

    def get_model_info(self, provider_name: str = None) -> Dict[str, Any]:
        """Get model information for all or specific provider."""
        if provider_name:
            if provider_name not in self.providers:
                raise ValueError(f"Unknown provider: {provider_name}")
            provider = self.providers[provider_name]
            return {
                provider_name: {
                    "models": provider.get_models(),
                    "default_model": provider.default_model,
                    "provider_name": provider.provider_name
                }
            }
        
        # Return info for all providers
        model_info = {}
        for name, provider in self.providers.items():
            model_info[name] = {
                "models": provider.get_models(),
                "default_model": provider.default_model,
                "provider_name": provider.provider_name
            }
        return model_info

    def _get_cheaper_models(self, provider_name: str, current_model: str) -> List[str]:
        """Get list of cheaper models for a provider."""
        # Model cost rankings (from most expensive to cheapest)
        model_rankings = {
            "openai": ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-opus-20240229", "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
            "google": ["gemini-1.5-pro", "gemini-pro", "gemini-1.5-flash"]
        }
        
        if provider_name not in model_rankings:
            return []
        
        ranking = model_rankings[provider_name]
        
        try:
            current_index = ranking.index(current_model)
            # Return models that are cheaper (later in the list)
            return ranking[current_index + 1:]
        except ValueError:
            # Model not found in ranking, return all models as potential alternatives
            return ranking[1:] if len(ranking) > 1 else []

    async def get_budget_status(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current budget status for a user."""
        if not self.budget_manager:
            return None
        
        return await self.budget_manager.get_budget_report(user_id=user_id)

    async def create_admin_override(
        self,
        budget_id: str,
        user_id: str,
        admin_user_id: str,
        override_type: str,
        new_limit: float,
        reason: str,
        expires_hours: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Create an admin override for budget restrictions."""
        if not self.budget_manager:
            return None
        
        from decimal import Decimal
        override = await self.budget_manager.create_admin_override(
            budget_id=budget_id,
            user_id=user_id,
            admin_user_id=admin_user_id,
            override_type=override_type,
            new_limit=Decimal(str(new_limit)),
            reason=reason,
            expires_hours=expires_hours
        )
        
        return {
            "id": override.id,
            "budget_id": override.budget_id,
            "user_id": override.user_id,
            "admin_user_id": override.admin_user_id,
            "override_type": override.override_type,
            "original_limit": float(override.original_limit),
            "new_limit": float(override.new_limit),
            "reason": override.reason,
            "expires_at": override.expires_at.isoformat() if override.expires_at else None,
            "created_at": override.created_at.isoformat()
        }

