"""Google AI Provider for Sutra Multi-LLM Prompt Studio."""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import google.generativeai as genai
from google.generativeai.types import GenerationConfig, HarmBlockThreshold, HarmCategory

from .base_provider import BaseLLMProvider, LLMResponse, ModelCapability, ModelInfo, TokenUsage


class GoogleProvider(BaseLLMProvider):
    """Google Gemini provider implementation with real API integration."""

    def __init__(self):
        super().__init__("Google")
        self._configured = False

    @property
    def provider_name(self) -> str:
        """Get the official provider name."""
        return "Google AI"

    def _get_available_models(self) -> Dict[str, ModelInfo]:
        """Get available Google Gemini models with current pricing."""
        return {
            "gemini-1.5-pro": ModelInfo(
                name="gemini-1.5-pro",
                display_name="Gemini 1.5 Pro",
                max_tokens=8192,
                cost_per_input_token=0.00125,  # $0.00125 per 1K tokens (up to 128K)
                cost_per_output_token=0.005,  # $0.005 per 1K tokens
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.STREAMING,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.IMAGE_ANALYSIS,
                    ModelCapability.JSON_MODE,
                ],
                context_window=1048576,  # 1M tokens
                supports_streaming=True,
            ),
            "gemini-1.5-flash": ModelInfo(
                name="gemini-1.5-flash",
                display_name="Gemini 1.5 Flash",
                max_tokens=8192,
                cost_per_input_token=0.000075,  # $0.000075 per 1K tokens (up to 128K)
                cost_per_output_token=0.0003,  # $0.0003 per 1K tokens
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.STREAMING,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.IMAGE_ANALYSIS,
                    ModelCapability.JSON_MODE,
                ],
                context_window=1048576,  # 1M tokens
                supports_streaming=True,
            ),
            "gemini-pro": ModelInfo(
                name="gemini-pro",
                display_name="Gemini Pro",
                max_tokens=8192,
                cost_per_input_token=0.0005,  # $0.0005 per 1K tokens
                cost_per_output_token=0.0015,  # $0.0015 per 1K tokens
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.STREAMING,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.JSON_MODE,
                ],
                context_window=32768,
                supports_streaming=True,
            ),
        }

    async def initialize(self, kv_client) -> bool:
        """Initialize Google provider with API client."""
        if not await super().initialize(kv_client):
            return False

        try:
            # Configure Google AI
            genai.configure(api_key=self.api_key)
            self._configured = True

            # Set default model
            if not self.default_model:
                self.default_model = "gemini-1.5-flash"  # Use Flash as default for cost efficiency

            self.logger.info(
                f"Google AI configured with API key ending in: ...{self.api_key[-4:] if self.api_key else 'None'}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to configure Google AI: {e}")
            return False

    def _calculate_cost(self, usage: TokenUsage, model: str) -> float:
        """Calculate cost based on token usage and model pricing."""
        if model not in self.models:
            return 0.0

        model_info = self.models[model]
        input_cost = (usage.prompt_tokens / 1000) * model_info.cost_per_input_token
        output_cost = (usage.completion_tokens / 1000) * model_info.cost_per_output_token
        return input_cost + output_cost

    def _get_safety_settings(self) -> Dict[HarmCategory, HarmBlockThreshold]:
        """Get safety settings for Google AI."""
        return {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

    async def _execute_request(
        self, prompt: str, model: str, context: Dict[str, Any], stream: bool = False
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """Execute the actual Google AI API request."""
        if not self._configured:
            raise RuntimeError("Google AI not configured")

        try:
            # Get the model instance
            model_instance = genai.GenerativeModel(model)

            # Prepare generation config
            generation_config = GenerationConfig(
                max_output_tokens=context.get("max_tokens", self.models[model].max_tokens),
                temperature=context.get("temperature", 0.7),
            )

            # Add JSON mode if requested
            if context.get("response_format") == "json":
                generation_config.response_mime_type = "application/json"

            # Prepare the prompt with system instruction if provided
            system_prompt = context.get("system_prompt")
            if system_prompt:
                model_instance = genai.GenerativeModel(model, system_instruction=system_prompt)

            # Get safety settings
            safety_settings = self._get_safety_settings()

            if stream:
                return self._handle_streaming_response(model_instance, prompt, generation_config, safety_settings, model)
            else:
                return await self._handle_standard_response(model_instance, prompt, generation_config, safety_settings, model)

        except Exception as e:
            self.logger.error(f"Unexpected error in Google AI request: {e}")
            raise RuntimeError(f"Google AI request failed: {str(e)}")

    async def _handle_standard_response(
        self, model_instance, prompt: str, generation_config: GenerationConfig, safety_settings: Dict, model: str
    ) -> LLMResponse:
        """Handle non-streaming Google AI response."""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model_instance.generate_content(
                    prompt, generation_config=generation_config, safety_settings=safety_settings
                ),
            )

            # Extract response data
            content = response.text if response.text else ""
            finish_reason = response.candidates[0].finish_reason.name if response.candidates else "UNKNOWN"

            # Create usage object (Google AI doesn't provide detailed token counts in free tier)
            # We'll estimate based on text length
            prompt_tokens = len(prompt.split())
            completion_tokens = len(content.split())

            usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            )

            # Calculate cost
            cost = self._calculate_cost(usage, model)

            # Create metadata
            metadata = {
                "model": model,
                "finish_reason": finish_reason,
                "safety_ratings": [],
                "usage_metadata": response.usage_metadata._pb if hasattr(response, "usage_metadata") else None,
            }

            # Add safety ratings if available
            if response.candidates and response.candidates[0].safety_ratings:
                metadata["safety_ratings"] = [
                    {"category": rating.category.name, "probability": rating.probability.name}
                    for rating in response.candidates[0].safety_ratings
                ]

            return LLMResponse.create(
                provider=self.name,
                model=model,
                response=content,
                usage=usage,
                cost=cost,
                metadata=metadata,
                finish_reason=finish_reason,
            )

        except Exception as e:
            self.logger.error(f"Error in Google AI standard response: {e}")
            raise RuntimeError(f"Google AI response failed: {str(e)}")

    async def _handle_streaming_response(
        self, model_instance, prompt: str, generation_config: GenerationConfig, safety_settings: Dict, model: str
    ) -> AsyncGenerator[str, None]:
        """Handle streaming Google AI response."""
        try:
            # Google AI streaming needs to be wrapped for async
            def generate_stream():
                return model_instance.generate_content(
                    prompt, generation_config=generation_config, safety_settings=safety_settings, stream=True
                )

            stream = await asyncio.get_event_loop().run_in_executor(None, generate_stream)

            accumulated_tokens = 0
            for chunk in stream:
                if chunk.text:
                    content = chunk.text
                    accumulated_tokens += len(content.split())  # Rough token count
                    yield content

        except Exception as e:
            self.logger.error(f"Error in streaming response: {e}")
            yield f"[ERROR: {str(e)}]"

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check specific to Google AI."""
        health = await super().health_check()

        if health["status"] == "healthy":
            try:
                # Test with a minimal request
                model_instance = genai.GenerativeModel(self.default_model or "gemini-pro")

                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: model_instance.generate_content("ping", generation_config=GenerationConfig(max_output_tokens=5)),
                )

                if response.text:
                    health["api_response_time"] = "< 1s"  # You could measure this
                    health["test_response"] = response.text[:50]
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
            "general": "gemini-1.5-flash",
            "code": "gemini-1.5-pro",
            "fast": "gemini-1.5-flash",
            "analysis": "gemini-1.5-pro",
            "creative": "gemini-1.5-pro",
            "cost_effective": "gemini-1.5-flash",
        }

        return recommendations.get(task_type, self.default_model or "gemini-1.5-flash")
