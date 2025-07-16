"""OpenAI Provider for Sutra Multi-LLM Prompt Studio."""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import openai
from openai import AsyncOpenAI

from .base_provider import BaseLLMProvider, LLMResponse, ModelCapability, ModelInfo, TokenUsage


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider implementation with real API integration."""

    def __init__(self):
        super().__init__("OpenAI")
        self.client: Optional[AsyncOpenAI] = None
        self.organization: Optional[str] = None

    @property
    def provider_name(self) -> str:
        """Get the official provider name."""
        return "OpenAI"

    def _get_available_models(self) -> Dict[str, ModelInfo]:
        """Get available OpenAI models with current pricing."""
        return {
            "gpt-4": ModelInfo(
                name="gpt-4",
                display_name="GPT-4",
                max_tokens=8192,
                cost_per_input_token=0.03,  # $0.03 per 1K tokens
                cost_per_output_token=0.06,  # $0.06 per 1K tokens
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.STREAMING,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.JSON_MODE,
                ],
                context_window=8192,
                supports_streaming=True,
            ),
            "gpt-4-1106-preview": ModelInfo(
                name="gpt-4-1106-preview",
                display_name="GPT-4 Turbo Preview",
                max_tokens=4096,
                cost_per_input_token=0.01,  # $0.01 per 1K tokens
                cost_per_output_token=0.03,  # $0.03 per 1K tokens
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.STREAMING,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.JSON_MODE,
                ],
                context_window=128000,
                supports_streaming=True,
            ),
            "gpt-4o": ModelInfo(
                name="gpt-4o",
                display_name="GPT-4o",
                max_tokens=4096,
                cost_per_input_token=0.005,  # $0.005 per 1K tokens
                cost_per_output_token=0.015,  # $0.015 per 1K tokens
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.STREAMING,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.JSON_MODE,
                    ModelCapability.IMAGE_ANALYSIS,
                ],
                context_window=128000,
                supports_streaming=True,
            ),
            "gpt-3.5-turbo": ModelInfo(
                name="gpt-3.5-turbo",
                display_name="GPT-3.5 Turbo",
                max_tokens=4096,
                cost_per_input_token=0.001,  # $0.001 per 1K tokens
                cost_per_output_token=0.002,  # $0.002 per 1K tokens
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.STREAMING,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.JSON_MODE,
                ],
                context_window=16385,
                supports_streaming=True,
            ),
        }

    async def initialize(self, kv_client) -> bool:
        """Initialize OpenAI provider with API client."""
        if not await super().initialize(kv_client):
            return False

        try:
            # Initialize OpenAI client
            self.client = AsyncOpenAI(api_key=self.api_key, organization=self.organization)

            # Set default model
            if not self.default_model:
                self.default_model = "gpt-4o"  # Use GPT-4o as default

            self.logger.info(
                f"OpenAI client initialized with API key ending in: ...{self.api_key[-4:] if self.api_key else 'None'}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
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
        self, prompt: str, model: str, context: Dict[str, Any], stream: bool = False
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """Execute the actual OpenAI API request."""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        # Prepare the messages
        messages = [{"role": "user", "content": prompt}]

        # Add system message if provided in context
        if "system_prompt" in context:
            messages.insert(0, {"role": "system", "content": context["system_prompt"]})

        # Prepare API parameters
        api_params = {
            "model": model,
            "messages": messages,
            "max_tokens": context.get("max_tokens", self.models[model].max_tokens),
            "temperature": context.get("temperature", 0.7),
            "stream": stream,
        }

        # Add JSON mode if requested and supported
        if context.get("response_format") == "json" and ModelCapability.JSON_MODE in self.models[model].capabilities:
            api_params["response_format"] = {"type": "json_object"}

        try:
            if stream:
                return self._handle_streaming_response(api_params, model)
            else:
                return await self._handle_standard_response(api_params, model)

        except openai.RateLimitError as e:
            self.logger.warning(f"OpenAI rate limit exceeded: {e}")
            raise RuntimeError(f"Rate limit exceeded. Please try again later.")

        except openai.APIError as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise RuntimeError(f"OpenAI API error: {str(e)}")

        except Exception as e:
            self.logger.error(f"Unexpected error in OpenAI request: {e}")
            raise RuntimeError(f"OpenAI request failed: {str(e)}")

    async def _handle_standard_response(self, api_params: Dict[str, Any], model: str) -> LLMResponse:
        """Handle non-streaming OpenAI response."""
        response = await self.client.chat.completions.create(**api_params)

        # Extract response data
        content = response.choices[0].message.content or ""
        finish_reason = response.choices[0].finish_reason

        # Create usage object
        usage = TokenUsage(
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
        )

        # Calculate cost
        cost = self._calculate_cost(usage, model)

        # Create metadata
        metadata = {
            "model": model,
            "finish_reason": finish_reason,
            "response_id": response.id if hasattr(response, "id") else None,
            "created": response.created if hasattr(response, "created") else None,
        }

        return LLMResponse.create(
            provider=self.name,
            model=model,
            response=content,
            usage=usage,
            cost=cost,
            metadata=metadata,
            finish_reason=finish_reason,
        )

    async def _handle_streaming_response(self, api_params: Dict[str, Any], model: str) -> AsyncGenerator[str, None]:
        """Handle streaming OpenAI response."""
        try:
            stream = await self.client.chat.completions.create(**api_params)

            accumulated_tokens = 0
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    accumulated_tokens += len(content.split())  # Rough token count
                    yield content

        except Exception as e:
            self.logger.error(f"Error in streaming response: {e}")
            yield f"[ERROR: {str(e)}]"

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check specific to OpenAI."""
        health = await super().health_check()

        if health["status"] == "healthy":
            try:
                # Test with a minimal request
                response = await self.client.chat.completions.create(
                    model=self.default_model or "gpt-3.5-turbo", messages=[{"role": "user", "content": "ping"}], max_tokens=5
                )

                if response.choices and response.choices[0].message.content:
                    health["api_response_time"] = "< 1s"  # You could measure this
                    health["test_response"] = response.choices[0].message.content[:50]
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
            "general": "gpt-4o",
            "code": "gpt-4",
            "fast": "gpt-3.5-turbo",
            "analysis": "gpt-4-1106-preview",
            "creative": "gpt-4",
            "cost_effective": "gpt-3.5-turbo",
        }

        return recommendations.get(task_type, self.default_model or "gpt-4o")
