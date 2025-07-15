"""Anthropic Provider for Sutra Multi-LLM Prompt Studio."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator, Union

import anthropic
from anthropic import AsyncAnthropic

from .base_provider import (
    BaseLLMProvider, 
    ModelInfo, 
    ModelCapability, 
    TokenUsage, 
    LLMResponse
)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider implementation with real API integration."""

    def __init__(self):
        super().__init__("Anthropic")
        self.client: Optional[AsyncAnthropic] = None

    @property
    def provider_name(self) -> str:
        """Get the official provider name."""
        return "Anthropic"

    def _get_available_models(self) -> Dict[str, ModelInfo]:
        """Get available Anthropic models with current pricing."""
        return {
            "claude-3-5-sonnet-20241022": ModelInfo(
                name="claude-3-5-sonnet-20241022",
                display_name="Claude 3.5 Sonnet",
                max_tokens=8192,
                cost_per_input_token=0.003,  # $0.003 per 1K tokens
                cost_per_output_token=0.015,  # $0.015 per 1K tokens
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.STREAMING,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.IMAGE_ANALYSIS
                ],
                context_window=200000,
                supports_streaming=True
            ),
            "claude-3-haiku-20240307": ModelInfo(
                name="claude-3-haiku-20240307",
                display_name="Claude 3 Haiku",
                max_tokens=4096,
                cost_per_input_token=0.00025,  # $0.00025 per 1K tokens
                cost_per_output_token=0.00125,  # $0.00125 per 1K tokens
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.STREAMING,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.IMAGE_ANALYSIS
                ],
                context_window=200000,
                supports_streaming=True
            ),
            "claude-3-opus-20240229": ModelInfo(
                name="claude-3-opus-20240229",
                display_name="Claude 3 Opus",
                max_tokens=4096,
                cost_per_input_token=0.015,  # $0.015 per 1K tokens
                cost_per_output_token=0.075,  # $0.075 per 1K tokens
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.STREAMING,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.IMAGE_ANALYSIS
                ],
                context_window=200000,
                supports_streaming=True
            ),
        }

    async def initialize(self, kv_client) -> bool:
        """Initialize Anthropic provider with API client."""
        if not await super().initialize(kv_client):
            return False

        try:
            # Initialize Anthropic client
            self.client = AsyncAnthropic(
                api_key=self.api_key
            )

            # Set default model
            if not self.default_model:
                self.default_model = "claude-3-5-sonnet-20241022"  # Use Claude 3.5 Sonnet as default

            self.logger.info(f"Anthropic client initialized with API key ending in: ...{self.api_key[-4:] if self.api_key else 'None'}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize Anthropic client: {e}")
            return False

    def _calculate_cost(self, usage: TokenUsage, model: str) -> float:
        """Calculate cost based on token usage and model pricing."""
        if model not in self.models:
            return 0.0

        model_info = self.models[model]
        input_cost = (usage.prompt_tokens / 1000) * model_info.cost_per_input_token
        output_cost = (usage.completion_tokens / 1000) * model_info.cost_per_output_token
        return input_cost + output_cost

    async def _execute_request(
        self, 
        prompt: str, 
        model: str, 
        context: Dict[str, Any],
        stream: bool = False
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """Execute the actual Anthropic API request."""
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")

        # Prepare the messages
        messages = [{"role": "user", "content": prompt}]
        
        # Prepare API parameters
        api_params = {
            "model": model,
            "messages": messages,
            "max_tokens": context.get("max_tokens", self.models[model].max_tokens),
            "temperature": context.get("temperature", 0.7),
            "stream": stream
        }

        # Add system prompt if provided
        if "system_prompt" in context:
            api_params["system"] = context["system_prompt"]

        try:
            if stream:
                return self._handle_streaming_response(api_params, model)
            else:
                return await self._handle_standard_response(api_params, model)

        except anthropic.RateLimitError as e:
            self.logger.warning(f"Anthropic rate limit exceeded: {e}")
            raise RuntimeError(f"Rate limit exceeded. Please try again later.")
        
        except anthropic.APIError as e:
            self.logger.error(f"Anthropic API error: {e}")
            raise RuntimeError(f"Anthropic API error: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Unexpected error in Anthropic request: {e}")
            raise RuntimeError(f"Anthropic request failed: {str(e)}")

    async def _handle_standard_response(self, api_params: Dict[str, Any], model: str) -> LLMResponse:
        """Handle non-streaming Anthropic response."""
        response = await self.client.messages.create(**api_params)
        
        # Extract response data - Anthropic returns content as a list
        content = ""
        if response.content and len(response.content) > 0:
            content = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
        
        finish_reason = response.stop_reason
        
        # Create usage object
        usage = TokenUsage(
            prompt_tokens=response.usage.input_tokens if response.usage else 0,
            completion_tokens=response.usage.output_tokens if response.usage else 0
        )
        
        # Calculate cost
        cost = self._calculate_cost(usage, model)
        
        # Create metadata
        metadata = {
            "model": model,
            "finish_reason": finish_reason,
            "response_id": response.id if hasattr(response, 'id') else None,
            "role": response.role if hasattr(response, 'role') else "assistant"
        }
        
        return LLMResponse.create(
            provider=self.name,
            model=model,
            response=content,
            usage=usage,
            cost=cost,
            metadata=metadata,
            finish_reason=finish_reason
        )

    async def _handle_streaming_response(self, api_params: Dict[str, Any], model: str) -> AsyncGenerator[str, None]:
        """Handle streaming Anthropic response."""
        try:
            async with self.client.messages.stream(**api_params) as stream:
                accumulated_tokens = 0
                async for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, 'text'):
                            content = event.delta.text
                            accumulated_tokens += len(content.split())  # Rough token count
                            yield content
                    elif event.type == "message_stop":
                        # Stream has ended
                        break
                        
        except Exception as e:
            self.logger.error(f"Error in streaming response: {e}")
            yield f"[ERROR: {str(e)}]"

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check specific to Anthropic."""
        health = await super().health_check()
        
        if health["status"] == "healthy":
            try:
                # Test with a minimal request
                response = await self.client.messages.create(
                    model=self.default_model or "claude-3-haiku-20240307",
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=5
                )
                
                if response.content and len(response.content) > 0:
                    health["api_response_time"] = "< 1s"  # You could measure this
                    test_content = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
                    health["test_response"] = test_content[:50]
                else:
                    health["status"] = "unhealthy"
                    health["error"] = "No response content received"
                    
            except Exception as e:
                health["status"] = "error"
                health["error"] = f"Health check failed: {str(e)}"
        
        return health

    def get_model_names(self) -> List[str]:
        """Get list of available model names."""
        return list(self.models.keys())

    def get_recommended_model(self, task_type: str = "general") -> str:
        """Get recommended model based on task type."""
        recommendations = {
            "general": "claude-3-5-sonnet-20241022",
            "code": "claude-3-5-sonnet-20241022",
            "fast": "claude-3-haiku-20240307",
            "analysis": "claude-3-opus-20240229",
            "creative": "claude-3-opus-20240229",
            "cost_effective": "claude-3-haiku-20240307"
        }
        
        return recommendations.get(task_type, self.default_model or "claude-3-5-sonnet-20241022")
