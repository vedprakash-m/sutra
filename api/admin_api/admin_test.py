import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

import azure.functions as func
from api.admin_api import main as admin_main


class TestAdminAPI:
    """Test suite for Admin API endpoints."""
    
    @pytest.fixture
    def mock_admin_auth(self):
        """Mock successful admin authentication."""
        with patch('api.shared.auth.verify_jwt_token') as mock_verify, \
             patch('api.shared.auth.get_user_id_from_token') as mock_user_id, \
             patch('api.shared.auth.check_admin_role') as mock_admin:
            mock_verify.return_value = {'valid': True}
            mock_user_id.return_value = 'admin-user-123'
            mock_admin.return_value = True
            yield
    
    @pytest.fixture
    def mock_non_admin_auth(self):
        """Mock successful authentication but non-admin user."""
        with patch('api.shared.auth.verify_jwt_token') as mock_verify, \
             patch('api.shared.auth.get_user_id_from_token') as mock_user_id, \
             patch('api.shared.auth.check_admin_role') as mock_admin:
            mock_verify.return_value = {'valid': True}
            mock_user_id.return_value = 'regular-user-123'
            mock_admin.return_value = False
            yield
    
    @pytest.fixture
    def mock_cosmos_client(self):
        """Mock Cosmos DB client."""
        with patch('api.shared.database.get_cosmos_client') as mock_client:
            mock_container = Mock()
            mock_client.return_value.get_container.return_value = mock_container
            yield mock_container
    
    @pytest.mark.asyncio
    async def test_list_users_success(self, mock_admin_auth, mock_cosmos_client):
        """Test successful user listing by admin."""
        # Arrange
        mock_users = [
            {
                'id': 'user-1',
                'email': 'user1@example.com',
                'name': 'User One',
                'role': 'member',
                'createdAt': '2025-06-15T09:00:00Z',
                'llmApiKeys': {
                    'openai': 'kv-ref-key',
                    'google_gemini': {'enabled': True, 'status': 'active'}
                }
            },
            {
                'id': 'user-2',
                'email': 'user2@example.com',
                'name': 'User Two',
                'role': 'contributor',
                'createdAt': '2025-06-15T10:00:00Z'
            }
        ]
        
        # Mock database responses
        mock_cosmos_client.query_items.side_effect = [
            mock_users,  # Users list
            [2]          # Count
        ]
        
        # Create request
        req = func.HttpRequest(
            method='GET',
            url='http://localhost/api/admin/users?page=1&limit=50',
            body=b'',
            headers={},
            route_params={'resource': 'users'},
            params={'page': '1', 'limit': '50'}
        )
        
        # Act
        response = await admin_main(req)
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert len(response_data['users']) == 2
        assert response_data['pagination']['total_count'] == 2
        
        # Check that API keys are masked
        user1 = response_data['users'][0]
        assert 'llmApiKeys' in user1
        assert user1['llmApiKeys']['openai']['enabled'] == True
        assert 'kv-ref-key' not in str(user1['llmApiKeys'])
    
    @pytest.mark.asyncio
    async def test_update_user_role_success(self, mock_admin_auth, mock_cosmos_client):
        """Test successful user role update by admin."""
        # Arrange
        target_user_id = 'user-123'
        existing_user = {
            'id': target_user_id,
            'email': 'user@example.com',
            'name': 'Test User',
            'role': 'member',
            'createdAt': '2025-06-15T09:00:00Z'
        }
        
        new_role_data = {'role': 'contributor'}
        
        mock_cosmos_client.query_items.return_value = [existing_user]
        mock_cosmos_client.replace_item.return_value = {
            **existing_user,
            'role': 'contributor',
            'updatedAt': '2025-06-15T10:00:00Z'
        }
        
        # Create request
        req = func.HttpRequest(
            method='PUT',
            url=f'http://localhost/api/admin/users/{target_user_id}/role',
            body=json.dumps(new_role_data).encode(),
            headers={'Content-Type': 'application/json'},
            route_params={
                'resource': 'users',
                'user_id': target_user_id,
                'action': 'role'
            }
        )
        
        # Act
        response = await admin_main(req)
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data['newRole'] == 'contributor'
        assert response_data['oldRole'] == 'member'
        assert response_data['userId'] == target_user_id
        mock_cosmos_client.replace_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_role_invalid_role(self, mock_admin_auth, mock_cosmos_client):
        """Test user role update with invalid role."""
        # Arrange
        target_user_id = 'user-123'
        invalid_role_data = {'role': 'invalid_role'}
        
        # Create request
        req = func.HttpRequest(
            method='PUT',
            url=f'http://localhost/api/admin/users/{target_user_id}/role',
            body=json.dumps(invalid_role_data).encode(),
            headers={'Content-Type': 'application/json'},
            route_params={
                'resource': 'users',
                'user_id': target_user_id,
                'action': 'role'
            }
        )
        
        # Act
        response = await admin_main(req)
        
        # Assert
        assert response.status_code == 400
        response_data = json.loads(response.get_body())
        assert 'Invalid role' in response_data['error']
        assert 'member, contributor, prompt_manager, admin' in response_data['message']
    
    @pytest.mark.asyncio
    async def test_get_system_health_success(self, mock_admin_auth, mock_cosmos_client):
        """Test successful system health check."""
        # Arrange
        # Mock successful database query
        mock_cosmos_client.query_items.return_value = [1]  # Successful query
        
        # Create request
        req = func.HttpRequest(
            method='GET',
            url='http://localhost/api/admin/system/health',
            body=b'',
            headers={},
            route_params={'resource': 'system', 'action': 'health'}
        )
        
        # Act
        response = await admin_main(req)
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data['status'] == 'healthy'
        assert response_data['components']['database']['status'] == 'healthy'
        assert response_data['components']['api']['status'] == 'healthy'
    
    @pytest.mark.asyncio
    async def test_get_system_stats_success(self, mock_admin_auth, mock_cosmos_client):
        """Test successful system statistics retrieval."""
        # Arrange
        # Mock database responses for different counts
        mock_cosmos_client.query_items.side_effect = [
            [10],  # User count
            [25],  # Prompt count
            [5],   # Collection count
            [8],   # Playbook count
            [3],   # Recent users
            [7]    # Recent prompts
        ]
        
        # Create request
        req = func.HttpRequest(
            method='GET',
            url='http://localhost/api/admin/system/stats',
            body=b'',
            headers={},
            route_params={'resource': 'system', 'action': 'stats'}
        )
        
        # Act
        response = await admin_main(req)
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data['totals']['users'] == 10
        assert response_data['totals']['prompts'] == 25
        assert response_data['totals']['collections'] == 5
        assert response_data['totals']['playbooks'] == 8
        assert response_data['recent_activity']['new_users'] == 3
        assert response_data['recent_activity']['new_prompts'] == 7
    
    @pytest.mark.asyncio
    async def test_set_maintenance_mode_enable(self, mock_admin_auth, mock_cosmos_client):
        """Test enabling maintenance mode."""
        # Arrange
        maintenance_data = {
            'enabled': True,
            'message': 'System maintenance in progress'
        }
        
        mock_cosmos_client.replace_item.return_value = {
            'id': 'maintenance_mode',
            'enabled': True,
            'message': 'System maintenance in progress',
            'setBy': 'admin-user-123'
        }
        
        # Create request
        req = func.HttpRequest(
            method='POST',
            url='http://localhost/api/admin/system/maintenance',
            body=json.dumps(maintenance_data).encode(),
            headers={'Content-Type': 'application/json'},
            route_params={'resource': 'system', 'action': 'maintenance'}
        )
        
        # Act
        response = await admin_main(req)
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data['enabled'] is True
        assert 'enabled' in response_data['message']
        assert response_data['maintenanceMessage'] == 'System maintenance in progress'
    
    @pytest.mark.asyncio
    async def test_get_llm_settings_success(self, mock_admin_auth, mock_cosmos_client):
        """Test successful LLM settings retrieval."""
        # Arrange
        llm_settings = {
            'id': 'llm_settings',
            'providers': {
                'openai': {
                    'enabled': True,
                    'priority': 1,
                    'rateLimits': {'requestsPerMinute': 60},
                    'budgetLimits': {'dailyBudget': 50.0}
                },
                'google_gemini': {
                    'enabled': True,
                    'priority': 2,
                    'rateLimits': {'requestsPerMinute': 60},
                    'budgetLimits': {'dailyBudget': 30.0}
                }
            },
            'defaultProvider': 'openai'
        }
        
        mock_cosmos_client.read_item.return_value = llm_settings
        
        # Create request
        req = func.HttpRequest(
            method='GET',
            url='http://localhost/api/admin/llm/settings',
            body=b'',
            headers={},
            route_params={'resource': 'llm', 'action': 'settings'}
        )
        
        # Act
        response = await admin_main(req)
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert 'providers' in response_data
        assert response_data['defaultProvider'] == 'openai'
        assert response_data['providers']['openai']['enabled'] is True
        assert response_data['providers']['openai']['priority'] == 1
    
    @pytest.mark.asyncio
    async def test_update_llm_settings_success(self, mock_admin_auth, mock_cosmos_client):
        """Test successful LLM settings update."""
        # Arrange
        existing_settings = {
            'id': 'llm_settings',
            'providers': {
                'openai': {'enabled': True, 'priority': 1}
            }
        }
        
        update_data = {
            'providers': {
                'openai': {
                    'enabled': True,
                    'priority': 1,
                    'budgetLimits': {'dailyBudget': 100.0}
                },
                'google_gemini': {
                    'enabled': False,
                    'priority': 2
                }
            },
            'defaultProvider': 'openai'
        }
        
        mock_cosmos_client.read_item.return_value = existing_settings
        mock_cosmos_client.replace_item.return_value = {
            **existing_settings,
            **update_data,
            'updatedAt': '2025-06-15T10:00:00Z',
            'updatedBy': 'admin-user-123'
        }
        
        # Create request
        req = func.HttpRequest(
            method='PUT',
            url='http://localhost/api/admin/llm/settings',
            body=json.dumps(update_data).encode(),
            headers={'Content-Type': 'application/json'},
            route_params={'resource': 'llm', 'action': 'settings'}
        )
        
        # Act
        response = await admin_main(req)
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data['providers']['openai']['budgetLimits']['dailyBudget'] == 100.0
        assert response_data['providers']['google_gemini']['enabled'] is False
        assert response_data['updatedBy'] == 'admin-user-123'
        mock_cosmos_client.replace_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_usage_stats_success(self, mock_admin_auth, mock_cosmos_client):
        """Test successful usage statistics retrieval."""
        # Arrange
        # Mock database responses for usage stats
        mock_cosmos_client.query_items.side_effect = [
            [15],  # Total executions
            [12],  # Successful executions
            [3],   # Failed executions
            [8]    # Active users
        ]
        
        # Create request
        req = func.HttpRequest(
            method='GET',
            url='http://localhost/api/admin/usage?period=day',
            body=b'',
            headers={},
            route_params={'resource': 'usage'},
            params={'period': 'day'}
        )
        
        # Act
        response = await admin_main(req)
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.get_body())
        assert response_data['period'] == 'day'
        assert response_data['statistics']['executions']['total'] == 15
        assert response_data['statistics']['executions']['successful'] == 12
        assert response_data['statistics']['executions']['failed'] == 3
        assert response_data['statistics']['executions']['success_rate'] == 80.0
        assert response_data['statistics']['users']['active'] == 8
    
    @pytest.mark.asyncio
    async def test_non_admin_access_forbidden(self, mock_non_admin_auth):
        """Test that non-admin users cannot access admin endpoints."""
        # Create request
        req = func.HttpRequest(
            method='GET',
            url='http://localhost/api/admin/users',
            body=b'',
            headers={},
            route_params={'resource': 'users'}
        )
        
        # Act
        response = await admin_main(req)
        
        # Assert
        assert response.status_code == 403
        response_data = json.loads(response.get_body())
        assert response_data['error'] == 'Forbidden'
        assert 'Admin privileges required' in response_data['message']
    
    @pytest.mark.asyncio
    async def test_get_system_health_database_failure(self, mock_admin_auth, mock_cosmos_client):
        """Test system health check when database is unavailable."""
        # Arrange
        # Mock database failure
        mock_cosmos_client.query_items.side_effect = Exception("Database connection failed")
        
        # Create request
        req = func.HttpRequest(
            method='GET',
            url='http://localhost/api/admin/system/health',
            body=b'',
            headers={},
            route_params={'resource': 'system', 'action': 'health'}
        )
        
        # Act
        response = await admin_main(req)
        
        # Assert
        assert response.status_code == 503
        response_data = json.loads(response.get_body())
        assert response_data['status'] == 'degraded'
        assert 'unhealthy' in response_data['components']['database']['status']
    
    @pytest.mark.asyncio
    async def test_update_user_role_user_not_found(self, mock_admin_auth, mock_cosmos_client):
        """Test user role update when user doesn't exist."""
        # Arrange
        target_user_id = 'nonexistent-user'
        new_role_data = {'role': 'contributor'}
        
        mock_cosmos_client.query_items.return_value = []  # No user found
        
        # Create request
        req = func.HttpRequest(
            method='PUT',
            url=f'http://localhost/api/admin/users/{target_user_id}/role',
            body=json.dumps(new_role_data).encode(),
            headers={'Content-Type': 'application/json'},
            route_params={
                'resource': 'users',
                'user_id': target_user_id,
                'action': 'role'
            }
        )
        
        # Act
        response = await admin_main(req)
        
        # Assert
        assert response.status_code == 404
        response_data = json.loads(response.get_body())
        assert response_data['error'] == 'User not found'


if __name__ == '__main__':
    pytest.main([__file__])
