import json
import logging

import sys
import os

# Add the root directory to Python path for proper imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import azure.functions as func
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import uuid

# Updated imports for unified auth and validation
from shared.unified_auth import require_authentication, require_permissions, auth_required
from shared.real_time_cost import get_real_time_cost_manager
from shared.database import get_database_manager
from shared.models import (
    PromptTemplate,
    PromptStatus,
    CreatePromptRequest,
    UpdatePromptRequest,
    ErrorResponse,
)
from shared.validation import PromptTemplateValidator
from shared.error_handling import (
    ValidationException,
    BusinessLogicException,
    ErrorHandler,
    handle_api_errors,
    extract_request_id,
    SutraError,
    ErrorType
)
from shared.validation import (
    validate_pagination_params,
    validate_search_query,
    validate_resource_ownership,
    RateLimitValidator,
)

# Import schema validation
try:
    from shared.utils.schemaValidator import validatePrompt, createPromptValidation
except ImportError:
    # Fallback if schema validator not available
    def validatePrompt(data, partial=False):
        return {"isValid": True, "errors": [], "data": data}
    
    def createPromptValidation(options=None):
        return lambda req, res, next: next()


@auth_required(permissions=["prompts.create", "prompts.read"])
@handle_api_errors
async def main(req: func.HttpRequest, user=None) -> func.HttpResponse:
    """Handle prompts API requests with unified auth and validation."""
    logging.info("Prompts API function processed a request.")

    request_id = extract_request_id(req)
    cost_manager = get_real_time_cost_manager()
    
    # Store user in request for consistency with existing code
    req.current_user = user

    # Route based on HTTP method
    method = req.method.upper()

    if method == "GET":
        return await handle_get_prompts(req, request_id)
    elif method == "POST":
        return await handle_create_prompt(req, request_id)
    elif method == "PUT":
        return await handle_update_prompt(req, request_id)
    elif method == "DELETE":
        return await handle_delete_prompt(req, request_id)
    else:
        return ErrorHandler.handle_not_found_error(
            "endpoint", f"{method} /prompts", request_id
        ).to_azure_response()


async def handle_get_prompts(
    req: func.HttpRequest, request_id: Optional[str] = None
) -> func.HttpResponse:
    """Handle GET requests for prompts with validation."""
    user = req.current_user
    db_manager = get_database_manager()

    # Check for specific prompt ID in the route
    prompt_id = req.route_params.get("id")

    if prompt_id:
        # Get single prompt
        prompt = await db_manager.read_item(
            container_name="Prompts", item_id=prompt_id, partition_key=user.id
        )

        if not prompt:
            return ErrorHandler.handle_not_found_error(
                "prompt", prompt_id, request_id
            ).to_azure_response()

        # Validate user can access this resource
        validate_resource_ownership(prompt.get("user_id", ""), user.id, user.roles)

        return func.HttpResponse(
            json.dumps(prompt, default=str),
            headers={"Content-Type": "application/json"},
        )

    else:
        # List prompts with validation
        query_params = dict(req.params)

        # Validate pagination parameters
        skip = int(query_params.get("skip", 0))
        limit = int(query_params.get("limit", 50))
        skip, limit = validate_pagination_params(skip, limit)

        # Validate search query
        search_query = validate_search_query(query_params.get("q", ""))

        # Validate status filter
        status = query_params.get("status")
        if status and status not in [s.value for s in PromptStatus]:
            raise ValidationException(f"Invalid status: {status}", "status")

        # Validate and process tags
        tags_param = query_params.get("tags", "")
        tags = (
            [tag.strip() for tag in tags_param.split(",") if tag.strip()]
            if tags_param
            else None
        )

        # Build query - use consistent database field names
        query = "SELECT * FROM c WHERE c.userId = @user_id"
        parameters = [{"name": "@user_id", "value": user.id}]

        if status:
            query += " AND c.status = @status"
            parameters.append({"name": "@status", "value": status})

        if search_query:
            query += " AND (CONTAINS(LOWER(c.title), LOWER(@search)) OR CONTAINS(LOWER(c.description), LOWER(@search)))"
            parameters.append({"name": "@search", "value": search_query})

        if tags:
            # Simple tag filtering - in production, this could be more sophisticated
            query += " AND ARRAY_CONTAINS(c.tags, @tag)"
            parameters.append({"name": "@tag", "value": tags[0]})

        query += f" ORDER BY c.updatedAt DESC OFFSET {skip} LIMIT {limit}"

        prompts = await db_manager.query_items(
            container_name="Prompts", query=query, parameters=parameters
        )

        return func.HttpResponse(
            json.dumps(
                {
                    "prompts": prompts,
                    "total": len(prompts),
                    "skip": skip,
                    "limit": limit,
                    "user_id": user.id,
                },
                default=str,
            ),
            headers={"Content-Type": "application/json"},
        )


async def handle_create_prompt(
    req: func.HttpRequest, request_id: Optional[str] = None
) -> func.HttpResponse:
    """Handle POST requests to create prompts."""
    try:
        user = req.current_user
        db_manager = get_database_manager()

        # Parse request body
        try:
            request_data = req.get_json()
            create_request = CreatePromptRequest(**request_data)
        except Exception as e:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "validation_error",
                        "message": "Invalid request data",
                        "details": {"error": str(e)},
                    }
                ),
                status_code=400,
                headers={"Content-Type": "application/json"},
            )

        # Create prompt template with consistent database field names
        now = datetime.now(timezone.utc)
        prompt_id = str(uuid.uuid4())

        # Create prompt data for database storage
        prompt_data = {
            "id": prompt_id,
            "userId": user.id,  # Consistent with partition key
            "title": create_request.title,
            "description": create_request.description,
            "content": create_request.content,
            "variables": create_request.variables,
            "tags": create_request.tags,
            "status": PromptStatus.DRAFT.value,
            "version": 1,
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
            "collectionId": create_request.collection_id,  # Store collection_id from request
            "creatorId": user.id,  # For backward compatibility
        }

        # Save to database
        created_prompt = await db_manager.create_item(
            container_name="Prompts",
            item=prompt_data,
            partition_key=user.id
        )

        logging.info(f"Created prompt {prompt_id} for user {user.id}")

        return func.HttpResponse(
            json.dumps(created_prompt, default=str),
            status_code=201,
            headers={"Content-Type": "application/json"},
        )
    except Exception as e:
        logging.error(f"Error creating prompt: {str(e)}")
        return func.HttpResponse(
            json.dumps(
                {"error": "internal_error", "message": "Failed to create prompt"}
            ),
            status_code=500,
            headers={"Content-Type": "application/json"},
        )


async def handle_update_prompt(req: func.HttpRequest) -> func.HttpResponse:
    """Handle PUT requests to update prompts."""
    try:
        user = req.current_user
        db_manager = get_database_manager()

        # Get prompt ID from route
        prompt_id = req.route_params.get("id")
        if not prompt_id:
            return func.HttpResponse(
                json.dumps({"error": "missing_id", "message": "Prompt ID is required"}),
                status_code=400,
                headers={"Content-Type": "application/json"},
            )

        # Parse request body
        try:
            request_data = req.get_json()
            update_request = UpdatePromptRequest(**request_data)
        except Exception as e:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "validation_error",
                        "message": "Invalid request data",
                        "details": {"error": str(e)},
                    }
                ),
                status_code=400,
                headers={"Content-Type": "application/json"},
            )

        # Get existing prompt
        existing_prompt = await db_manager.read_item(
            container_name="Prompts", item_id=prompt_id, partition_key=user.id
        )

        if not existing_prompt:
            return func.HttpResponse(
                json.dumps({"error": "not_found", "message": "Prompt not found"}),
                status_code=404,
                headers={"Content-Type": "application/json"},
            )

        # Update fields
        now = datetime.now(timezone.utc)

        # Only update provided fields
        if update_request.title is not None:
            existing_prompt["title"] = update_request.title
        if update_request.description is not None:
            existing_prompt["description"] = update_request.description
        if update_request.content is not None:
            existing_prompt["content"] = update_request.content
        if update_request.variables is not None:
            existing_prompt["variables"] = [
                var.dict() for var in update_request.variables
            ]
        if update_request.tags is not None:
            existing_prompt["tags"] = update_request.tags
        if update_request.status is not None:
            existing_prompt["status"] = update_request.status

        # Always update timestamp
        existing_prompt["updated_at"] = now.isoformat()

        # If content changed, create new version
        if update_request.content is not None:
            existing_prompt["version"] = existing_prompt.get("version", 1) + 1
            existing_prompt["parent_id"] = prompt_id  # Track version history

        # Save updated prompt
        updated_prompt = await db_manager.update_item(
            container_name="Prompts",
            item=existing_prompt,
            partition_key=user.id,
        )

        logging.info(f"Updated prompt {prompt_id} for user {user.id}")

        return func.HttpResponse(
            json.dumps(updated_prompt, default=str),
            headers={"Content-Type": "application/json"},
        )

    except Exception as e:
        logging.error(f"Error updating prompt: {str(e)}")
        error = ErrorResponse(
            error="update_error",
            message="Failed to update prompt",
            details={"error": str(e)},
        )
        return func.HttpResponse(
            error.json(), status_code=500, headers={"Content-Type": "application/json"}
        )


async def handle_delete_prompt(req: func.HttpRequest) -> func.HttpResponse:
    """Handle DELETE requests to delete prompts."""
    try:
        user = req.current_user
        db_manager = get_database_manager()

        # Get prompt ID from route
        prompt_id = req.route_params.get("id")
        if not prompt_id:
            return func.HttpResponse(
                json.dumps({"error": "missing_id", "message": "Prompt ID is required"}),
                status_code=400,
                headers={"Content-Type": "application/json"},
            )

        # Check if prompt exists and belongs to user
        existing_prompt = await db_manager.read_item(
            container_name="Prompts", item_id=prompt_id, partition_key=user.id
        )

        if not existing_prompt:
            return func.HttpResponse(
                json.dumps({"error": "not_found", "message": "Prompt not found"}),
                status_code=404,
                headers={"Content-Type": "application/json"},
            )

        # Delete the prompt
        success = await db_manager.delete_item(
            container_name="Prompts", item_id=prompt_id, partition_key=user.id
        )

        if success:
            logging.info(f"Deleted prompt {prompt_id} for user {user.id}")
            return func.HttpResponse(
                json.dumps({"message": "Prompt deleted successfully", "id": prompt_id}),
                headers={"Content-Type": "application/json"},
            )
        else:
            return func.HttpResponse(
                json.dumps(
                    {"error": "deletion_failed", "message": "Failed to delete prompt"}
                ),
                status_code=500,
                headers={"Content-Type": "application/json"},
            )

    except Exception as e:
        logging.error(f"Error deleting prompt: {str(e)}")
        error = ErrorResponse(
            error="deletion_error",
            message="Failed to delete prompt",
            details={"error": str(e)},
        )
        return func.HttpResponse(
            error.json(), status_code=500, headers={"Content-Type": "application/json"}
        )
