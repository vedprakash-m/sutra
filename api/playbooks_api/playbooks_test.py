import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

import azure.functions as func
from api.playbooks_api import main as playbooks_main


class TestPlaybooksAPI:
    """Test suite for Playbooks API endpoints."""
    
    @pytest.fixture
    def mock_auth_success(self):
        """Mock successful authentication."""
        with patch('api.shared.auth.verify_jwt_token') as mock_verify, \
             patch('api.shared.auth.get_user_id_from_token') as mock_user_id:
            mock_verify.return_value = {'valid': True}
            mock_user_id.return_value = 'test-user-123'
            yield
    
    @pytest.fixture
    def mock_cosmos_client(self):
        """Mock Cosmos DB client."""
        with patch('api.shared.database.get_cosmos_client') as mock_client:
            mock_container = Mock()
            mock_client.return_value.get_container.return_value = mock_container
            yield mock_container
    
    @pytest.mark.asyncio
    async def test_create_playbook_success(self, mock_auth_success, mock_cosmos_client):
        """Test successful playbook creation."""
        # Arrange
        playbook_data = {
            'name': 'Test Playbook',
            'description': 'A test playbook for automation',
            'visibility': 'private',
            'initialInputVariables': {
                'customer_name': {
                    'type': 'string',
                    'label': 'Customer Name',
                    'required': True
                }
            },
            'steps': [
                {
                    'stepId': 'step1',
                    'type': 'prompt',
                    'promptText': 'Hello {{customer_name}}',
                    'config': {
                        'llm': 'gpt-4',
                        'temperature': 0.7
                    }
                }
            ]
        }
        
        mock_cosmos_client.create_item.return_value = {
            'id': 'test-playbook-id',
            **playbook_data,
            'creatorId': 'test-user-123',
            'createdAt': '2025-06-15T10:00:00Z',
            'updatedAt': '2025-06-15T10:00:00Z'
        }
        
        # Mock validation
        with patch('api.shared.validation.validate_playbook_data') as mock_validate:
            mock_validate.return_value = {'valid': True, 'errors': []}
            
            # Create request
            req = func.HttpRequest(
                method='POST',
                url='http://localhost/api/playbooks',
                body=json.dumps(playbook_data).encode(),
                headers={'Content-Type': 'application/json'},
                route_params={}
            )
            
            # Act
            response = await playbooks_main(req)
            
            # Assert
            assert response.status_code == 201
            response_data = json.loads(response.get_body())
            assert response_data['name'] == 'Test Playbook'
            assert response_data['creatorId'] == 'test-user-123'
            assert len(response_data['steps']) == 1
            mock_cosmos_client.create_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_playbooks_success(self, mock_auth_success, mock_cosmos_client):
        """Test successful playbook listing."""
        # Arrange
        mock_playbooks = [
            {
                'id': 'playbook-1',
                'name': 'Playbook 1',
                'creatorId': 'test-user-123',
                'visibility': 'private',
                'createdAt': '2025-06-15T09:00:00Z'
            },
            {
                'id': 'playbook-2',
                'name': 'Playbook 2',
                'creatorId': 'test-user-123',
                'visibility': 'shared',
                'createdAt': '2025-06-15T10:00:00Z'
            }
        ]
        
        # Mock database responses
        mock_cosmos_client.query_items.side_effect = [
            mock_playbooks,  # First call for items
            [2]  # Second call for count
        ]
        
        # Create request
        req = func.HttpRequest(
            method='GET',
            url='http://localhost/api/playbooks?page=1&limit=20',
            body=b'',
            headers={},
            route_params={},
            params={'page': '1', 'limit': '20'}
        )
        
        # Act
        response = await playbooks_main(req)
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert len(response_data['playbooks']) == 2
        assert response_data['pagination']['total_count'] == 2
    
    @pytest.mark.asyncio
    async def test_run_playbook_success(self, mock_auth_success, mock_cosmos_client):
        """Test successful playbook execution."""
        # Arrange
        playbook_id = 'test-playbook-123'
        playbook = {
            'id': playbook_id,
            'name': 'Test Playbook',
            'creatorId': 'test-user-123',
            'initialInputVariables': {
                'customer_name': {'type': 'string', 'required': True}
            },
            'steps': [
                {
                    'stepId': 'step1',
                    'type': 'prompt',
                    'promptText': 'Hello {{customer_name}}'
                }
            ]
        }
        
        execution_input = {
            'initialInputs': {
                'customer_name': 'John Doe'
            }
        }
        
        # Mock database responses
        mock_cosmos_client.query_items.return_value = [playbook]
        mock_cosmos_client.create_item.return_value = {
            'id': 'execution-123',
            'playbookId': playbook_id,
            'userId': 'test-user-123',
            'status': 'running',
            'initialInputs': execution_input['initialInputs']
        }
        
        # Mock async execution
        with patch('asyncio.create_task') as mock_task:
            # Create request
            req = func.HttpRequest(
                method='POST',
                url=f'http://localhost/api/playbooks/{playbook_id}/run',
                body=json.dumps(execution_input).encode(),
                headers={'Content-Type': 'application/json'},
                route_params={'id': playbook_id}
            )
            
            # Act
            response = await playbooks_main(req)
            
            # Assert
            assert response.status_code == 202
            response_data = json.loads(response.get_body())
            assert response_data['status'] == 'running'
            assert 'executionId' in response_data
            mock_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_playbook_missing_inputs(self, mock_auth_success, mock_cosmos_client):
        """Test playbook execution with missing required inputs."""
        # Arrange
        playbook_id = 'test-playbook-123'
        playbook = {
            'id': playbook_id,
            'name': 'Test Playbook',
            'creatorId': 'test-user-123',
            'initialInputVariables': {
                'customer_name': {'type': 'string', 'required': True},
                'product_name': {'type': 'string', 'required': True}
            }
        }
        
        execution_input = {
            'initialInputs': {
                'customer_name': 'John Doe'
                # Missing required product_name
            }
        }
        
        mock_cosmos_client.query_items.return_value = [playbook]
        
        # Create request
        req = func.HttpRequest(
            method='POST',
            url=f'http://localhost/api/playbooks/{playbook_id}/run',
            body=json.dumps(execution_input).encode(),
            headers={'Content-Type': 'application/json'},
            route_params={'id': playbook_id}
        )
        
        # Act
        response = await playbooks_main(req)
        
        # Assert
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert 'Missing required input' in response_data['error']
        assert 'product_name' in response_data['message']
    
    @pytest.mark.asyncio
    async def test_get_execution_status_success(self, mock_auth_success, mock_cosmos_client):
        """Test successful execution status retrieval."""
        # Arrange
        execution_id = 'execution-123'
        execution = {
            'id': execution_id,
            'playbookId': 'playbook-123',
            'userId': 'test-user-123',
            'status': 'completed',
            'startTime': '2025-06-15T10:00:00Z',
            'endTime': '2025-06-15T10:05:00Z',
            'stepLogs': [
                {
                    'stepId': 'step1',
                    'status': 'completed',
                    'outputPreview': {
                        'text': 'Generated output',
                        'llm': 'gpt-4'
                    }
                }
            ]
        }
        
        mock_cosmos_client.query_items.return_value = [execution]
        
        # Create request - simulating executions route
        req = func.HttpRequest(
            method='GET',
            url=f'http://localhost/api/playbooks/executions/{execution_id}',
            body=b'',
            headers={},
            route_params={'execution_id': execution_id}
        )
        
        # Mock the URL check
        req.url = f'http://localhost/api/playbooks/executions/{execution_id}'
        
        # Act
        response = await playbooks_main(req)
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data['id'] == execution_id
        assert response_data['status'] == 'completed'
        assert len(response_data['stepLogs']) == 1
    
    @pytest.mark.asyncio
    async def test_continue_execution_success(self, mock_auth_success, mock_cosmos_client):
        """Test successful execution continuation after manual review."""
        # Arrange
        execution_id = 'execution-123'
        execution = {
            'id': execution_id,
            'playbookId': 'playbook-123',
            'userId': 'test-user-123',
            'status': 'paused_for_review',
            'stepLogs': [
                {
                    'stepId': 'step1',
                    'status': 'paused',
                    'outputPreview': {'text': 'Generated output'}
                }
            ],
            'auditTrail': []
        }
        
        playbook = {
            'id': 'playbook-123',
            'steps': []
        }
        
        continue_data = {
            'editedOutput': 'Manual edited output'
        }
        
        # Mock database responses
        mock_cosmos_client.query_items.side_effect = [
            [execution],  # Get execution
            [playbook]    # Get playbook for resumption
        ]
        mock_cosmos_client.replace_item.return_value = execution
        
        # Mock async resumption
        with patch('asyncio.create_task') as mock_task:
            # Create request - simulating continue route
            req = func.HttpRequest(
                method='POST',
                url=f'http://localhost/api/playbooks/executions/{execution_id}/continue',
                body=json.dumps(continue_data).encode(),
                headers={'Content-Type': 'application/json'},
                route_params={'execution_id': execution_id}
            )
            
            # Mock the URL check
            req.url = f'http://localhost/api/playbooks/executions/{execution_id}/continue'
            
            # Act
            response = await playbooks_main(req)
            
            # Assert
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data['status'] == 'running'
            assert 'continued' in response_data['message'].lower()
            mock_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_continue_execution_invalid_status(self, mock_auth_success, mock_cosmos_client):
        """Test execution continuation with invalid status."""
        # Arrange
        execution_id = 'execution-123'
        execution = {
            'id': execution_id,
            'playbookId': 'playbook-123',
            'userId': 'test-user-123',
            'status': 'completed',  # Not paused for review
            'stepLogs': [],
            'auditTrail': []
        }
        
        mock_cosmos_client.query_items.return_value = [execution]
        
        # Create request
        req = func.HttpRequest(
            method='POST',
            url=f'http://localhost/api/playbooks/executions/{execution_id}/continue',
            body=json.dumps({}).encode(),
            headers={'Content-Type': 'application/json'},
            route_params={'execution_id': execution_id}
        )
        
        # Mock the URL check
        req.url = f'http://localhost/api/playbooks/executions/{execution_id}/continue'
        
        # Act
        response = await playbooks_main(req)
        
        # Assert
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert 'Invalid status' in response_data['error']
        assert 'not paused for review' in response_data['message']
    
    @pytest.mark.asyncio
    async def test_delete_playbook_with_active_executions(self, mock_auth_success, mock_cosmos_client):
        """Test playbook deletion when there are active executions."""
        # Arrange
        playbook_id = 'test-playbook-123'
        playbook = {
            'id': playbook_id,
            'name': 'Test Playbook',
            'creatorId': 'test-user-123'
        }
        
        # Mock database responses
        mock_cosmos_client.query_items.side_effect = [
            [playbook],  # Playbook exists
            [2]          # 2 active executions
        ]
        
        # Create request
        req = func.HttpRequest(
            method='DELETE',
            url=f'http://localhost/api/playbooks/{playbook_id}',
            body=b'',
            headers={},
            route_params={'id': playbook_id}
        )
        
        # Act
        response = await playbooks_main(req)
        
        # Assert
        assert response.status_code == 409
        response_data = json.loads(response.get_body())
        assert 'Cannot delete playbook' in response_data['error']
        assert '2 active executions' in response_data['message']
        mock_cosmos_client.delete_item.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_playbook_success(self, mock_auth_success, mock_cosmos_client):
        """Test successful playbook update."""
        # Arrange
        playbook_id = 'test-playbook-123'
        existing_playbook = {
            'id': playbook_id,
            'name': 'Old Name',
            'creatorId': 'test-user-123',
            'visibility': 'private',
            'steps': [],
            'createdAt': '2025-06-15T09:00:00Z',
            'updatedAt': '2025-06-15T09:00:00Z'
        }
        
        update_data = {
            'name': 'Updated Playbook Name',
            'description': 'Updated description',
            'steps': [
                {
                    'stepId': 'new_step',
                    'type': 'prompt',
                    'promptText': 'New step content'
                }
            ]
        }
        
        mock_cosmos_client.query_items.return_value = [existing_playbook]
        mock_cosmos_client.replace_item.return_value = {
            **existing_playbook,
            **update_data,
            'updatedAt': '2025-06-15T10:00:00Z'
        }
        
        # Mock validation
        with patch('api.shared.validation.validate_playbook_data') as mock_validate:
            mock_validate.return_value = {'valid': True, 'errors': []}
            
            # Create request
            req = func.HttpRequest(
                method='PUT',
                url=f'http://localhost/api/playbooks/{playbook_id}',
                body=json.dumps(update_data).encode(),
                headers={'Content-Type': 'application/json'},
                route_params={'id': playbook_id}
            )
            
            # Act
            response = await playbooks_main(req)
            
            # Assert
            assert response.status_code == 200
            response_data = json.loads(response.get_body())
            assert response_data['name'] == 'Updated Playbook Name'
            assert response_data['description'] == 'Updated description'
            assert len(response_data['steps']) == 1
            mock_cosmos_client.replace_item.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])
