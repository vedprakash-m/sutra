"""
Async Cosmos DB helper for Forge API endpoints.
Provides a shared async CosmosClient to avoid duplicate client creation across forge modules.
"""

import logging
import os
from types import TracebackType
from typing import Any, Dict, List, Optional, Type

from azure.cosmos.aio import CosmosClient

logger = logging.getLogger(__name__)

DATABASE_NAME = "SutraDB"
FORGE_PROJECTS_CONTAINER = "ForgeProjects"
FORGE_TEMPLATES_CONTAINER = "ForgeTemplates"
FORGE_ANALYTICS_CONTAINER = "ForgeAnalytics"


def get_connection_string() -> str:
    """Get Cosmos DB connection string from environment."""
    return os.getenv("COSMOS_DB_CONNECTION_STRING", "")


class AsyncCosmosHelper:
    """
    Async context manager for Cosmos DB operations.

    Usage:
        async with AsyncCosmosHelper() as helper:
            container = await helper.get_container("ForgeProjects")
            item = await container.read_item(item_id, partition_key=partition_key)
    """

    def __init__(self, connection_string: Optional[str] = None):
        self._connection_string = connection_string or get_connection_string()
        self._client: Optional[CosmosClient] = None

    async def __aenter__(self):
        self._client = CosmosClient.from_connection_string(self._connection_string)
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        if self._client:
            await self._client.close()
        return False

    async def get_container(self, container_name: str = FORGE_PROJECTS_CONTAINER) -> Any:
        """Get a container client."""
        if not self._client:
            raise RuntimeError("CosmosClient not initialized. Use 'async with' context manager.")
        database = self._client.get_database_client(DATABASE_NAME)
        return database.get_container_client(container_name)

    async def upsert_item(
        self,
        item: Dict[str, Any],
        container_name: str = FORGE_PROJECTS_CONTAINER,
    ) -> Dict[str, Any]:
        """Upsert an item into the specified container."""
        container = await self.get_container(container_name)
        return await container.upsert_item(item)

    async def read_item(
        self,
        item_id: str,
        partition_key: str,
        container_name: str = FORGE_PROJECTS_CONTAINER,
    ) -> Dict[str, Any]:
        """Read a single item by ID."""
        container = await self.get_container(container_name)
        return await container.read_item(item_id, partition_key=partition_key)

    async def query_items(
        self,
        query: str,
        parameters: Optional[List[Dict[str, Any]]] = None,
        container_name: str = FORGE_PROJECTS_CONTAINER,
    ) -> List[Dict[str, Any]]:
        """Query items from a container."""
        container = await self.get_container(container_name)
        items: List[Dict[str, Any]] = []
        async for item in container.query_items(
            query=query,
            parameters=parameters or [],
            enable_cross_partition_query=True,
        ):
            items.append(item)
        return items

    async def create_item(
        self,
        item: Dict[str, Any],
        container_name: str = FORGE_PROJECTS_CONTAINER,
    ) -> Dict[str, Any]:
        """Create a new item in the specified container (fails if ID already exists)."""
        container = await self.get_container(container_name)
        return await container.create_item(body=item)

    async def delete_item(
        self,
        item_id: str,
        partition_key: str,
        container_name: str = FORGE_PROJECTS_CONTAINER,
    ) -> None:
        """Delete an item by ID."""
        container = await self.get_container(container_name)
        await container.delete_item(item_id, partition_key=partition_key)
