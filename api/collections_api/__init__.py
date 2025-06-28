import azure.functions as func
import json

import sys
import os

# Add the root directory to Python path for proper imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import uuid

# NEW: Use unified authentication and validation systems
from shared.unified_auth import auth_required, get_user_from_request
from shared.utils.fieldConverter import convert_snake_to_camel, convert_camel_to_snake
from shared.utils.schemaValidator import validate_entity
from shared.real_time_cost import get_cost_manager
from shared.database import get_database_manager
from shared.models import Collection, ValidationError, User
from shared.error_handling import handle_api_error, SutraAPIError

# Initialize logging
logger = logging.getLogger(__name__)


@auth_required(permissions=["collections.read", "collections.create", "collections.update", "collections.delete"])
async def main(req: func.HttpRequest, user: User) -> func.HttpResponse:
    """
    Collections API endpoint for managing prompt collections.

    Supports:
    - GET /api/collections - List user's collections
    - POST /api/collections - Create new collection
    - GET /api/collections/{id} - Get specific collection
    - PUT /api/collections/{id} - Update collection
    - DELETE /api/collections/{id} - Delete collection
    - GET /api/collections/{id}/prompts - Get prompts in collection
    """
    try:
        # User is automatically injected by the auth decorator
        user_id = user.id
        method = req.method
        route_params = req.route_params
        collection_id = route_params.get("id")

        # Track API cost
        cost_manager = get_cost_manager()
        await cost_manager.track_api_usage(user_id, "collections", method.lower())

        # Route to appropriate handler
        if method == "GET":
            if collection_id:
                if req.url.endswith("/prompts"):
                    return await get_collection_prompts(user, collection_id, req)
                else:
                    return await get_collection(user, collection_id)
            else:
                return await list_collections(user, req)
        elif method == "POST":
            return await create_collection(user, req)
        elif method == "PUT" and collection_id:
            return await update_collection(user, collection_id, req)
        elif method == "DELETE" and collection_id:
            return await delete_collection(user, collection_id)
        else:
            return func.HttpResponse(
                json.dumps({"error": "Method not allowed"}),
                status_code=405,
                mimetype="application/json",
            )

    except Exception as e:
        return handle_api_error(e)


async def list_collections(user: User, req: func.HttpRequest) -> func.HttpResponse:
    """List collections for the authenticated user with pagination and filtering."""
    try:
        user_id = user.id
        # Parse query parameters
        params = req.params
        page = int(params.get("page", 1))
        limit = min(int(params.get("limit", 20)), 100)  # Max 100 items
        collection_type = params.get("type")  # private, shared_team, public_marketplace
        search = params.get("search", "").strip()
        team_id = params.get("teamId")

        db_manager = get_database_manager()

        # Build query - note: database uses userId to match partition key
        query_parts = ["SELECT * FROM c WHERE c.userId = @user_id"]
        query_params = [{"name": "@user_id", "value": user_id}]

        # Add filters
        if collection_type:
            query_parts.append("AND c.type = @type")
            query_params.append({"name": "@type", "value": collection_type})

        if team_id:
            query_parts.append("AND c.teamId = @team_id")
            query_params.append({"name": "@team_id", "value": team_id})

        if search:
            query_parts.append(
                "AND (CONTAINS(LOWER(c.name), LOWER(@search)) OR CONTAINS(LOWER(c.description), LOWER(@search)))"
            )
            query_params.append({"name": "@search", "value": search})

        # Add ordering and pagination
        query_parts.append("ORDER BY c.updatedAt DESC")
        query_parts.append(f"OFFSET {(page - 1) * limit} LIMIT {limit}")

        query = " ".join(query_parts)

        # Execute query
        items = await db_manager.query_items(
            container_name="Collections", query=query, parameters=query_params
        )

        # Get total count for pagination
        count_query = "SELECT VALUE COUNT(1) FROM c WHERE c.userId = @user_id"
        count_params = [{"name": "@user_id", "value": user_id}]

        if collection_type:
            count_query += " AND c.type = @type"
            count_params.append({"name": "@type", "value": collection_type})

        if team_id:
            count_query += " AND c.teamId = @team_id"
            count_params.append({"name": "@team_id", "value": team_id})

        if search:
            count_query += " AND (CONTAINS(LOWER(c.name), LOWER(@search)) OR CONTAINS(LOWER(c.description), LOWER(@search)))"
            count_params.append({"name": "@search", "value": search})

        count_result = await db_manager.query_items(
            container_name="Collections", query=count_query, parameters=count_params
        )

        # Handle development mode where we get mock data
        if (
            count_result
            and isinstance(count_result[0], dict)
            and "_mock" in count_result[0]
        ):
            total_count = 2  # Mock count for development
        else:
            total_count = count_result[0] if count_result else 0

        total_pages = (total_count + limit - 1) // limit

        response_data = {
            "collections": items,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_count": total_count,
                "limit": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }

        # Convert response to camelCase for frontend
        camel_response = convert_snake_to_camel(response_data)

        return func.HttpResponse(
            json.dumps(camel_response, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        raise SutraAPIError(f"Failed to list collections: {str(e)}", 500)


async def create_collection(user: User, req: func.HttpRequest) -> func.HttpResponse:
    """Create a new collection."""
    try:
        user_id = user.id
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

        # Convert request from camelCase to snake_case
        snake_body = convert_camel_to_snake(body)

        # Validate using centralized schema validation
        validation_result = validate_entity(snake_body, "collection")
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

        # Create collection object
        collection_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Use consistent database field names throughout
        collection_data = {
            "id": collection_id,
            "userId": user_id,  # Consistent with database partition key
            "name": snake_body["name"],
            "description": snake_body.get("description", ""),
            "type": snake_body.get("type", "private"),  # private, shared_team, public_marketplace
            "tags": snake_body.get("tags", []),
            "promptIds": [],  # Array of prompt IDs in this collection
            "teamId": body.get("teamId"),  # For shared_team collections
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
            "ownerId": user_id,  # For backward compatibility, same as userId
        }

        # Save to database
        created_item = await db_manager.create_item(
            container_name="Collections",
            item=collection_data,
            partition_key=user_id
        )

        logger.info(f"Created collection {collection_id} for user {user_id}")

        # Convert response to camelCase for frontend
        camel_response = convert_snake_to_camel(created_item)

        return func.HttpResponse(
            json.dumps(camel_response, default=str),
            status_code=201,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error creating collection: {str(e)}")
        raise SutraAPIError(f"Failed to create collection: {str(e)}", 500)


async def get_collection(user: User, collection_id: str) -> func.HttpResponse:
    """Get a specific collection by ID."""
    try:
        user_id = user.id
        db_manager = get_database_manager()

        # Query for the collection
        query = "SELECT * FROM c WHERE c.id = @collection_id AND c.userId = @user_id"
        parameters = [
            {"name": "@collection_id", "value": collection_id},
            {"name": "@user_id", "value": user_id},
        ]

        items = await db_manager.query_items(
            container_name="Collections", query=query, parameters=parameters
        )

        if not items:
            return func.HttpResponse(
                json.dumps({"error": "Collection not found"}),
                status_code=404,
                mimetype="application/json",
            )

        collection = items[0]

        # Convert response to camelCase for frontend
        camel_response = convert_snake_to_camel(collection)

        return func.HttpResponse(
            json.dumps(camel_response, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error getting collection {collection_id}: {str(e)}")
        raise SutraAPIError(f"Failed to get collection: {str(e)}", 500)


async def update_collection(
    user: User, collection_id: str, req: func.HttpRequest
) -> func.HttpResponse:
    """Update an existing collection."""
    try:
        user_id = user.id
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

        # Get existing collection
        query = "SELECT * FROM c WHERE c.id = @collection_id AND c.ownerId = @user_id"
        parameters = [
            {"name": "@collection_id", "value": collection_id},
            {"name": "@user_id", "value": user_id},
        ]

        items = await db_manager.query_items(
            container_name="Collections", query=query, parameters=parameters
        )

        if not items:
            return func.HttpResponse(
                json.dumps({"error": "Collection not found"}),
                status_code=404,
                mimetype="application/json",
            )

        existing_collection = items[0]

        # Update in database using patch operations
        update_operations = []

        # Update fields
        updatable_fields = ["name", "description", "type", "teamId", "permissions"]
        for field in updatable_fields:
            if field in body:
                existing_collection[field] = body[field]
                update_operations.append({
                    "op": "replace",
                    "path": f"/{field}",
                    "value": body[field]
                })

        # Always update the updatedAt timestamp
        updated_at = datetime.now(timezone.utc).isoformat()
        existing_collection["updatedAt"] = updated_at
        update_operations.append({
            "op": "replace",
            "path": "/updatedAt",
            "value": updated_at
        })

        # Validate updated collection
        validation_result = validate_collection_data(existing_collection)
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

        # Update in database
        updated_item = await db_manager.update_item(
            container_name="Collections",
            item_id=collection_id,
            partition_key=user_id,
            operations=update_operations
        )

        logger.info(f"Updated collection {collection_id} for user {user_id}")

        return func.HttpResponse(
            json.dumps(updated_item, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error updating collection {collection_id}: {str(e)}")
        raise SutraAPIError(f"Failed to update collection: {str(e)}", 500)


async def delete_collection(user: User, collection_id: str) -> func.HttpResponse:
    """Delete a collection."""
    try:
        user_id = user.id
        db_manager = get_database_manager()

        # Check if collection exists and belongs to user
        query = "SELECT * FROM c WHERE c.id = @collection_id AND c.userId = @user_id"
        parameters = [
            {"name": "@collection_id", "value": collection_id},
            {"name": "@user_id", "value": user_id},
        ]

        items = await db_manager.query_items(
            container_name="Collections", query=query, parameters=parameters
        )

        if not items:
            return func.HttpResponse(
                json.dumps({"error": "Collection not found"}),
                status_code=404,
                mimetype="application/json",
            )

        # Check if collection has prompts
        prompts_query = (
            "SELECT VALUE COUNT(1) FROM c WHERE c.collectionId = @collection_id"
        )
        prompts_params = [{"name": "@collection_id", "value": collection_id}]

        prompt_count_result = await db_manager.query_items(
            container_name="Prompts", query=prompts_query, parameters=prompts_params
        )
        prompt_count = prompt_count_result[0] if prompt_count_result else 0

        if prompt_count > 0:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "Cannot delete collection",
                        "message": f"Collection contains {prompt_count} prompts. Move or delete prompts first.",
                    }
                ),
                status_code=409,
                mimetype="application/json",
            )

        # Delete collection
        await db_manager.delete_item(
            container_name="Collections",
            item_id=collection_id,
            partition_key=user_id,
        )

        logger.info(f"Deleted collection {collection_id} for user {user_id}")

        return func.HttpResponse(
            json.dumps({"message": "Collection deleted successfully"}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error deleting collection {collection_id}: {str(e)}")
        raise SutraAPIError(f"Failed to delete collection: {str(e)}", 500)


async def get_collection_prompts(
    user: User, collection_id: str, req: func.HttpRequest
) -> func.HttpResponse:
    """Get prompts within a specific collection."""
    try:
        user_id = user.id
        # Parse query parameters
        params = req.params
        page = int(params.get("page", 1))
        limit = min(int(params.get("limit", 20)), 100)
        search = params.get("search", "").strip()
        tags = params.get("tags", "").strip()

        db_manager = get_database_manager()

        # Verify user has access to collection
        collection_query = (
            "SELECT * FROM c WHERE c.id = @collection_id AND c.ownerId = @user_id"
        )
        collection_params = [
            {"name": "@collection_id", "value": collection_id},
            {"name": "@user_id", "value": user_id},
        ]

        collections = await db_manager.query_items(
            container_name="Collections",
            query=collection_query,
            parameters=collection_params,
        )

        if not collections:
            return func.HttpResponse(
                json.dumps({"error": "Collection not found"}),
                status_code=404,
                mimetype="application/json",
            )

        # Get prompts in collection
        # Build query
        query_parts = ["SELECT * FROM c WHERE c.collectionId = @collection_id"]
        query_params = [{"name": "@collection_id", "value": collection_id}]

        # Add filters
        if search:
            query_parts.append(
                "AND (CONTAINS(LOWER(c.name), LOWER(@search)) OR CONTAINS(LOWER(c.description), LOWER(@search)))"
            )
            query_params.append({"name": "@search", "value": search})

        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            tag_conditions = []
            for i, tag in enumerate(tag_list):
                param_name = f"@tag{i}"
                tag_conditions.append(f"ARRAY_CONTAINS(c.tags, {param_name})")
                query_params.append({"name": param_name, "value": tag})
            query_parts.append(f"AND ({' OR '.join(tag_conditions)})")

        # Add ordering and pagination
        query_parts.append("ORDER BY c.updatedAt DESC")
        query_parts.append(f"OFFSET {(page - 1) * limit} LIMIT {limit}")

        query = " ".join(query_parts)

        # Execute query
        prompts = await db_manager.query_items(
            container_name="Prompts", query=query, parameters=query_params
        )

        # Get total count
        count_query = (
            "SELECT VALUE COUNT(1) FROM c WHERE c.collectionId = @collection_id"
        )
        count_params = [{"name": "@collection_id", "value": collection_id}]

        if search:
            count_query += " AND (CONTAINS(LOWER(c.name), LOWER(@search)) OR CONTAINS(LOWER(c.description), LOWER(@search)))"
            count_params.append({"name": "@search", "value": search})

        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            tag_conditions = []
            for i, tag in enumerate(tag_list):
                param_name = f"@tag{i}"
                tag_conditions.append(f"ARRAY_CONTAINS(c.tags, {param_name})")
                count_params.append({"name": param_name, "value": tag})
            count_query += f" AND ({' OR '.join(tag_conditions)})"

        total_count_result = await db_manager.query_items(
            container_name="Prompts", query=count_query, parameters=count_params
        )
        total_count = total_count_result[0] if total_count_result else 0

        total_pages = (total_count + limit - 1) // limit

        response_data = {
            "collection": collections[0],
            "prompts": prompts,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_count": total_count,
                "limit": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }

        return func.HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Error getting collection prompts: {str(e)}")
        raise SutraAPIError(f"Failed to get collection prompts: {str(e)}", 500)
