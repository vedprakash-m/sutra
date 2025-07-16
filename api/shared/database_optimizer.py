"""
Database Query Optimization Service - Task 3.2 Performance Optimization
Implements query optimization, connection pooling, and indexing strategies
"""

import logging
import time
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
from dataclasses import dataclass

@dataclass
class QueryMetrics:
    """Metrics for database query performance tracking"""
    query: str
    execution_time: float
    request_charge: float
    result_count: int
    timestamp: float
    container: str

class DatabaseOptimizer:
    """
    Database optimization service with query optimization, caching, and performance monitoring
    """
    
    def __init__(self, database_manager: Any):
        self.db_manager = database_manager
        self.query_metrics: List[QueryMetrics] = []
        self.slow_query_threshold = 1000  # ms
        self.high_ru_threshold = 50  # RU
        
    def track_query_performance(self, func: Callable) -> Callable:
        """Decorator to track query performance metrics"""
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Extract query info from kwargs
                query = str(kwargs.get('query', 'unknown'))
                container_name = str(kwargs.get('container_name', 'unknown'))
                
                # Estimate RU cost (simplified - in real scenario, get from response headers)
                ru_cost = self._estimate_ru_cost(query, result)
                
                # Store metrics
                metrics = QueryMetrics(
                    query=query,
                    execution_time=execution_time,
                    request_charge=ru_cost,
                    result_count=len(result) if isinstance(result, list) else 1,
                    timestamp=time.time(),
                    container=container_name
                )
                
                self.query_metrics.append(metrics)
                
                # Log slow queries
                if execution_time > self.slow_query_threshold:
                    logging.warning(f"Slow query detected: {execution_time:.2f}ms - {query[:100]}...")
                
                if ru_cost > self.high_ru_threshold:
                    logging.warning(f"High RU cost query: {ru_cost:.2f}RU - {query[:100]}...")
                
                return result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logging.error(f"Query failed after {execution_time:.2f}ms: {str(e)}")
                raise
                
        return wrapper
    
    def _estimate_ru_cost(self, query: str, result: Any) -> float:
        """Estimate RU cost based on query complexity and result size"""
        base_cost = 2.5  # Base read cost
        
        # Increase cost for complex queries
        if 'JOIN' in query.upper():
            base_cost *= 2
        if 'ORDER BY' in query.upper():
            base_cost *= 1.5
        if 'GROUP BY' in query.upper():
            base_cost *= 2
        if 'DISTINCT' in query.upper():
            base_cost *= 1.5
        
        # Increase cost based on result size
        if isinstance(result, list):
            base_cost += len(result) * 0.1
        
        return base_cost
    
    def get_optimization_suggestions(self) -> List[str]:
        """Analyze query metrics and provide optimization suggestions"""
        suggestions = []
        
        if not self.query_metrics:
            return ["No query metrics available for analysis"]
        
        # Analyze recent metrics (last 100 queries)
        recent_metrics = self.query_metrics[-100:]
        
        # Find slow queries
        slow_queries = [m for m in recent_metrics if m.execution_time > self.slow_query_threshold]
        if slow_queries:
            suggestions.append(f"Found {len(slow_queries)} slow queries. Consider adding indexes or optimizing WHERE clauses.")
        
        # Find high RU queries
        high_ru_queries = [m for m in recent_metrics if m.request_charge > self.high_ru_threshold]
        if high_ru_queries:
            suggestions.append(f"Found {len(high_ru_queries)} high RU cost queries. Consider query optimization or result limiting.")
        
        # Check for frequently executed queries
        query_counts = {}
        for metric in recent_metrics:
            query_key = metric.query[:50]  # Use first 50 chars as key
            query_counts[query_key] = query_counts.get(query_key, 0) + 1
        
        frequent_queries = {k: v for k, v in query_counts.items() if v > 5}
        if frequent_queries:
            suggestions.append(f"Found {len(frequent_queries)} frequently executed queries. Consider caching results.")
        
        # Average performance analysis
        avg_time = sum(m.execution_time for m in recent_metrics) / len(recent_metrics)
        avg_ru = sum(m.request_charge for m in recent_metrics) / len(recent_metrics)
        
        if avg_time > 500:
            suggestions.append(f"Average query time is {avg_time:.2f}ms. Consider general performance optimization.")
        
        if avg_ru > 25:
            suggestions.append(f"Average RU cost is {avg_ru:.2f}. Consider query pattern optimization.")
        
        return suggestions or ["Query performance looks good!"]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        if not self.query_metrics:
            return {"message": "No metrics available"}
        
        recent_metrics = self.query_metrics[-100:]
        
        return {
            "total_queries": len(self.query_metrics),
            "recent_queries": len(recent_metrics),
            "avg_execution_time": sum(m.execution_time for m in recent_metrics) / len(recent_metrics),
            "avg_ru_cost": sum(m.request_charge for m in recent_metrics) / len(recent_metrics),
            "slow_queries_count": len([m for m in recent_metrics if m.execution_time > self.slow_query_threshold]),
            "high_ru_queries_count": len([m for m in recent_metrics if m.request_charge > self.high_ru_threshold]),
            "containers_accessed": list(set(m.container for m in recent_metrics)),
            "optimization_suggestions": self.get_optimization_suggestions()
        }

class OptimizedDatabaseManager:
    """
    Enhanced database manager with performance optimizations
    """
    
    def __init__(self, base_manager):
        self.base_manager = base_manager
        self.optimizer = DatabaseOptimizer(base_manager)
        self._connection_pool_size = 10
        self._query_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
    @property
    def client(self):
        return self.base_manager.client
    
    @property 
    def database(self):
        return self.base_manager.database
    
    def get_container(self, container_name: str):
        return self.base_manager.get_container(container_name)
    
    def _build_optimized_query(self, container_name: str, query: str, parameters: Optional[list] = None) -> str:
        """Build optimized query with indexing hints and best practices"""
        
        # Add indexing hints based on container type
        optimized_query = query
        
        if container_name == "Prompts":
            # Optimize for common prompt queries
            if "WHERE" in query.upper() and "userId" in query:
                # Ensure userId is used efficiently
                if "ORDER BY" not in query.upper():
                    optimized_query += " ORDER BY c.userId, c.createdAt DESC"
        
        elif container_name == "Collections":
            # Optimize for collection queries
            if "WHERE" in query.upper() and "userId" in query:
                if "ORDER BY" not in query.upper():
                    optimized_query += " ORDER BY c.userId, c.updatedAt DESC"
        
        elif container_name == "Users":
            # Optimize for user queries
            if "WHERE" in query.upper() and "email" in query:
                # Email lookups should be efficient
                pass
        
        elif container_name == "CostTracking":
            # Optimize for cost tracking queries
            if "WHERE" in query.upper() and "date" in query:
                if "ORDER BY" not in query.upper():
                    optimized_query += " ORDER BY c.date DESC"
        
        return optimized_query
    
    def _should_cache_query(self, query: str, container_name: str) -> bool:
        """Determine if query results should be cached"""
        
        # Cache read-only queries for relatively static data
        if query.strip().upper().startswith("SELECT"):
            # Cache user lookups
            if container_name == "Users" and "email" in query:
                return True
            
            # Cache prompt templates and collections
            if container_name in ["Prompts", "Collections"] and "WHERE c.isTemplate = true" in query:
                return True
            
            # Don't cache real-time data
            if container_name == "CostTracking":
                return False
                
            # Cache configuration and settings
            if "settings" in query.lower() or "config" in query.lower():
                return True
        
        return False
    
    @DatabaseOptimizer.track_query_performance
    async def query_items_optimized(
        self,
        container_name: str,
        query: str,
        parameters: Optional[list] = None,
        partition_key: Optional[str] = None,
        enable_caching: bool = True
    ) -> list:
        """Optimized query method with caching and performance tracking"""
        
        # Build cache key
        cache_key = f"{container_name}:{query}:{str(parameters)}:{partition_key}"
        
        # Check cache if enabled
        if enable_caching and self._should_cache_query(query, container_name):
            cached_result = self._query_cache.get(cache_key)
            if cached_result and time.time() - cached_result['timestamp'] < self._cache_ttl:
                logging.debug(f"Cache hit for query in {container_name}")
                return cached_result['data']
        
        # Optimize the query
        optimized_query = self._build_optimized_query(container_name, query, parameters)
        
        # Execute query through base manager
        start_time = time.time()
        try:
            result = await self.base_manager.query_items(
                container_name=container_name,
                query=optimized_query,
                parameters=parameters,
                partition_key=partition_key
            )
            
            # Cache the result if appropriate
            if enable_caching and self._should_cache_query(query, container_name):
                self._query_cache[cache_key] = {
                    'data': result,
                    'timestamp': time.time()
                }
                logging.debug(f"Cached query result for {container_name}")
            
            return result
            
        except Exception as e:
            logging.error(f"Optimized query failed: {str(e)}")
            raise
    
    def clear_query_cache(self, container_name: Optional[str] = None):
        """Clear query cache for specific container or all"""
        if container_name:
            # Clear cache entries for specific container
            keys_to_remove = [k for k in self._query_cache.keys() if k.startswith(f"{container_name}:")]
            for key in keys_to_remove:
                del self._query_cache[key]
            logging.info(f"Cleared query cache for {container_name}")
        else:
            # Clear entire cache
            self._query_cache.clear()
            logging.info("Cleared entire query cache")
    
    async def create_item(self, container_name: str, item: Dict[str, Any], partition_key: str = None) -> Dict[str, Any]:
        """Create item and invalidate relevant cache"""
        result = await self.base_manager.create_item(container_name, item, partition_key)
        
        # Invalidate cache for this container
        self.clear_query_cache(container_name)
        
        return result
    
    async def update_item(self, container_name: str, item: Dict[str, Any], partition_key: str) -> Dict[str, Any]:
        """Update item and invalidate relevant cache"""
        result = await self.base_manager.update_item(container_name, item, partition_key)
        
        # Invalidate cache for this container
        self.clear_query_cache(container_name)
        
        return result
    
    async def delete_item(self, container_name: str, item_id: str, partition_key: str) -> None:
        """Delete item and invalidate relevant cache"""
        result = await self.base_manager.delete_item(container_name, item_id, partition_key)
        
        # Invalidate cache for this container
        self.clear_query_cache(container_name)
        
        return result
    
    # Delegate other methods to base manager
    async def read_item(self, container_name: str, item_id: str, partition_key: str):
        return await self.base_manager.read_item(container_name, item_id, partition_key)
    
    async def list_items(self, container_name: str, partition_key: Optional[str] = None, max_item_count: int = 100):
        return await self.base_manager.list_items(container_name, partition_key, max_item_count)

# Global optimized database manager instance
_optimized_db_manager = None

def get_optimized_database_manager():
    """Get singleton optimized database manager"""
    global _optimized_db_manager
    if _optimized_db_manager is None:
        from shared.database import get_database_manager
        base_manager = get_database_manager()
        _optimized_db_manager = OptimizedDatabaseManager(base_manager)
    return _optimized_db_manager
