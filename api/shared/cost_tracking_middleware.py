"""
Cost tracking middleware for LLM API calls.
Integrates with existing LLM providers to automatically track costs.
"""
import asyncio
import logging
import time
import uuid
from typing import Any, Dict, Optional, Callable, Awaitable
from functools import wraps
from datetime import datetime, timezone

from .cost_tracker import CostTracker
from .llm_providers.base_provider import LLMResponse, TokenUsage


class CostTrackingMiddleware:
    """
    Middleware to automatically track costs for all LLM API calls.
    
    Features:
    - Automatic cost tracking for all LLM executions
    - Real-time budget validation
    - Request/response logging
    - Performance metrics
    """
    
    def __init__(self, cost_tracker: CostTracker):
        self.cost_tracker = cost_tracker
        self.logger = logging.getLogger(__name__)
    
    def track_llm_execution(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ):
        """
        Decorator to track LLM execution costs.
        
        Usage:
            @middleware.track_llm_execution(user_id="user123", session_id="session456")
            async def execute_prompt(provider, prompt, **kwargs):
                return await provider.execute_prompt(prompt, **kwargs)
        """
        def decorator(func: Callable[..., Any]):
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Generate request tracking info
                request_id = str(uuid.uuid4())
                start_time = time.time()
                session = session_id or f"session_{int(time.time())}"
                
                try:
                    # Extract provider and model info from args/kwargs
                    provider_name = None
                    model_name = None
                    
                    # Try to extract from first argument (provider)
                    if args and hasattr(args[0], '__class__'):
                        provider_class = args[0].__class__.__name__
                        if 'provider' in provider_class.lower():
                            provider_name = provider_class.replace('Provider', '').replace('LLM', '').lower()
                    
                    # Try to extract model from kwargs
                    if 'model' in kwargs:
                        model_name = kwargs['model']
                    elif 'model_name' in kwargs:
                        model_name = kwargs['model_name']
                    
                    self.logger.info(
                        f"Starting LLM execution tracking: {request_id} "
                        f"({provider_name}/{model_name})"
                    )
                    
                    # Execute the original function
                    result = await func(*args, **kwargs)
                    
                    # Calculate execution time
                    execution_time_ms = int((time.time() - start_time) * 1000)
                    
                    # Extract token usage and cost information
                    if isinstance(result, LLMResponse) and result.token_usage:
                        await self._track_execution_result(
                            user_id=user_id,
                            session_id=session,
                            provider=provider_name or "unknown",
                            model=model_name or "unknown",
                            token_usage=result.token_usage,
                            execution_time_ms=execution_time_ms,
                            request_id=request_id,
                            response=result,
                            request_data=kwargs
                        )
                    else:
                        self.logger.warning(
                            f"No token usage data available for request {request_id}"
                        )
                    
                    return result
                    
                except Exception as e:
                    # Track failed executions too
                    execution_time_ms = int((time.time() - start_time) * 1000)
                    
                    await self._track_execution_failure(
                        user_id=user_id,
                        session_id=session,
                        provider=provider_name or "unknown",
                        model=model_name or "unknown", 
                        execution_time_ms=execution_time_ms,
                        request_id=request_id,
                        error=str(e),
                        request_data=kwargs
                    )
                    
                    raise
            
            return wrapper
        return decorator
    
    async def _track_execution_result(
        self,
        user_id: str,
        session_id: str,
        provider: str,
        model: str,
        token_usage: TokenUsage,
        execution_time_ms: int,
        request_id: str,
        response: LLMResponse,
        request_data: Dict[str, Any]
    ) -> None:
        """Track successful LLM execution."""
        try:
            # Prepare metadata
            metadata = {
                "success": True,
                "response_id": response.id if hasattr(response, 'id') else None,
                "finish_reason": response.finish_reason if hasattr(response, 'finish_reason') else None,
                "model_version": response.model if hasattr(response, 'model') else model,
                "request_data": {
                    "temperature": request_data.get("temperature"),
                    "max_tokens": request_data.get("max_tokens"),
                    "stream": request_data.get("stream", False),
                    "system_prompt_length": len(str(request_data.get("system_prompt", "")))
                }
            }
            
            # Track in cost tracker
            cost_entry = await self.cost_tracker.track_llm_usage(
                user_id=user_id,
                session_id=session_id,
                provider=provider,
                model=model,
                prompt_tokens=token_usage.prompt_tokens,
                completion_tokens=token_usage.completion_tokens,
                execution_time_ms=execution_time_ms,
                request_id=request_id,
                metadata=metadata
            )
            
            self.logger.info(
                f"Tracked successful execution: {request_id} - "
                f"${float(cost_entry.total_cost):.6f} "
                f"({token_usage.total_tokens} tokens)"
            )
            
        except Exception as e:
            self.logger.error(f"Error tracking execution result: {str(e)}")
    
    async def _track_execution_failure(
        self,
        user_id: str,
        session_id: str,
        provider: str,
        model: str,
        execution_time_ms: int,
        request_id: str,
        error: str,
        request_data: Dict[str, Any]
    ) -> None:
        """Track failed LLM execution."""
        try:
            # Prepare metadata for failed execution
            metadata = {
                "success": False,
                "error": error,
                "request_data": {
                    "temperature": request_data.get("temperature"),
                    "max_tokens": request_data.get("max_tokens"),
                    "stream": request_data.get("stream", False)
                }
            }
            
            # Track with zero costs but record the failure
            await self.cost_tracker.track_llm_usage(
                user_id=user_id,
                session_id=session_id,
                provider=provider,
                model=model,
                prompt_tokens=0,
                completion_tokens=0,
                execution_time_ms=execution_time_ms,
                request_id=request_id,
                metadata=metadata
            )
            
            self.logger.warning(
                f"Tracked failed execution: {request_id} - {error}"
            )
            
        except Exception as e:
            self.logger.error(f"Error tracking execution failure: {str(e)}")
    
    async def validate_budget_before_execution(
        self,
        user_id: str,
        provider: str,
        model: str,
        estimated_tokens: int
    ) -> Dict[str, Any]:
        """
        Validate budget constraints before executing LLM request.
        
        Returns:
            Dict with validation result and details
        """
        try:
            # Get current month's spending
            start_of_month = datetime.now(timezone.utc).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            
            summary = await self.cost_tracker.get_cost_summary(
                user_id=user_id,
                start_date=start_of_month
            )
            
            # Estimate cost for this request
            input_cost, output_cost, estimated_cost = self.cost_tracker._calculate_cost(
                provider, model, estimated_tokens, estimated_tokens // 2  # Rough estimate
            )
            
            # Check against alert thresholds
            projected_total = summary.total_cost + estimated_cost
            
            # Default budget limits (should be configurable per user)
            budget_limits = {
                "daily": 50.0,    # $50 per day
                "monthly": 500.0,  # $500 per month
                "emergency": 1000.0  # $1000 hard limit
            }
            
            warnings = []
            can_execute = True
            
            # Check emergency limit
            if projected_total >= budget_limits["emergency"]:
                can_execute = False
                warnings.append({
                    "level": "emergency",
                    "message": f"Emergency budget limit exceeded: ${float(projected_total):.2f} >= ${budget_limits['emergency']:.2f}",
                    "current_spend": float(summary.total_cost),
                    "estimated_cost": float(estimated_cost),
                    "projected_total": float(projected_total)
                })
            
            # Check monthly limit
            elif projected_total >= budget_limits["monthly"]:
                warnings.append({
                    "level": "critical",
                    "message": f"Monthly budget limit approaching: ${float(projected_total):.2f} >= ${budget_limits['monthly']:.2f}",
                    "current_spend": float(summary.total_cost),
                    "estimated_cost": float(estimated_cost),
                    "projected_total": float(projected_total)
                })
            
            # Check warning thresholds
            elif projected_total >= budget_limits["monthly"] * 0.8:
                warnings.append({
                    "level": "warning",
                    "message": f"80% of monthly budget reached: ${float(projected_total):.2f}",
                    "current_spend": float(summary.total_cost),
                    "estimated_cost": float(estimated_cost),
                    "projected_total": float(projected_total)
                })
            
            return {
                "can_execute": can_execute,
                "current_spend": float(summary.total_cost),
                "estimated_cost": float(estimated_cost),
                "projected_total": float(projected_total),
                "warnings": warnings,
                "budget_limits": budget_limits,
                "provider": provider,
                "model": model,
                "estimated_tokens": estimated_tokens
            }
            
        except Exception as e:
            self.logger.error(f"Error validating budget: {str(e)}")
            # In case of error, allow execution but log the issue
            return {
                "can_execute": True,
                "error": str(e),
                "current_spend": 0,
                "estimated_cost": 0,
                "projected_total": 0,
                "warnings": [],
                "budget_limits": {}
            }
    
    async def get_real_time_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get real-time usage statistics for a user."""
        try:
            # Get current month's summary
            start_of_month = datetime.now(timezone.utc).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            
            summary = await self.cost_tracker.get_cost_summary(
                user_id=user_id,
                start_date=start_of_month
            )
            
            # Get recent alerts
            alerts = await self.cost_tracker.get_recent_alerts(user_id=user_id, limit=10)
            
            # Get cost analytics
            analytics = await self.cost_tracker.get_cost_analytics(user_id=user_id, days=30)
            
            return {
                "current_month": {
                    "total_cost": float(summary.total_cost),
                    "total_requests": summary.total_requests,
                    "total_tokens": summary.total_tokens,
                    "average_cost_per_request": float(summary.average_cost_per_request),
                    "cost_by_provider": {k: float(v) for k, v in summary.cost_by_provider.items()},
                    "cost_by_model": {k: float(v) for k, v in summary.cost_by_model.items()}
                },
                "recent_alerts": [
                    {
                        "level": alert.level.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "acknowledged": alert.acknowledged
                    }
                    for alert in alerts
                ],
                "analytics": analytics,
                "period": {
                    "start": start_of_month.isoformat(),
                    "end": datetime.now(timezone.utc).isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting usage stats: {str(e)}")
            return {"error": str(e)}


class BudgetValidationError(Exception):
    """Exception raised when budget validation fails."""
    
    def __init__(self, message: str, current_spend: float, estimated_cost: float, limit: float):
        self.message = message
        self.current_spend = current_spend
        self.estimated_cost = estimated_cost
        self.limit = limit
        super().__init__(self.message)


# Singleton instance for middleware
_cost_middleware_instance = None


def get_cost_tracking_middleware(cost_tracker: CostTracker = None) -> CostTrackingMiddleware:
    """Get or create cost tracking middleware instance."""
    global _cost_middleware_instance
    
    if _cost_middleware_instance is None and cost_tracker:
        _cost_middleware_instance = CostTrackingMiddleware(cost_tracker)
    
    return _cost_middleware_instance


def track_costs(user_id: str, session_id: Optional[str] = None):
    """
    Convenience decorator for cost tracking.
    
    Usage:
        @track_costs(user_id="user123")
        async def my_llm_function(provider, prompt):
            return await provider.execute_prompt(prompt)
    """
    middleware = get_cost_tracking_middleware()
    if middleware:
        return middleware.track_llm_execution(user_id=user_id, session_id=session_id)
    else:
        # Return a no-op decorator if middleware not initialized
        def no_op_decorator(func):
            return func
        return no_op_decorator
