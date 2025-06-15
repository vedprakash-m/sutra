import azure.functions as func
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

from ..shared.auth import verify_jwt_token, get_user_id_from_token
from ..shared.database import get_database_manager
from ..shared.models import Collection, ValidationError
from ..shared.validation import validate_collection_data
from ..shared.error_handling import handle_api_error, SutraAPIError

# Initialize logging
logger = logging.getLogger(__name__)

async def main(req: func.HttpRequest) -> func.HttpResponse:
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
        # Verify authentication
        auth_result = verify_jwt_token(req)
        if not auth_result['valid']:
            return func.HttpResponse(
                json.dumps({'error': 'Unauthorized', 'message': auth_result['message']}),
                status_code=401,
                mimetype='application/json'
            )
        
        user_id = get_user_id_from_token(req)
        method = req.method
        route_params = req.route_params
        collection_id = route_params.get('id')
        
        # Route to appropriate handler
        if method == 'GET':
            if collection_id:
                if req.url.endswith('/prompts'):
                    return await get_collection_prompts(user_id, collection_id, req)
                else:
                    return await get_collection(user_id, collection_id)
            else:
                return await list_collections(user_id, req)
        elif method == 'POST':
            return await create_collection(user_id, req)
        elif method == 'PUT' and collection_id:
            return await update_collection(user_id, collection_id, req)
        elif method == 'DELETE' and collection_id:
            return await delete_collection(user_id, collection_id)
        else:
            return func.HttpResponse(
                json.dumps({'error': 'Method not allowed'}),
                status_code=405,
                mimetype='application/json'
            )
            
    except Exception as e:
        return handle_api_error(e)


async def list_collections(user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """List collections for the authenticated user with pagination and filtering."""
    try:
        # Parse query parameters
        params = req.params
        page = int(params.get('page', 1))
        limit = min(int(params.get('limit', 20)), 100)  # Max 100 items
        collection_type = params.get('type')  # private, shared_team, public_marketplace
        search = params.get('search', '').strip()
        team_id = params.get('teamId')
        
        db_manager = get_database_manager()
        
        # Build query
        query_parts = ["SELECT * FROM c WHERE c.ownerId = @user_id"]
        query_params = [{"name": "@user_id", "value": user_id}]
        
        # Add filters
        if collection_type:
            query_parts.append("AND c.type = @type")
            query_params.append({"name": "@type", "value": collection_type})
            
        if team_id:
            query_parts.append("AND c.teamId = @team_id")
            query_params.append({"name": "@team_id", "value": team_id})
            
        if search:
            query_parts.append("AND (CONTAINS(LOWER(c.name), LOWER(@search)) OR CONTAINS(LOWER(c.description), LOWER(@search)))")
            query_params.append({"name": "@search", "value": search})
        
        # Add ordering and pagination
        query_parts.append("ORDER BY c.updatedAt DESC")
        query_parts.append(f"OFFSET {(page - 1) * limit} LIMIT {limit}")
        
        query = " ".join(query_parts)
        
        # Execute query
        items = await db_manager.query_items(
            container_name='Collections',
            query=query,
            parameters=query_params
        )
        
        # Get total count for pagination
        count_query = "SELECT VALUE COUNT(1) FROM c WHERE c.ownerId = @user_id"
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
            container_name='Collections',
            query=count_query,
            parameters=count_params
        )
        
        # Handle development mode where we get mock data
        if count_result and isinstance(count_result[0], dict) and '_mock' in count_result[0]:
            total_count = 2  # Mock count for development
        else:
            total_count = count_result[0] if count_result else 0
        
        total_pages = (total_count + limit - 1) // limit
        
        response_data = {
            'collections': items,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_count': total_count,
                'limit': limit,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }
        
        return func.HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        raise SutraAPIError(f"Failed to list collections: {str(e)}", 500)


async def create_collection(user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """Create a new collection."""
    try:
        # Parse request body
        try:
            body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({'error': 'Invalid JSON in request body'}),
                status_code=400,
                mimetype='application/json'
            )
        
        # Validate required fields
        validation_result = validate_collection_data(body)
        if not validation_result['valid']:
            return func.HttpResponse(
                json.dumps({'error': 'Validation failed', 'details': validation_result['errors']}),
                status_code=400,
                mimetype='application/json'
            )
        
        # Create collection object
        collection_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + 'Z'
        
        collection_data = {
            'id': collection_id,
            'ownerId': user_id,
            'name': body['name'],
            'description': body.get('description', ''),
            'type': body.get('type', 'private'),
            'teamId': body.get('teamId'),
            'permissions': body.get('permissions', {}),
            'createdAt': now,
            'updatedAt': now
        }
        
        # Validate collection object
        try:
            collection = Collection(**collection_data)
        except ValidationError as e:
            return func.HttpResponse(
                json.dumps({'error': 'Invalid collection data', 'details': str(e)}),
                status_code=400,
                mimetype='application/json'
            )
        
        # Save to database
        client = get_cosmos_client()
        container = client.get_container('Collections')
        
        created_item = container.create_item(collection_data)
        
        logger.info(f"Created collection {collection_id} for user {user_id}")
        
        return func.HttpResponse(
            json.dumps(created_item, default=str),
            status_code=201,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error creating collection: {str(e)}")
        raise SutraAPIError(f"Failed to create collection: {str(e)}", 500)


async def get_collection(user_id: str, collection_id: str) -> func.HttpResponse:
    """Get a specific collection by ID."""
    try:
        client = get_cosmos_client()
        container = client.get_container('Collections')
        
        # Query for the collection
        query = "SELECT * FROM c WHERE c.id = @collection_id AND c.ownerId = @user_id"
        parameters = [
            {"name": "@collection_id", "value": collection_id},
            {"name": "@user_id", "value": user_id}
        ]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return func.HttpResponse(
                json.dumps({'error': 'Collection not found'}),
                status_code=404,
                mimetype='application/json'
            )
        
        collection = items[0]
        
        return func.HttpResponse(
            json.dumps(collection, default=str),
            status_code=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error getting collection {collection_id}: {str(e)}")
        raise SutraAPIError(f"Failed to get collection: {str(e)}", 500)


async def update_collection(user_id: str, collection_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """Update an existing collection."""
    try:
        # Parse request body
        try:
            body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({'error': 'Invalid JSON in request body'}),
                status_code=400,
                mimetype='application/json'
            )
        
        client = get_cosmos_client()
        container = client.get_container('Collections')
        
        # Get existing collection
        query = "SELECT * FROM c WHERE c.id = @collection_id AND c.ownerId = @user_id"
        parameters = [
            {"name": "@collection_id", "value": collection_id},
            {"name": "@user_id", "value": user_id}
        ]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return func.HttpResponse(
                json.dumps({'error': 'Collection not found'}),
                status_code=404,
                mimetype='application/json'
            )
        
        existing_collection = items[0]
        
        # Update fields
        updatable_fields = ['name', 'description', 'type', 'teamId', 'permissions']
        for field in updatable_fields:
            if field in body:
                existing_collection[field] = body[field]
        
        existing_collection['updatedAt'] = datetime.utcnow().isoformat() + 'Z'
        
        # Validate updated collection
        validation_result = validate_collection_data(existing_collection)
        if not validation_result['valid']:
            return func.HttpResponse(
                json.dumps({'error': 'Validation failed', 'details': validation_result['errors']}),
                status_code=400,
                mimetype='application/json'
            )
        
        # Update in database
        updated_item = container.replace_item(
            item=existing_collection['id'],
            body=existing_collection
        )
        
        logger.info(f"Updated collection {collection_id} for user {user_id}")
        
        return func.HttpResponse(
            json.dumps(updated_item, default=str),
            status_code=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error updating collection {collection_id}: {str(e)}")
        raise SutraAPIError(f"Failed to update collection: {str(e)}", 500)


async def delete_collection(user_id: str, collection_id: str) -> func.HttpResponse:
    """Delete a collection."""
    try:
        client = get_cosmos_client()
        container = client.get_container('Collections')
        
        # Check if collection exists and belongs to user
        query = "SELECT * FROM c WHERE c.id = @collection_id AND c.ownerId = @user_id"
        parameters = [
            {"name": "@collection_id", "value": collection_id},
            {"name": "@user_id", "value": user_id}
        ]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return func.HttpResponse(
                json.dumps({'error': 'Collection not found'}),
                status_code=404,
                mimetype='application/json'
            )
        
        # Check if collection has prompts
        prompts_container = client.get_container('Prompts')
        prompts_query = "SELECT VALUE COUNT(1) FROM c WHERE c.collectionId = @collection_id"
        prompts_params = [{"name": "@collection_id", "value": collection_id}]
        
        prompt_count = list(prompts_container.query_items(
            query=prompts_query,
            parameters=prompts_params,
            enable_cross_partition_query=True
        ))[0]
        
        if prompt_count > 0:
            return func.HttpResponse(
                json.dumps({
                    'error': 'Cannot delete collection',
                    'message': f'Collection contains {prompt_count} prompts. Move or delete prompts first.'
                }),
                status_code=409,
                mimetype='application/json'
            )
        
        # Delete collection
        container.delete_item(item=collection_id, partition_key=collection_id)
        
        logger.info(f"Deleted collection {collection_id} for user {user_id}")
        
        return func.HttpResponse(
            json.dumps({'message': 'Collection deleted successfully'}),
            status_code=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error deleting collection {collection_id}: {str(e)}")
        raise SutraAPIError(f"Failed to delete collection: {str(e)}", 500)


async def get_collection_prompts(user_id: str, collection_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """Get prompts within a specific collection."""
    try:
        # Parse query parameters
        params = req.params
        page = int(params.get('page', 1))
        limit = min(int(params.get('limit', 20)), 100)
        search = params.get('search', '').strip()
        tags = params.get('tags', '').strip()
        
        client = get_cosmos_client()
        
        # Verify user has access to collection
        collections_container = client.get_container('Collections')
        collection_query = "SELECT * FROM c WHERE c.id = @collection_id AND c.ownerId = @user_id"
        collection_params = [
            {"name": "@collection_id", "value": collection_id},
            {"name": "@user_id", "value": user_id}
        ]
        
        collections = list(collections_container.query_items(
            query=collection_query,
            parameters=collection_params,
            enable_cross_partition_query=True
        ))
        
        if not collections:
            return func.HttpResponse(
                json.dumps({'error': 'Collection not found'}),
                status_code=404,
                mimetype='application/json'
            )
        
        # Get prompts in collection
        prompts_container = client.get_container('Prompts')
        
        # Build query
        query_parts = ["SELECT * FROM c WHERE c.collectionId = @collection_id"]
        query_params = [{"name": "@collection_id", "value": collection_id}]
        
        # Add filters
        if search:
            query_parts.append("AND (CONTAINS(LOWER(c.name), LOWER(@search)) OR CONTAINS(LOWER(c.description), LOWER(@search)))")
            query_params.append({"name": "@search", "value": search})
        
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
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
        prompts = list(prompts_container.query_items(
            query=query,
            parameters=query_params,
            enable_cross_partition_query=True
        ))
        
        # Get total count
        count_query = "SELECT VALUE COUNT(1) FROM c WHERE c.collectionId = @collection_id"
        count_params = [{"name": "@collection_id", "value": collection_id}]
        
        if search:
            count_query += " AND (CONTAINS(LOWER(c.name), LOWER(@search)) OR CONTAINS(LOWER(c.description), LOWER(@search)))"
            count_params.append({"name": "@search", "value": search})
        
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            tag_conditions = []
            for i, tag in enumerate(tag_list):
                param_name = f"@tag{i}"
                tag_conditions.append(f"ARRAY_CONTAINS(c.tags, {param_name})")
                count_params.append({"name": param_name, "value": tag})
            count_query += f" AND ({' OR '.join(tag_conditions)})"
        
        total_count = list(prompts_container.query_items(
            query=count_query,
            parameters=count_params,
            enable_cross_partition_query=True
        ))[0]
        
        total_pages = (total_count + limit - 1) // limit
        
        response_data = {
            'collection': collections[0],
            'prompts': prompts,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_count': total_count,
                'limit': limit,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }
        
        return func.HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error getting collection prompts: {str(e)}")
        raise SutraAPIError(f"Failed to get collection prompts: {str(e)}", 500)
