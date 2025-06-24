import azure.functions as func
import json

import sys
import os

# Add the root directory to Python path for proper imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncio
import httpx

from shared.auth_static_web_apps import require_auth, get_current_user
from shared.database import get_database_manager
from shared.llm_client import get_llm_client, LLMProvider
from shared.error_handling import handle_api_error, SutraAPIError

# Initialize logging
logger = logging.getLogger(__name__)


@require_auth
async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    LLM Execution API endpoint for Multi-LLM optimization and comparison.

    Supports:
    - POST /api/llm/execute - Execute prompt across multiple LLMs
    - POST /api/llm/compare - Compare outputs from different LLMs
    - GET /api/llm/providers - Get available LLM providers
    """
    try:
        # Get authenticated user from request context
        user_id = req.current_user.id
        method = req.method
        route_params = req.route_params
        action = route_params.get("action")

        # Route to appropriate handler
        if method == "POST":
            if action == "compare":
                return await compare_llm_outputs(user_id, req)
            else:
                return await execute_llm_prompt(user_id, req)
        elif method == "GET" and action == "providers":
            return await get_available_providers(user_id)
        else:
            return func.HttpResponse(
                json.dumps({"error": "Method not allowed"}),
                status_code=405,
                mimetype="application/json",
            )

    except Exception as e:
        return handle_api_error(e)


async def execute_llm_prompt(user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """Execute a prompt across multiple LLMs for comparison."""
    try:
        # Parse request body
        try:
            body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json",
            )

        # Validate required fields
        prompt_text = body.get("promptText")
        llm_providers = body.get("llms", ["openai"])
        variables = body.get("variables", {})
        output_format = body.get("outputFormat", "text")
        temperature = body.get("temperature", 0.7)
        max_tokens = body.get("maxTokens", 2000)

        if not prompt_text:
            return func.HttpResponse(
                json.dumps({"error": "promptText is required"}),
                status_code=400,
                mimetype="application/json",
            )

        # Replace variables in prompt text
        processed_prompt = prompt_text
        for var_name, var_value in variables.items():
            processed_prompt = processed_prompt.replace(
                f"{{{{{var_name}}}}}", str(var_value)
            )

        # Get user's LLM API keys
        db_manager = get_database_manager()
        users_container = db_manager.get_container("Users")

        query = "SELECT * FROM c WHERE c.id = @user_id"
        parameters = [{"name": "@user_id", "value": user_id}]

        user_items = list(
            users_container.query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            )
        )

        if not user_items:
            return func.HttpResponse(
                json.dumps({"error": "User not found"}),
                status_code=404,
                mimetype="application/json",
            )

        user_data = user_items[0]
        user_llm_keys = user_data.get("llmApiKeys", {})

        # Execute prompts in parallel across selected LLMs
        execution_tasks = []

        for provider in llm_providers:
            if provider in user_llm_keys:
                task = execute_single_llm(
                    provider=provider,
                    prompt=processed_prompt,
                    api_config=user_llm_keys[provider],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    output_format=output_format,
                )
                execution_tasks.append((provider, task))

        if not execution_tasks:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "No valid LLM providers configured",
                        "message": "Please configure API keys for the selected LLM providers",
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        # Execute all LLMs in parallel
        results = {}
        execution_start = datetime.utcnow()

        for provider, task in execution_tasks:
            try:
                result = await task
                results[provider] = result
            except Exception as e:
                results[provider] = {"error": str(e), "status": "failed"}

        execution_end = datetime.utcnow()
        total_duration = (execution_end - execution_start).total_seconds() * 1000

        # Analyze and score outputs
        analyzed_results = await analyze_llm_outputs(results, processed_prompt)

        response_data = {
            "executionId": f"exec_{int(execution_start.timestamp())}",
            "prompt": processed_prompt,
            "variables": variables,
            "llmOutputs": analyzed_results,
            "execution": {
                "startTime": execution_start.isoformat() + "Z",
                "endTime": execution_end.isoformat() + "Z",
                "totalDurationMs": int(total_duration),
                "providersExecuted": len(execution_tasks),
                "successfulProviders": len(
                    [r for r in results.values() if "error" not in r]
                ),
            },
        }

        logger.info(
            f"Executed prompt across {len(execution_tasks)} LLMs for user {user_id}"
        )

        return func.HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error executing LLM prompt: {str(e)}")
        raise SutraAPIError(f"Failed to execute LLM prompt: {str(e)}", 500)


async def execute_single_llm(
    provider: str,
    prompt: str,
    api_config: Any,
    temperature: float,
    max_tokens: int,
    output_format: str,
) -> Dict[str, Any]:
    """Execute prompt on a single LLM provider."""
    start_time = datetime.utcnow()

    try:
        # Get LLM client
        llm_client = get_llm_client(provider, api_config)

        # Execute the prompt
        response = await llm_client.complete(
            prompt=prompt, temperature=temperature, max_tokens=max_tokens
        )

        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000

        return {
            "text": response.get("text", ""),
            "model": response.get("model", ""),
            "usage": response.get("usage", {}),
            "durationMs": int(duration_ms),
            "status": "completed",
            "timestamp": end_time.isoformat() + "Z",
            "provider": provider,
        }

    except Exception as e:
        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000

        return {
            "error": str(e),
            "status": "failed",
            "durationMs": int(duration_ms),
            "timestamp": end_time.isoformat() + "Z",
            "provider": provider,
        }


async def analyze_llm_outputs(results: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    """Analyze and score LLM outputs for comparison."""
    analyzed_results = {}

    for provider, result in results.items():
        if "error" in result:
            analyzed_results[provider] = result
            continue

        # Simple analysis for MVP - in production this would be more sophisticated
        text = result.get("text", "")

        # Calculate basic metrics
        word_count = len(text.split())
        char_count = len(text)

        # Simple scoring based on length and completeness
        if word_count < 10:
            score = "Poor"
            feedback = "Response too short"
        elif word_count < 50:
            score = "Fair"
            feedback = "Brief response"
        elif word_count < 200:
            score = "Good"
            feedback = "Well-balanced response"
        else:
            score = "Excellent"
            feedback = "Comprehensive response"

        analyzed_results[provider] = {
            **result,
            "analysis": {
                "score": score,
                "feedback": feedback,
                "metrics": {
                    "word_count": word_count,
                    "character_count": char_count,
                    "estimated_reading_time": max(1, word_count // 200),  # minutes
                },
            },
        }

    return analyzed_results


async def compare_llm_outputs(user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """Compare outputs from different LLMs side by side."""
    try:
        # Parse request body
        try:
            body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json",
            )

        outputs = body.get("outputs", {})
        comparison_criteria = body.get(
            "criteria", ["quality", "relevance", "creativity"]
        )

        if len(outputs) < 2:
            return func.HttpResponse(
                json.dumps({"error": "At least 2 outputs required for comparison"}),
                status_code=400,
                mimetype="application/json",
            )

        # Perform comparison analysis
        comparison_results = {}

        for criterion in comparison_criteria:
            criterion_scores = {}

            for provider, output in outputs.items():
                if "text" in output:
                    text = output["text"]

                    # Simple scoring for MVP
                    if criterion == "quality":
                        score = min(100, len(text.split()) * 2)  # Based on length
                    elif criterion == "relevance":
                        score = 85  # Default score for MVP
                    elif criterion == "creativity":
                        # Count unique words as a proxy for creativity
                        unique_words = len(set(text.lower().split()))
                        score = min(100, unique_words * 3)
                    else:
                        score = 75  # Default score

                    criterion_scores[provider] = score

            comparison_results[criterion] = criterion_scores

        # Determine overall rankings
        overall_scores = {}
        for provider in outputs.keys():
            total_score = sum(
                comparison_results[criterion].get(provider, 0)
                for criterion in comparison_criteria
            )
            overall_scores[provider] = total_score / len(comparison_criteria)

        # Sort by score
        ranked_providers = sorted(
            overall_scores.items(), key=lambda x: x[1], reverse=True
        )

        response_data = {
            "comparison": comparison_results,
            "overall_scores": overall_scores,
            "ranking": [provider for provider, score in ranked_providers],
            "recommended": ranked_providers[0][0] if ranked_providers else None,
            "criteria": comparison_criteria,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        logger.info(f"Compared {len(outputs)} LLM outputs for user {user_id}")

        return func.HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error comparing LLM outputs: {str(e)}")
        raise SutraAPIError(f"Failed to compare LLM outputs: {str(e)}", 500)


async def get_available_providers(user_id: str) -> func.HttpResponse:
    """Get available LLM providers for the user."""
    try:
        # Get user's configured LLM providers
        db_manager = get_database_manager()
        users_container = db_manager.get_container("Users")

        query = "SELECT * FROM c WHERE c.id = @user_id"
        parameters = [{"name": "@user_id", "value": user_id}]

        user_items = list(
            users_container.query_items(
                query=query, parameters=parameters, enable_cross_partition_query=True
            )
        )

        user_llm_keys = {}
        if user_items:
            user_llm_keys = user_items[0].get("llmApiKeys", {})

        # Get system LLM settings
        system_container = db_manager.get_container("SystemConfig")
        try:
            llm_settings = system_container.read_item(
                item="llm_settings", partition_key="llm_settings"
            )
            system_providers = llm_settings.get("providers", {})
        except:
            system_providers = {}

        # Build provider list
        available_providers = []

        for provider in ["openai", "google_gemini", "anthropic"]:
            system_config = system_providers.get(provider, {})
            user_config = user_llm_keys.get(provider)

            provider_info = {
                "id": provider,
                "name": provider.replace("_", " ").title(),
                "configured": user_config is not None,
                "enabled": system_config.get("enabled", True)
                and user_config is not None,
                "priority": system_config.get("priority", 999),
                "models": get_provider_models(provider),
                "rateLimits": system_config.get("rateLimits", {}),
                "status": "available" if user_config else "requires_setup",
            }

            available_providers.append(provider_info)

        # Sort by priority
        available_providers.sort(key=lambda x: x["priority"])

        response_data = {
            "providers": available_providers,
            "defaultProvider": next(
                (p["id"] for p in available_providers if p["enabled"]), "openai"
            ),
            "totalConfigured": len([p for p in available_providers if p["configured"]]),
            "totalEnabled": len([p for p in available_providers if p["enabled"]]),
        }

        return func.HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error getting available providers: {str(e)}")
        raise SutraAPIError(f"Failed to get available providers: {str(e)}", 500)


def get_provider_models(provider: str) -> List[str]:
    """Get available models for a provider."""
    models_map = {
        "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
        "google_gemini": ["gemini-1.5-pro", "gemini-1.5-flash"],
        "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
    }
    return models_map.get(provider, [])
