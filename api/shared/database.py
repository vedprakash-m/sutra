import json
import logging
import os
from typing import Any, Dict, Optional, Union
from azure.cosmos import CosmosClient, exceptions
from azure.cosmos.database import DatabaseProxy
from azure.cosmos.container import ContainerProxy


class DatabaseManager:
    """Manages Cosmos DB connections and operations for the Sutra application."""
    
    def __init__(self):
        self._client: Optional[CosmosClient] = None
        self._database: Optional[DatabaseProxy] = None
        self._containers: Dict[str, ContainerProxy] = {}
        
        # Check if we're in development mode
        self._development_mode = os.getenv('ENVIRONMENT') == 'development'
        
        # Get connection string from environment
        self._connection_string = os.getenv('COSMOS_DB_CONNECTION_STRING')
        if not self._connection_string and not self._development_mode:
            raise ValueError("COSMOS_DB_CONNECTION_STRING environment variable is required")
        
        self._database_name = 'sutra'
        
    @property
    def client(self) -> CosmosClient:
        """Get or create Cosmos DB client."""
        if self._development_mode:
            # Return a mock client for development
            return None
        
        if self._client is None:
            self._client = CosmosClient.from_connection_string(self._connection_string)
        return self._client
    
    @property
    def database(self) -> DatabaseProxy:
        """Get or create database proxy."""
        if self._development_mode:
            # Return None for development mode
            return None
        
        if self._database is None:
            self._database = self.client.get_database_client(self._database_name)
        return self._database
    
    def get_container(self, container_name: str) -> ContainerProxy:
        """Get or create container proxy."""
        if self._development_mode:
            # Return None for development mode
            return None
        
        if container_name not in self._containers:
            self._containers[container_name] = self.database.get_container_client(container_name)
        return self._containers[container_name]
    
    async def create_item(self, container_name: str, item: Dict[str, Any], partition_key: str) -> Dict[str, Any]:
        """Create a new item in the specified container."""
        if self._development_mode:
            # Return mock response for development
            logging.info(f"DEV MODE: Creating item in {container_name}")
            return {**item, 'id': item.get('id', 'mock-id'), '_mock': True}
        
        try:
            container = self.get_container(container_name)
            
            # Ensure partition key is set in the item
            if 'userId' in item and partition_key != item['userId']:
                item['userId'] = partition_key
            elif 'date' in item and partition_key != item['date']:
                item['date'] = partition_key
            elif 'type' in item and partition_key != item['type']:
                item['type'] = partition_key
            
            result = container.create_item(body=item, partition_key=partition_key)
            return result
            
        except exceptions.CosmosResourceExistsError:
            logging.warning(f"Item already exists in {container_name}")
            raise
        except exceptions.CosmosHttpResponseError as e:
            logging.error(f"Error creating item in {container_name}: {e}")
            raise
    
    async def read_item(self, container_name: str, item_id: str, partition_key: str) -> Optional[Dict[str, Any]]:
        """Read an item from the specified container."""
        if self._development_mode:
            # Return mock response for development
            logging.info(f"DEV MODE: Reading item {item_id} from {container_name}")
            return {'id': item_id, 'name': 'Mock Item', '_mock': True}
        
        try:
            container = self.get_container(container_name)
            result = container.read_item(item=item_id, partition_key=partition_key)
            return result
            
        except exceptions.CosmosResourceNotFoundError:
            return None
        except exceptions.CosmosHttpResponseError as e:
            logging.error(f"Error reading item from {container_name}: {e}")
            raise
    
    async def update_item(self, container_name: str, item: Dict[str, Any], partition_key: str) -> Dict[str, Any]:
        """Update an item in the specified container."""
        if self._development_mode:
            # Return mock response for development
            logging.info(f"DEV MODE: Updating item in {container_name}")
            return {**item, '_mock': True}
        
        try:
            container = self.get_container(container_name)
            
            # Ensure the partition key is correct in the item
            if 'userId' in item and partition_key != item['userId']:
                item['userId'] = partition_key
            elif 'date' in item and partition_key != item['date']:
                item['date'] = partition_key
            elif 'type' in item and partition_key != item['type']:
                item['type'] = partition_key
            
            result = container.upsert_item(body=item, partition_key=partition_key)
            return result
            
        except exceptions.CosmosHttpResponseError as e:
            logging.error(f"Error updating item in {container_name}: {e}")
            raise
    
    async def delete_item(self, container_name: str, item_id: str, partition_key: str) -> None:
        """Delete an item from the specified container."""
        if self._development_mode:
            # Mock delete for development
            logging.info(f"DEV MODE: Deleting item {item_id} from {container_name}")
            return
        
        try:
            container = self.get_container(container_name)
            container.delete_item(item=item_id, partition_key=partition_key)
            return True
            
        except exceptions.CosmosResourceNotFoundError:
            return False
        except exceptions.CosmosHttpResponseError as e:
            logging.error(f"Error deleting item from {container_name}: {e}")
            raise
    
    async def query_items(self, container_name: str, query: str, parameters: Optional[list] = None, partition_key: Optional[str] = None) -> list:
        """Query items from the specified container."""
        if self._development_mode:
            # Return mock query results for development
            logging.info(f"DEV MODE: Querying items from {container_name} with query: {query}")
            return [
                {'id': 'mock-query-result-1', 'name': 'Mock Query Result 1', '_mock': True},
                {'id': 'mock-query-result-2', 'name': 'Mock Query Result 2', '_mock': True}
            ]
        
        try:
            container = self.get_container(container_name)
            
            query_options = {}
            if partition_key:
                query_options['partition_key'] = partition_key
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                **query_options
            ))
            
            return items
            
        except exceptions.CosmosHttpResponseError as e:
            logging.error(f"Error querying items from {container_name}: {e}")
            raise
    
    async def list_items(self, container_name: str, partition_key: Optional[str] = None, max_item_count: int = 100) -> list:
        """List items from the specified container."""
        if self._development_mode:
            # Return mock list for development
            logging.info(f"DEV MODE: Listing items from {container_name}")
            return [
                {'id': 'mock-item-1', 'name': 'Mock Item 1', '_mock': True},
                {'id': 'mock-item-2', 'name': 'Mock Item 2', '_mock': True}
            ]
        
        try:
            container = self.get_container(container_name)
            
            query_options = {'max_item_count': max_item_count}
            if partition_key:
                query_options['partition_key'] = partition_key
            
            items = list(container.read_all_items(**query_options))
            return items
            
        except exceptions.CosmosHttpResponseError as e:
            logging.error(f"Error listing items from {container_name}: {e}")
            raise


# Global database manager instance
db_manager = DatabaseManager()


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager


def get_cosmos_client():
    """Get a Cosmos DB client instance."""
    return db_manager.client
