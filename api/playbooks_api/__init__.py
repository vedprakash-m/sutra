import azure.functions as func
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid
import asyncio

from ..shared.auth import verify_jwt_token, get_user_id_from_token
from ..shared.database import get_database_manager
from ..shared.models import Playbook, PlaybookExecution, ValidationError
from ..shared.validation import validate_playbook_data
from ..shared.error_handling import handle_api_error, SutraAPIError

# Initialize logging
logger = logging.getLogger(__name__)

async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Playbooks API endpoint for managing AI workflow playbooks.
    
    Supports:
    - GET /api/playbooks - List user's playbooks
    - POST /api/playbooks - Create new playbook
    - GET /api/playbooks/{id} - Get specific playbook
    - PUT /api/playbooks/{id} - Update playbook
    - DELETE /api/playbooks/{id} - Delete playbook
    - POST /api/playbooks/{id}/run - Execute playbook
    - GET /api/playbooks/executions/{execution_id} - Get execution status
    - POST /api/playbooks/executions/{execution_id}/continue - Continue paused execution
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
        playbook_id = route_params.get('id')
        execution_id = route_params.get('execution_id')
        
        # Route to appropriate handler
        if 'executions' in req.url:
            if method == 'GET':
                return await get_execution_status(user_id, execution_id)
            elif method == 'POST' and req.url.endswith('/continue'):
                return await continue_execution(user_id, execution_id, req)
        elif method == 'GET':
            if playbook_id:
                return await get_playbook(user_id, playbook_id)
            else:
                return await list_playbooks(user_id, req)
        elif method == 'POST':
            if playbook_id and req.url.endswith('/run'):
                return await run_playbook(user_id, playbook_id, req)
            else:
                return await create_playbook(user_id, req)
        elif method == 'PUT' and playbook_id:
            return await update_playbook(user_id, playbook_id, req)
        elif method == 'DELETE' and playbook_id:
            return await delete_playbook(user_id, playbook_id)
        else:
            return func.HttpResponse(
                json.dumps({'error': 'Method not allowed'}),
                status_code=405,
                mimetype='application/json'
            )
            
    except Exception as e:
        return handle_api_error(e)


async def list_playbooks(user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """List playbooks for the authenticated user with pagination and filtering."""
    try:
        # Parse query parameters
        params = req.params
        page = int(params.get('page', 1))
        limit = min(int(params.get('limit', 20)), 100)
        visibility = params.get('visibility')  # private, shared
        search = params.get('search', '').strip()
        team_id = params.get('teamId')
        
        db_manager = get_database_manager()
        
        # Build query
        query_parts = ["SELECT * FROM c WHERE c.creatorId = @user_id"]
        query_params = [{"name": "@user_id", "value": user_id}]
        
        # Add filters
        if visibility:
            query_parts.append("AND c.visibility = @visibility")
            query_params.append({"name": "@visibility", "value": visibility})
            
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
            container_name='Playbooks',
            query=query,
            parameters=query_params
        )
        
        # Get total count for pagination
        count_query = "SELECT VALUE COUNT(1) FROM c WHERE c.creatorId = @user_id"
        count_params = [{"name": "@user_id", "value": user_id}]
        
        if visibility:
            count_query += " AND c.visibility = @visibility"
            count_params.append({"name": "@visibility", "value": visibility})
            
        if team_id:
            count_query += " AND c.teamId = @team_id"
            count_params.append({"name": "@team_id", "value": team_id})
            
        if search:
            count_query += " AND (CONTAINS(LOWER(c.name), LOWER(@search)) OR CONTAINS(LOWER(c.description), LOWER(@search)))"
            count_params.append({"name": "@search", "value": search})
        
        count_result = await db_manager.query_items(
            container_name='Playbooks',
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
            'playbooks': items,
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
        logger.error(f"Error listing playbooks: {str(e)}")
        raise SutraAPIError(f"Failed to list playbooks: {str(e)}", 500)


async def create_playbook(user_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """Create a new playbook."""
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
        validation_result = validate_playbook_data(body)
        if not validation_result['valid']:
            return func.HttpResponse(
                json.dumps({'error': 'Validation failed', 'details': validation_result['errors']}),
                status_code=400,
                mimetype='application/json'
            )
        
        # Create playbook object
        playbook_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + 'Z'
        
        playbook_data = {
            'id': playbook_id,
            'creatorId': user_id,
            'name': body['name'],
            'description': body.get('description', ''),
            'visibility': body.get('visibility', 'private'),
            'teamId': body.get('teamId'),
            'initialInputVariables': body.get('initialInputVariables', {}),
            'steps': body.get('steps', []),
            'createdAt': now,
            'updatedAt': now
        }
        
        # Validate playbook object
        try:
            playbook = Playbook(**playbook_data)
        except ValidationError as e:
            return func.HttpResponse(
                json.dumps({'error': 'Invalid playbook data', 'details': str(e)}),
                status_code=400,
                mimetype='application/json'
            )
        
        # Save to database
        db_manager = get_database_manager()
        container = client.get_container('Playbooks')
        
        created_item = container.create_item(playbook_data)
        
        logger.info(f"Created playbook {playbook_id} for user {user_id}")
        
        return func.HttpResponse(
            json.dumps(created_item, default=str),
            status_code=201,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error creating playbook: {str(e)}")
        raise SutraAPIError(f"Failed to create playbook: {str(e)}", 500)


async def get_playbook(user_id: str, playbook_id: str) -> func.HttpResponse:
    """Get a specific playbook by ID."""
    try:
        db_manager = get_database_manager()
        container = client.get_container('Playbooks')
        
        # Query for the playbook
        query = "SELECT * FROM c WHERE c.id = @playbook_id AND c.creatorId = @user_id"
        parameters = [
            {"name": "@playbook_id", "value": playbook_id},
            {"name": "@user_id", "value": user_id}
        ]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return func.HttpResponse(
                json.dumps({'error': 'Playbook not found'}),
                status_code=404,
                mimetype='application/json'
            )
        
        playbook = items[0]
        
        return func.HttpResponse(
            json.dumps(playbook, default=str),
            status_code=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error getting playbook {playbook_id}: {str(e)}")
        raise SutraAPIError(f"Failed to get playbook: {str(e)}", 500)


async def update_playbook(user_id: str, playbook_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """Update an existing playbook."""
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
        
        db_manager = get_database_manager()
        container = client.get_container('Playbooks')
        
        # Get existing playbook
        query = "SELECT * FROM c WHERE c.id = @playbook_id AND c.creatorId = @user_id"
        parameters = [
            {"name": "@playbook_id", "value": playbook_id},
            {"name": "@user_id", "value": user_id}
        ]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return func.HttpResponse(
                json.dumps({'error': 'Playbook not found'}),
                status_code=404,
                mimetype='application/json'
            )
        
        existing_playbook = items[0]
        
        # Update fields
        updatable_fields = ['name', 'description', 'visibility', 'teamId', 'initialInputVariables', 'steps']
        for field in updatable_fields:
            if field in body:
                existing_playbook[field] = body[field]
        
        existing_playbook['updatedAt'] = datetime.utcnow().isoformat() + 'Z'
        
        # Validate updated playbook
        validation_result = validate_playbook_data(existing_playbook)
        if not validation_result['valid']:
            return func.HttpResponse(
                json.dumps({'error': 'Validation failed', 'details': validation_result['errors']}),
                status_code=400,
                mimetype='application/json'
            )
        
        # Update in database
        updated_item = container.replace_item(
            item=existing_playbook['id'],
            body=existing_playbook
        )
        
        logger.info(f"Updated playbook {playbook_id} for user {user_id}")
        
        return func.HttpResponse(
            json.dumps(updated_item, default=str),
            status_code=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error updating playbook {playbook_id}: {str(e)}")
        raise SutraAPIError(f"Failed to update playbook: {str(e)}", 500)


async def delete_playbook(user_id: str, playbook_id: str) -> func.HttpResponse:
    """Delete a playbook."""
    try:
        db_manager = get_database_manager()
        container = client.get_container('Playbooks')
        
        # Check if playbook exists and belongs to user
        query = "SELECT * FROM c WHERE c.id = @playbook_id AND c.creatorId = @user_id"
        parameters = [
            {"name": "@playbook_id", "value": playbook_id},
            {"name": "@user_id", "value": user_id}
        ]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return func.HttpResponse(
                json.dumps({'error': 'Playbook not found'}),
                status_code=404,
                mimetype='application/json'
            )
        
        # Check if playbook has active executions
        executions_container = client.get_container('PlaybookExecutions')
        exec_query = "SELECT VALUE COUNT(1) FROM c WHERE c.playbookId = @playbook_id AND c.status IN ('running', 'paused_for_review')"
        exec_params = [{"name": "@playbook_id", "value": playbook_id}]
        
        active_count = list(executions_container.query_items(
            query=exec_query,
            parameters=exec_params,
            enable_cross_partition_query=True
        ))[0]
        
        if active_count > 0:
            return func.HttpResponse(
                json.dumps({
                    'error': 'Cannot delete playbook',
                    'message': f'Playbook has {active_count} active executions. Stop executions first.'
                }),
                status_code=409,
                mimetype='application/json'
            )
        
        # Delete playbook
        container.delete_item(item=playbook_id, partition_key=playbook_id)
        
        logger.info(f"Deleted playbook {playbook_id} for user {user_id}")
        
        return func.HttpResponse(
            json.dumps({'message': 'Playbook deleted successfully'}),
            status_code=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error deleting playbook {playbook_id}: {str(e)}")
        raise SutraAPIError(f"Failed to delete playbook: {str(e)}", 500)


async def run_playbook(user_id: str, playbook_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """Execute a playbook (async)."""
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
        
        db_manager = get_database_manager()
        
        # Get playbook
        playbooks_container = client.get_container('Playbooks')
        query = "SELECT * FROM c WHERE c.id = @playbook_id AND c.creatorId = @user_id"
        parameters = [
            {"name": "@playbook_id", "value": playbook_id},
            {"name": "@user_id", "value": user_id}
        ]
        
        items = list(playbooks_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return func.HttpResponse(
                json.dumps({'error': 'Playbook not found'}),
                status_code=404,
                mimetype='application/json'
            )
        
        playbook = items[0]
        initial_inputs = body.get('initialInputs', {})
        
        # Validate initial inputs against playbook requirements
        required_inputs = playbook.get('initialInputVariables', {})
        for var_name, var_config in required_inputs.items():
            if var_name not in initial_inputs and var_config.get('required', True):
                return func.HttpResponse(
                    json.dumps({
                        'error': 'Missing required input',
                        'message': f'Required input variable "{var_name}" not provided'
                    }),
                    status_code=400,
                    mimetype='application/json'
                )
        
        # Create execution record
        execution_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + 'Z'
        
        execution_data = {
            'id': execution_id,
            'playbookId': playbook_id,
            'userId': user_id,
            'status': 'running',
            'startTime': now,
            'initialInputs': initial_inputs,
            'stepLogs': [],
            'auditTrail': [
                {
                    'action': 'playbook_started',
                    'userId': user_id,
                    'timestamp': now
                }
            ]
        }
        
        # Save execution record
        executions_container = client.get_container('PlaybookExecutions')
        created_execution = executions_container.create_item(execution_data)
        
        # Start async execution (simplified for MVP)
        # In production, this would use Azure Service Bus or Functions orchestration
        asyncio.create_task(execute_playbook_steps(execution_id, playbook, initial_inputs))
        
        logger.info(f"Started playbook execution {execution_id} for playbook {playbook_id}")
        
        return func.HttpResponse(
            json.dumps({
                'executionId': execution_id,
                'status': 'running',
                'message': 'Playbook execution started'
            }),
            status_code=202,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error running playbook {playbook_id}: {str(e)}")
        raise SutraAPIError(f"Failed to run playbook: {str(e)}", 500)


async def get_execution_status(user_id: str, execution_id: str) -> func.HttpResponse:
    """Get real-time status and logs of a playbook execution."""
    try:
        db_manager = get_database_manager()
        container = client.get_container('PlaybookExecutions')
        
        # Query for the execution
        query = "SELECT * FROM c WHERE c.id = @execution_id AND c.userId = @user_id"
        parameters = [
            {"name": "@execution_id", "value": execution_id},
            {"name": "@user_id", "value": user_id}
        ]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return func.HttpResponse(
                json.dumps({'error': 'Execution not found'}),
                status_code=404,
                mimetype='application/json'
            )
        
        execution = items[0]
        
        return func.HttpResponse(
            json.dumps(execution, default=str),
            status_code=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error getting execution status {execution_id}: {str(e)}")
        raise SutraAPIError(f"Failed to get execution status: {str(e)}", 500)


async def continue_execution(user_id: str, execution_id: str, req: func.HttpRequest) -> func.HttpResponse:
    """Continue a paused playbook after manual review."""
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
        
        db_manager = get_database_manager()
        container = client.get_container('PlaybookExecutions')
        
        # Get execution
        query = "SELECT * FROM c WHERE c.id = @execution_id AND c.userId = @user_id"
        parameters = [
            {"name": "@execution_id", "value": execution_id},
            {"name": "@user_id", "value": user_id}
        ]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return func.HttpResponse(
                json.dumps({'error': 'Execution not found'}),
                status_code=404,
                mimetype='application/json'
            )
        
        execution = items[0]
        
        if execution['status'] != 'paused_for_review':
            return func.HttpResponse(
                json.dumps({
                    'error': 'Invalid status',
                    'message': f'Execution is not paused for review. Current status: {execution["status"]}'
                }),
                status_code=400,
                mimetype='application/json'
            )
        
        # Update execution to continue
        now = datetime.utcnow().isoformat() + 'Z'
        execution['status'] = 'running'
        execution['auditTrail'].append({
            'action': 'manual_review_approved',
            'userId': user_id,
            'timestamp': now
        })
        
        # Apply any manual edits to the current step
        if 'editedOutput' in body:
            # Find the current paused step and update it
            for step_log in execution['stepLogs']:
                if step_log.get('status') == 'paused':
                    if 'manualReview' not in step_log:
                        step_log['manualReview'] = {}
                    step_log['manualReview']['reviewerId'] = user_id
                    step_log['manualReview']['reviewedAt'] = now
                    step_log['manualReview']['editedOutput'] = body['editedOutput']
                    break
        
        # Update in database
        updated_execution = container.replace_item(
            item=execution['id'],
            body=execution
        )
        
        # Resume execution
        playbooks_container = client.get_container('Playbooks')
        playbook_query = "SELECT * FROM c WHERE c.id = @playbook_id"
        playbook_params = [{"name": "@playbook_id", "value": execution['playbookId']}]
        
        playbook_items = list(playbooks_container.query_items(
            query=playbook_query,
            parameters=playbook_params,
            enable_cross_partition_query=True
        ))
        
        if playbook_items:
            asyncio.create_task(resume_playbook_execution(execution_id, playbook_items[0], execution))
        
        logger.info(f"Continued execution {execution_id} after manual review")
        
        return func.HttpResponse(
            json.dumps({
                'message': 'Execution continued',
                'status': 'running'
            }),
            status_code=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error continuing execution {execution_id}: {str(e)}")
        raise SutraAPIError(f"Failed to continue execution: {str(e)}", 500)


async def execute_playbook_steps(execution_id: str, playbook: Dict[str, Any], initial_inputs: Dict[str, Any]):
    """Execute playbook steps asynchronously (simplified for MVP)."""
    try:
        # This is a simplified implementation for MVP
        # In production, this would use Azure Durable Functions or Service Bus
        
        db_manager = get_database_manager()
        container = client.get_container('PlaybookExecutions')
        
        # Get current execution
        execution = container.read_item(item=execution_id, partition_key=execution_id)
        
        current_variables = initial_inputs.copy()
        
        for i, step in enumerate(playbook.get('steps', [])):
            step_id = step.get('stepId', f'step_{i}')
            step_type = step.get('type', 'prompt')
            
            # Create step log
            step_log = {
                'stepId': step_id,
                'stepName': step.get('name', f'Step {i + 1}'),
                'status': 'running',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            try:
                if step_type == 'prompt':
                    # Execute prompt step (simplified)
                    step_log['input'] = {
                        'prompt_text': step.get('promptText', ''),
                        'variables': current_variables
                    }
                    
                    # Simulate LLM execution
                    await asyncio.sleep(2)  # Simulate processing time
                    
                    step_log['outputPreview'] = {
                        'llm': step.get('config', {}).get('llm', 'gpt-4'),
                        'text': f'Generated output for step {step_id}',
                        'score': 'Good'
                    }
                    step_log['status'] = 'completed'
                    step_log['durationMs'] = 2000
                    
                    # Parse output and update variables (simplified)
                    if 'variableMappings' in step:
                        for var_name, mapping in step['variableMappings'].items():
                            current_variables[var_name] = f'extracted_value_{var_name}'
                
                elif step_type == 'manual_review':
                    # Pause for manual review
                    step_log['status'] = 'paused'
                    execution['status'] = 'paused_for_review'
                    
                    # Update execution and wait for manual approval
                    execution['stepLogs'].append(step_log)
                    container.replace_item(item=execution_id, body=execution)
                    return  # Exit and wait for manual continuation
                
            except Exception as step_error:
                step_log['status'] = 'failed'
                step_log['error'] = str(step_error)
                execution['status'] = 'failed'
                break
            
            execution['stepLogs'].append(step_log)
            container.replace_item(item=execution_id, body=execution)
        
        # Mark execution as completed
        if execution['status'] != 'failed':
            execution['status'] = 'completed'
            execution['endTime'] = datetime.utcnow().isoformat() + 'Z'
        
        container.replace_item(item=execution_id, body=execution)
        
        logger.info(f"Completed playbook execution {execution_id}")
        
    except Exception as e:
        logger.error(f"Error executing playbook {execution_id}: {str(e)}")
        # Mark execution as failed
        try:
            execution = container.read_item(item=execution_id, partition_key=execution_id)
            execution['status'] = 'failed'
            execution['endTime'] = datetime.utcnow().isoformat() + 'Z'
            execution['error'] = str(e)
            container.replace_item(item=execution_id, body=execution)
        except:
            pass


async def resume_playbook_execution(execution_id: str, playbook: Dict[str, Any], execution: Dict[str, Any]):
    """Resume playbook execution after manual review."""
    try:
        # Find the last completed step and continue from there
        last_step_index = len(execution.get('stepLogs', []))
        
        # Continue execution from where it left off
        await execute_playbook_steps(execution_id, playbook, execution['initialInputs'])
        
    except Exception as e:
        logger.error(f"Error resuming playbook execution {execution_id}: {str(e)}")
