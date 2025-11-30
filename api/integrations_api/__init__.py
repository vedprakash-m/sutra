import json
import logging
import os
import sys
import traceback

import azure.functions as func

# Add the root directory to Python path for proper imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from shared.database import get_database_manager
from shared.error_handling import SutraAPIError, handle_api_error
from shared.keyvault_manager import get_keyvault_manager
from shared.models import User, ValidationError
from shared.real_time_cost import get_cost_manager

# NEW: Use unified authentication and validation systems
from shared.unified_auth import require_authentication
from shared.utils.fieldConverter import convert_camel_to_snake, convert_snake_to_camel
from shared.utils.schemaValidator import validate_entity
from shared.validation import validate_llm_integration_data

# Initialize logging
logger = logging.getLogger(__name__)


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Integrations API endpoint for managing LLM provider integrations.

    Supports:
    - GET /api/integrations/llm - List user's LLM integrations
    - POST /api/integrations/llm - Add new LLM integration
    - PUT /api/integrations/llm/{provider} - Update LLM integration
    - DELETE /api/integrations/llm/{provider} - Remove LLM integration
    - POST /api/integrations/llm/{provider}/test - Test LLM connection
    """
    try:
        # Manual authentication - no decorator
        user = await require_authentication(req)
        user_id = user.id
        method = req.method
        route_params = req.route_params
        provider = route_params.get("provider")
        action = route_params.get("action")

        logger.info(f"Integrations API called by {user.email}: {method} {req.url}")

        # Route to appropriate handler
        if method == "GET":
            return await list_llm_integrations(user_id)
        elif method == "POST":
            if provider and action == "test":
                return await validate_llm_connection(user_id, provider, req)
            else:
                return await create_llm_integration(user_id, req)
        elif method == "PUT" and provider:
            return await update_llm_integration(user_id, provider, req)
        elif method == "DELETE" and provider:
            return await delete_llm_integration(user_id, provider)
        else:
            return func.HttpResponse(
                json.dumps({"error": "Method not allowed"}),
                status_code=405,
                mimetype="application/json",
            )

    except Exception as e:
        logger.error(f"Integrations API error: {str(e)}")
        logger.error(traceback.format_exc())

        # Return proper error response
        if "Authentication required" in str(e) or "401" in str(e):
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "authentication_required",
                        "message": "Please log in to access this resource",
                    }
                ),
                status_code=401,
                mimetype="application/json",
            )
        else:
            return func.HttpResponse(
                json.dumps({"error": "internal_error", "message": "An internal error occurred"}),
                status_code=500,
                mimetype="application/json",
            )


async def list_llm_integrations(user_id: str) -> func.HttpResponse:
    """List LLM integrations for the authenticated user."""
    try:
        db_manager = get_database_manager()

        # Check if database is available (development mode handling)
        if not db_manager.client:
            # Return mock data for development mode
            return func.HttpResponse(
                json.dumps(
                    {
                        "integrations": {
                            "openai": {
                                "keyRe": "***masked***",
                                "enabled": False,
                                "status": "disconnected",
                                "lastTested": None,
                            },
                            "anthropic": {
                                "keyRe": "***masked***",
                                "enabled": False,
                                "status": "disconnected",
                                "lastTested": None,
                            },
                        },
                        "supportedProviders": [
                            {
                                "id": "openai",
                                "name": "OpenAI",
                                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                                "requiresUrl": False,
                            },
                            {
                                "id": "anthropic",
                                "name": "Anthropic",
                                "models": [
                                    "claude-3-opus",
                                    "claude-3-sonnet",
                                    "claude-3-haiku",
                                ],
                                "requiresUrl": False,
                            },
                            {
                                "id": "google",
                                "name": "Google",
                                "models": ["gemini-pro", "gemini-pro-vision"],
                                "requiresUrl": False,
                            },
                        ],
                        "_mock": True,
                    }
                ),
                status_code=200,
                mimetype="application/json",
            )

        # Get user profile with LLM integrations
        query = "SELECT * FROM c WHERE c.id = @user_id"
        parameters = [{"name": "@user_id", "value": user_id}]

        items = await db_manager.query_items(container_name="Users", query=query, parameters=parameters)

        if not items:
            return func.HttpResponse(
                json.dumps({"error": "User not found"}),
                status_code=404,
                mimetype="application/json",
            )

        user = items[0]
        llm_integrations = user.get("llmApiKeys", {})

        # Return masked API keys for security
        masked_integrations = {}
        for provider, config in llm_integrations.items():
            if isinstance(config, dict):
                masked_integrations[provider] = {
                    "url": config.get("url"),
                    "keyRe": "***masked***",
                    "enabled": config.get("enabled", True),
                    "lastTested": config.get("lastTested"),
                    "status": config.get("status", "unknown"),
                }
            else:
                masked_integrations[provider] = {
                    "keyRe": "***masked***",
                    "enabled": True,
                    "status": "unknown",
                }

        response_data = {
            "integrations": masked_integrations,
            "supportedProviders": [
                {
                    "id": "openai",
                    "name": "OpenAI",
                    "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                    "requiresUrl": False,
                },
                {
                    "id": "google_gemini",
                    "name": "Google Gemini",
                    "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
                    "requiresUrl": False,
                },
                {
                    "id": "anthropic",
                    "name": "Anthropic Claude",
                    "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                    "requiresUrl": False,
                },
                {
                    "id": "custom",
                    "name": "Custom OpenAI-Compatible",
                    "models": [],
                    "requiresUrl": True,
                },
            ],
        }

        return func.HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error listing LLM integrations: {str(e)}")
        raise SutraAPIError(f"Failed to list LLM integrations: {str(e)}", 500)


async def create_llm_integration(user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """Add a new LLM integration."""
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
        validation_result = validate_llm_integration_data(body)
        if not validation_result["valid"]:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "Validation failed",
                        "details": validation_result["errors"],
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        provider = body["provider"]
        api_key = body["apiKey"]
        custom_url = body.get("url")

        # Pre-validate API key
        validation_result = await validate_llm_api_key(provider, api_key, custom_url)
        if not validation_result["valid"]:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "API key validation failed",
                        "details": validation_result["error"],
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        db_manager = get_database_manager()
        container = db_manager.get_container("Users")

        # Get user profile
        query = "SELECT * FROM c WHERE c.id = @user_id"
        parameters = [{"name": "@user_id", "value": user_id}]

        items = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

        if not items:
            # Create user profile if it doesn't exist
            now = datetime.utcnow().isoformat() + "Z"
            user_data = {
                "id": user_id,
                "email": body.get("email", ""),
                "name": body.get("name", ""),
                "llmApiKeys": {},
                "createdAt": now,
                "updatedAt": now,
            }
        else:
            user_data = items[0]

        # Store API key reference (in production, this would be stored in Azure Key Vault)
        key_ref = f"kv-ref-{provider}-{user_id[:8]}"

        if "llmApiKeys" not in user_data:
            user_data["llmApiKeys"] = {}

        if custom_url:
            user_data["llmApiKeys"][provider] = {
                "url": custom_url,
                "keyRe": key_ref,
                "enabled": True,
                "lastTested": datetime.utcnow().isoformat() + "Z",
                "status": "active",
            }
        else:
            user_data["llmApiKeys"][provider] = key_ref

        user_data["updatedAt"] = datetime.utcnow().isoformat() + "Z"

        # Save to database
        if items:
            updated_user = container.replace_item(item=user_data["id"], body=user_data)
        else:
            updated_user = container.create_item(user_data)

        # Store actual API key in Azure Key Vault for secure storage
        try:
            keyvault_manager = get_keyvault_manager()
            if keyvault_manager.key_vault_available():
                await keyvault_manager.store_api_key(user_id, provider, api_key)
                logger.info(f"Stored API key in Key Vault for user {user_id}, provider {provider}")
            else:
                logger.warning(f"Key Vault not available, API key stored in reference only for user {user_id}")
        except Exception as kv_error:
            logger.warning(f"Failed to store API key in Key Vault: {kv_error}")
            # Continue with local reference - Key Vault is optional

        logger.info(f"Added LLM integration {provider} for user {user_id}")

        return func.HttpResponse(
            json.dumps(
                {
                    "message": f"Successfully added {provider} integration",
                    "provider": provider,
                    "status": "active",
                }
            ),
            status_code=201,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error creating LLM integration: {str(e)}")
        raise SutraAPIError(f"Failed to create LLM integration: {str(e)}", 500)


async def update_llm_integration(user_id: str, provider: str, req: func.HttpRequest) -> func.HttpResponse:
    """Update an existing LLM integration."""
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

        db_manager = get_database_manager()
        container = db_manager.get_container("Users")

        # Get user profile
        query = "SELECT * FROM c WHERE c.id = @user_id"
        parameters = [{"name": "@user_id", "value": user_id}]

        items = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

        if not items:
            return func.HttpResponse(
                json.dumps({"error": "User not found"}),
                status_code=404,
                mimetype="application/json",
            )

        user_data = items[0]

        if "llmApiKeys" not in user_data or provider not in user_data["llmApiKeys"]:
            return func.HttpResponse(
                json.dumps({"error": f"Integration for {provider} not found"}),
                status_code=404,
                mimetype="application/json",
            )

        # Update integration
        if "apiKey" in body:
            # Validate new API key
            api_key = body["apiKey"]
            custom_url = body.get("url")

            validation_result = await validate_llm_api_key(provider, api_key, custom_url)
            if not validation_result["valid"]:
                return func.HttpResponse(
                    json.dumps(
                        {
                            "error": "API key validation failed",
                            "details": validation_result["error"],
                        }
                    ),
                    status_code=400,
                    mimetype="application/json",
                )

            # Update key reference
            key_ref = f"kv-ref-{provider}-{user_id[:8]}"

            if isinstance(user_data["llmApiKeys"][provider], dict):
                user_data["llmApiKeys"][provider]["keyRe"] = key_ref
                if custom_url:
                    user_data["llmApiKeys"][provider]["url"] = custom_url
                user_data["llmApiKeys"][provider]["lastTested"] = datetime.utcnow().isoformat() + "Z"
                user_data["llmApiKeys"][provider]["status"] = "active"
            else:
                user_data["llmApiKeys"][provider] = key_ref

        # Update enabled status
        if "enabled" in body:
            if isinstance(user_data["llmApiKeys"][provider], dict):
                user_data["llmApiKeys"][provider]["enabled"] = body["enabled"]

        user_data["updatedAt"] = datetime.utcnow().isoformat() + "Z"

        # Save to database
        updated_user = container.replace_item(item=user_data["id"], body=user_data)

        logger.info(f"Updated LLM integration {provider} for user {user_id}")

        return func.HttpResponse(
            json.dumps(
                {
                    "message": f"Successfully updated {provider} integration",
                    "provider": provider,
                    "status": "active",
                }
            ),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error updating LLM integration {provider}: {str(e)}")
        raise SutraAPIError(f"Failed to update LLM integration: {str(e)}", 500)


async def delete_llm_integration(user_id: str, provider: str) -> func.HttpResponse:
    """Remove an LLM integration."""
    try:
        db_manager = get_database_manager()
        container = db_manager.get_container("Users")

        # Get user profile
        query = "SELECT * FROM c WHERE c.id = @user_id"
        parameters = [{"name": "@user_id", "value": user_id}]

        items = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

        if not items:
            return func.HttpResponse(
                json.dumps({"error": "User not found"}),
                status_code=404,
                mimetype="application/json",
            )

        user_data = items[0]

        if "llmApiKeys" not in user_data or provider not in user_data["llmApiKeys"]:
            return func.HttpResponse(
                json.dumps({"error": f"Integration for {provider} not found"}),
                status_code=404,
                mimetype="application/json",
            )

        # Remove integration
        del user_data["llmApiKeys"][provider]
        user_data["updatedAt"] = datetime.utcnow().isoformat() + "Z"

        # Save to database
        updated_user = container.replace_item(item=user_data["id"], body=user_data)

        # Remove API key from Azure Key Vault
        try:
            keyvault_manager = get_keyvault_manager()
            if keyvault_manager.key_vault_available():
                await keyvault_manager.delete_api_key(user_id, provider)
                logger.info(f"Deleted API key from Key Vault for user {user_id}, provider {provider}")
        except Exception as kv_error:
            logger.warning(f"Failed to delete API key from Key Vault: {kv_error}")
            # Continue - database record is already deleted

        logger.info(f"Removed LLM integration {provider} for user {user_id}")

        return func.HttpResponse(
            json.dumps({"message": f"Successfully removed {provider} integration"}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error deleting LLM integration {provider}: {str(e)}")
        raise SutraAPIError(f"Failed to delete LLM integration: {str(e)}", 500)


async def validate_llm_connection(user_id: str, provider: str, req: func.HttpRequest) -> func.HttpResponse:
    """Test LLM connection."""
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

        api_key = body.get("apiKey")
        custom_url = body.get("url")

        if not api_key:
            return func.HttpResponse(
                json.dumps({"error": "API key required for testing"}),
                status_code=400,
                mimetype="application/json",
            )

        # Test the connection
        validation_result = await validate_llm_api_key(provider, api_key, custom_url)

        if validation_result["valid"]:
            return func.HttpResponse(
                json.dumps(
                    {
                        "valid": True,
                        "message": f"Successfully connected to {provider}",
                        "model": validation_result.get("model"),
                        "response_time_ms": validation_result.get("response_time_ms"),
                    }
                ),
                status_code=200,
                mimetype="application/json",
            )
        else:
            return func.HttpResponse(
                json.dumps({"valid": False, "error": validation_result["error"]}),
                status_code=400,
                mimetype="application/json",
            )

    except Exception as e:
        logger.error(f"Error testing LLM connection {provider}: {str(e)}")
        raise SutraAPIError(f"Failed to test LLM connection: {str(e)}", 500)


async def validate_llm_api_key(provider: str, api_key: str, custom_url: Optional[str] = None) -> Dict[str, Any]:
    """Validate LLM API key by making a lightweight test call."""
    try:
        start_time = datetime.utcnow()

        async with httpx.AsyncClient(timeout=10.0) as client:
            if provider == "openai":
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )

                if response.status_code == 200:
                    models = response.json()
                    end_time = datetime.utcnow()
                    response_time = (end_time - start_time).total_seconds() * 1000

                    return {
                        "valid": True,
                        "model": "gpt-3.5-turbo",
                        "response_time_ms": int(response_time),
                    }
                else:
                    return {
                        "valid": False,
                        "error": f"OpenAI API error: {response.status_code} - {response.text}",
                    }

            elif provider == "google_gemini":
                response = await client.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}")

                if response.status_code == 200:
                    end_time = datetime.utcnow()
                    response_time = (end_time - start_time).total_seconds() * 1000

                    return {
                        "valid": True,
                        "model": "gemini-1.5-pro",
                        "response_time_ms": int(response_time),
                    }
                else:
                    return {
                        "valid": False,
                        "error": f"Google Gemini API error: {response.status_code} - {response.text}",
                    }

            elif provider == "anthropic":
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01",
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "test"}],
                    },
                )

                if response.status_code == 200:
                    end_time = datetime.utcnow()
                    response_time = (end_time - start_time).total_seconds() * 1000

                    return {
                        "valid": True,
                        "model": "claude-3-haiku",
                        "response_time_ms": int(response_time),
                    }
                else:
                    return {
                        "valid": False,
                        "error": f"Anthropic API error: {response.status_code} - {response.text}",
                    }

            elif provider == "custom" and custom_url:
                # Test custom OpenAI-compatible endpoint
                response = await client.get(
                    f"{custom_url}/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )

                if response.status_code == 200:
                    end_time = datetime.utcnow()
                    response_time = (end_time - start_time).total_seconds() * 1000

                    return {
                        "valid": True,
                        "model": "custom",
                        "response_time_ms": int(response_time),
                    }
                else:
                    return {
                        "valid": False,
                        "error": f"Custom API error: {response.status_code} - {response.text}",
                    }

            else:
                return {"valid": False, "error": f"Unsupported provider: {provider}"}

    except asyncio.TimeoutError:
        return {
            "valid": False,
            "error": "Connection timeout - API endpoint unreachable",
        }
    except Exception as e:
        return {"valid": False, "error": f"Connection error: {str(e)}"}
