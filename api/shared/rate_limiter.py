"""
Advanced Rate Limiting System
Implements sophisticated rate limiting with multiple strategies and adaptive thresholds
"""

import hashlib
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Callable, Dict, List, Optional, Tuple, Union

import azure.functions as func

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""

    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    ADAPTIVE = "adaptive"


class RateLimitScope(Enum):
    """Scope of rate limiting"""

    GLOBAL = "global"
    PER_USER = "per_user"
    PER_IP = "per_ip"
    PER_ENDPOINT = "per_endpoint"
    PER_USER_ENDPOINT = "per_user_endpoint"


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration"""

    name: str
    strategy: RateLimitStrategy
    scope: RateLimitScope
    limit: int  # Maximum requests
    window_seconds: int  # Time window
    burst_limit: Optional[int] = None  # Allow bursts up to this limit
    exempt_users: List[str] = None  # Users exempt from this rule
    exempt_ips: List[str] = None  # IPs exempt from this rule
    enabled: bool = True

    # Adaptive strategy parameters
    min_limit: Optional[int] = None
    max_limit: Optional[int] = None
    adjustment_factor: float = 0.1

    # Advanced options
    penalty_multiplier: float = 2.0  # Increase penalty for violations
    grace_period_seconds: int = 300  # Cool-down period after violation


@dataclass
class RateLimitStatus:
    """Current rate limit status"""

    rule_name: str
    current_count: int
    limit: int
    window_seconds: int
    reset_time: datetime
    remaining: int
    is_limited: bool
    penalty_until: Optional[datetime] = None


@dataclass
class RateLimitViolation:
    """Rate limit violation record"""

    timestamp: datetime
    rule_name: str
    identifier: str
    current_count: int
    limit: int
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    endpoint: Optional[str] = None
    user_agent: Optional[str] = None


class TokenBucket:
    """Token bucket implementation for rate limiting"""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from bucket"""
        now = time.time()

        # Refill tokens based on time passed
        time_passed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def get_status(self) -> dict:
        """Get current bucket status"""
        return {"tokens": self.tokens, "capacity": self.capacity, "refill_rate": self.refill_rate}


class SlidingWindowCounter:
    """Sliding window counter for rate limiting"""

    def __init__(self, window_seconds: int, max_requests: int):
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.requests = deque()

    def add_request(self, timestamp: float = None) -> bool:
        """Add a request and check if within limit"""
        if timestamp is None:
            timestamp = time.time()

        # Remove old requests outside the window
        window_start = timestamp - self.window_seconds
        while self.requests and self.requests[0] <= window_start:
            self.requests.popleft()

        # Check if we can add this request
        if len(self.requests) < self.max_requests:
            self.requests.append(timestamp)
            return True
        return False

    def get_count(self) -> int:
        """Get current request count in window"""
        now = time.time()
        window_start = now - self.window_seconds
        while self.requests and self.requests[0] <= window_start:
            self.requests.popleft()
        return len(self.requests)

    def get_reset_time(self) -> datetime:
        """Get when the window will reset"""
        if not self.requests:
            return datetime.utcnow()
        return datetime.fromtimestamp(self.requests[0] + self.window_seconds)


class RateLimiter:
    """Advanced rate limiting system"""

    def __init__(self):
        self.rules: Dict[str, RateLimitRule] = {}
        self.buckets: Dict[str, TokenBucket] = {}
        self.counters: Dict[str, SlidingWindowCounter] = {}
        self.violations: List[RateLimitViolation] = []
        self.penalties: Dict[str, datetime] = {}  # identifier -> penalty_until

        # Storage for fixed window counters
        self.fixed_windows: Dict[str, Dict[int, int]] = defaultdict(dict)

        # Adaptive rate limiting state
        self.adaptive_state: Dict[str, Dict] = defaultdict(dict)

        # Default rules
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Setup default rate limiting rules"""
        self.add_rule(
            RateLimitRule(
                name="api_global",
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                scope=RateLimitScope.GLOBAL,
                limit=10000,
                window_seconds=3600,  # 10k requests per hour globally
            )
        )

        self.add_rule(
            RateLimitRule(
                name="api_per_user",
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                scope=RateLimitScope.PER_USER,
                limit=1000,
                window_seconds=3600,  # 1k requests per hour per user
                burst_limit=100,  # Allow bursts up to 100 requests
            )
        )

        self.add_rule(
            RateLimitRule(
                name="api_per_ip",
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                scope=RateLimitScope.PER_IP,
                limit=100,
                window_seconds=60,  # 100 requests per minute per IP
            )
        )

        self.add_rule(
            RateLimitRule(
                name="auth_endpoint",
                strategy=RateLimitStrategy.FIXED_WINDOW,
                scope=RateLimitScope.PER_IP,
                limit=10,
                window_seconds=300,  # 10 auth attempts per 5 minutes per IP
                penalty_multiplier=3.0,
            )
        )

        self.add_rule(
            RateLimitRule(
                name="expensive_operations",
                strategy=RateLimitStrategy.ADAPTIVE,
                scope=RateLimitScope.PER_USER,
                limit=50,
                window_seconds=3600,
                min_limit=10,
                max_limit=200,
                adjustment_factor=0.2,
            )
        )

    def add_rule(self, rule: RateLimitRule):
        """Add a rate limiting rule"""
        self.rules[rule.name] = rule
        logger.info(f"Added rate limit rule: {rule.name}")

    def check_rate_limit(
        self, identifier: str, rule_names: List[str] = None, user_id: str = None, ip_address: str = None, endpoint: str = None
    ) -> Tuple[bool, List[RateLimitStatus]]:
        """Check if request is within rate limits"""
        if rule_names is None:
            rule_names = list(self.rules.keys())

        statuses = []
        is_allowed = True

        for rule_name in rule_names:
            rule = self.rules.get(rule_name)
            if not rule or not rule.enabled:
                continue

            # Check if exempt
            if self._is_exempt(rule, user_id, ip_address):
                continue

            # Get scope-specific identifier
            scope_identifier = self._get_scope_identifier(rule.scope, identifier, user_id, ip_address, endpoint)

            # Check for active penalty
            penalty_key = f"{rule_name}:{scope_identifier}"
            if penalty_key in self.penalties:
                if datetime.utcnow() < self.penalties[penalty_key]:
                    status = RateLimitStatus(
                        rule_name=rule_name,
                        current_count=rule.limit + 1,
                        limit=rule.limit,
                        window_seconds=rule.window_seconds,
                        reset_time=self.penalties[penalty_key],
                        remaining=0,
                        is_limited=True,
                        penalty_until=self.penalties[penalty_key],
                    )
                    statuses.append(status)
                    is_allowed = False
                    continue
                else:
                    # Penalty expired
                    del self.penalties[penalty_key]

            # Check rate limit based on strategy
            status = self._check_rule(rule, scope_identifier, user_id, ip_address, endpoint)
            statuses.append(status)

            if status.is_limited:
                is_allowed = False

                # Apply penalty if configured
                if rule.penalty_multiplier > 1.0:
                    penalty_duration = rule.window_seconds * rule.penalty_multiplier
                    penalty_until = datetime.utcnow() + timedelta(seconds=penalty_duration)
                    self.penalties[penalty_key] = penalty_until
                    status.penalty_until = penalty_until

                # Record violation
                violation = RateLimitViolation(
                    timestamp=datetime.utcnow(),
                    rule_name=rule_name,
                    identifier=scope_identifier,
                    current_count=status.current_count,
                    limit=status.limit,
                    user_id=user_id,
                    ip_address=ip_address,
                    endpoint=endpoint,
                )
                self.violations.append(violation)

                # Log violation
                logger.warning(f"Rate limit violation: {rule_name} for {scope_identifier}")

        return is_allowed, statuses

    def _is_exempt(self, rule: RateLimitRule, user_id: str = None, ip_address: str = None) -> bool:
        """Check if request is exempt from rate limiting"""
        if rule.exempt_users and user_id in rule.exempt_users:
            return True
        if rule.exempt_ips and ip_address in rule.exempt_ips:
            return True
        return False

    def _get_scope_identifier(
        self, scope: RateLimitScope, identifier: str, user_id: str = None, ip_address: str = None, endpoint: str = None
    ) -> str:
        """Get identifier based on scope"""
        if scope == RateLimitScope.GLOBAL:
            return "global"
        elif scope == RateLimitScope.PER_USER:
            return f"user:{user_id or identifier}"
        elif scope == RateLimitScope.PER_IP:
            return f"ip:{ip_address or identifier}"
        elif scope == RateLimitScope.PER_ENDPOINT:
            return f"endpoint:{endpoint or identifier}"
        elif scope == RateLimitScope.PER_USER_ENDPOINT:
            return f"user:{user_id or identifier}:endpoint:{endpoint or identifier}"
        return identifier

    def _check_rule(
        self, rule: RateLimitRule, identifier: str, user_id: str = None, ip_address: str = None, endpoint: str = None
    ) -> RateLimitStatus:
        """Check a specific rule"""
        key = f"{rule.name}:{identifier}"

        if rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return self._check_token_bucket(rule, key)
        elif rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return self._check_sliding_window(rule, key)
        elif rule.strategy == RateLimitStrategy.FIXED_WINDOW:
            return self._check_fixed_window(rule, key)
        elif rule.strategy == RateLimitStrategy.ADAPTIVE:
            return self._check_adaptive(rule, key, user_id, ip_address, endpoint)
        else:
            # Default to sliding window
            return self._check_sliding_window(rule, key)

    def _check_token_bucket(self, rule: RateLimitRule, key: str) -> RateLimitStatus:
        """Check token bucket rate limit"""
        if key not in self.buckets:
            refill_rate = rule.limit / rule.window_seconds
            self.buckets[key] = TokenBucket(rule.limit, refill_rate)

        bucket = self.buckets[key]
        can_proceed = bucket.consume(1)

        return RateLimitStatus(
            rule_name=rule.name,
            current_count=int(rule.limit - bucket.tokens),
            limit=rule.limit,
            window_seconds=rule.window_seconds,
            reset_time=datetime.utcnow() + timedelta(seconds=rule.window_seconds),
            remaining=int(bucket.tokens),
            is_limited=not can_proceed,
        )

    def _check_sliding_window(self, rule: RateLimitRule, key: str) -> RateLimitStatus:
        """Check sliding window rate limit"""
        if key not in self.counters:
            self.counters[key] = SlidingWindowCounter(rule.window_seconds, rule.limit)

        counter = self.counters[key]
        can_proceed = counter.add_request()
        current_count = counter.get_count()

        return RateLimitStatus(
            rule_name=rule.name,
            current_count=current_count,
            limit=rule.limit,
            window_seconds=rule.window_seconds,
            reset_time=counter.get_reset_time(),
            remaining=max(0, rule.limit - current_count),
            is_limited=not can_proceed,
        )

    def _check_fixed_window(self, rule: RateLimitRule, key: str) -> RateLimitStatus:
        """Check fixed window rate limit"""
        now = time.time()
        window_start = int(now // rule.window_seconds) * rule.window_seconds

        if key not in self.fixed_windows:
            self.fixed_windows[key] = {}

        # Clean old windows
        old_windows = [w for w in self.fixed_windows[key].keys() if w < window_start - rule.window_seconds]
        for old_window in old_windows:
            del self.fixed_windows[key][old_window]

        # Get current count
        current_count = self.fixed_windows[key].get(window_start, 0)

        # Check if can proceed
        can_proceed = current_count < rule.limit
        if can_proceed:
            self.fixed_windows[key][window_start] = current_count + 1
            current_count += 1

        reset_time = datetime.fromtimestamp(window_start + rule.window_seconds)

        return RateLimitStatus(
            rule_name=rule.name,
            current_count=current_count,
            limit=rule.limit,
            window_seconds=rule.window_seconds,
            reset_time=reset_time,
            remaining=max(0, rule.limit - current_count),
            is_limited=not can_proceed,
        )

    def _check_adaptive(
        self, rule: RateLimitRule, key: str, user_id: str = None, ip_address: str = None, endpoint: str = None
    ) -> RateLimitStatus:
        """Check adaptive rate limit"""
        if key not in self.adaptive_state:
            self.adaptive_state[key] = {
                "current_limit": rule.limit,
                "success_rate": 1.0,
                "error_count": 0,
                "total_requests": 0,
                "last_adjustment": time.time(),
            }

        state = self.adaptive_state[key]

        # Adjust limit based on success rate and load
        now = time.time()
        if now - state["last_adjustment"] > 300:  # Adjust every 5 minutes
            self._adjust_adaptive_limit(rule, state)
            state["last_adjustment"] = now

        # Use sliding window with current adaptive limit
        temp_rule = RateLimitRule(
            name=rule.name,
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            scope=rule.scope,
            limit=int(state["current_limit"]),
            window_seconds=rule.window_seconds,
        )

        return self._check_sliding_window(temp_rule, key)

    def _adjust_adaptive_limit(self, rule: RateLimitRule, state: dict):
        """Adjust adaptive rate limit based on performance"""
        if state["total_requests"] == 0:
            return

        success_rate = 1.0 - (state["error_count"] / state["total_requests"])

        # Increase limit if success rate is high
        if success_rate > 0.95 and state["current_limit"] < rule.max_limit:
            adjustment = state["current_limit"] * rule.adjustment_factor
            state["current_limit"] = min(rule.max_limit, state["current_limit"] + adjustment)

        # Decrease limit if success rate is low
        elif success_rate < 0.85 and state["current_limit"] > rule.min_limit:
            adjustment = state["current_limit"] * rule.adjustment_factor
            state["current_limit"] = max(rule.min_limit, state["current_limit"] - adjustment)

        # Reset counters
        state["error_count"] = 0
        state["total_requests"] = 0

    def record_request_result(self, identifier: str, success: bool, rule_names: List[str] = None):
        """Record the result of a request for adaptive rate limiting"""
        if rule_names is None:
            rule_names = [name for name, rule in self.rules.items() if rule.strategy == RateLimitStrategy.ADAPTIVE]

        for rule_name in rule_names:
            rule = self.rules.get(rule_name)
            if not rule or rule.strategy != RateLimitStrategy.ADAPTIVE:
                continue

            key = f"{rule_name}:{identifier}"
            if key in self.adaptive_state:
                state = self.adaptive_state[key]
                state["total_requests"] += 1
                if not success:
                    state["error_count"] += 1

    def get_violations(self, hours: int = 24) -> List[RateLimitViolation]:
        """Get recent rate limit violations"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [v for v in self.violations if v.timestamp > cutoff]

    def get_statistics(self) -> Dict[str, any]:
        """Get rate limiting statistics"""
        now = datetime.utcnow()
        recent_violations = self.get_violations(24)

        stats = {
            "total_rules": len(self.rules),
            "active_penalties": len(self.penalties),
            "violations_24h": len(recent_violations),
            "active_buckets": len(self.buckets),
            "active_counters": len(self.counters),
            "violations_by_rule": {},
        }

        # Group violations by rule
        for violation in recent_violations:
            rule_name = violation.rule_name
            if rule_name not in stats["violations_by_rule"]:
                stats["violations_by_rule"][rule_name] = 0
            stats["violations_by_rule"][rule_name] += 1

        return stats


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(rule_names: List[str] = None, identifier_func: Callable = None):
    """Decorator for rate limiting Azure Functions"""

    def decorator(func):
        @wraps(func)
        async def wrapper(req: func.HttpRequest, *args, **kwargs):
            try:
                # Extract context
                user_id = req.headers.get("X-User-ID")
                ip_address = req.headers.get("X-Forwarded-For", req.headers.get("X-Real-IP", "unknown"))
                endpoint = req.url.split("?")[0]  # Remove query params

                # Get identifier
                if identifier_func:
                    identifier = identifier_func(req)
                else:
                    identifier = user_id or ip_address

                # Check rate limits
                is_allowed, statuses = rate_limiter.check_rate_limit(
                    identifier=identifier, rule_names=rule_names, user_id=user_id, ip_address=ip_address, endpoint=endpoint
                )

                if not is_allowed:
                    # Return rate limit error
                    error_response = {"error": "Rate limit exceeded", "code": "RATE_LIMIT_EXCEEDED", "details": []}

                    for status in statuses:
                        if status.is_limited:
                            error_response["details"].append(
                                {
                                    "rule": status.rule_name,
                                    "limit": status.limit,
                                    "window_seconds": status.window_seconds,
                                    "reset_time": status.reset_time.isoformat(),
                                    "retry_after_seconds": (status.reset_time - datetime.utcnow()).total_seconds(),
                                }
                            )

                    # Add rate limit headers
                    headers = {
                        "Content-Type": "application/json",
                        "X-RateLimit-Limit": str(min(s.limit for s in statuses)),
                        "X-RateLimit-Remaining": str(min(s.remaining for s in statuses)),
                        "X-RateLimit-Reset": str(int(min(s.reset_time.timestamp() for s in statuses))),
                        "Retry-After": str(
                            int(max((s.reset_time - datetime.utcnow()).total_seconds() for s in statuses if s.is_limited))
                        ),
                    }

                    return func.HttpResponse(json.dumps(error_response), status_code=429, headers=headers)

                # Execute function
                start_time = time.time()
                try:
                    result = await func(req, *args, **kwargs)
                    success = True
                except Exception as e:
                    success = False
                    raise
                finally:
                    # Record result for adaptive rate limiting
                    rate_limiter.record_request_result(identifier, success, rule_names)

                # Add rate limit headers to successful responses
                if statuses:
                    min_remaining = min(s.remaining for s in statuses)
                    min_limit = min(s.limit for s in statuses)
                    earliest_reset = min(s.reset_time.timestamp() for s in statuses)

                    if hasattr(result, "headers"):
                        result.headers["X-RateLimit-Limit"] = str(min_limit)
                        result.headers["X-RateLimit-Remaining"] = str(min_remaining)
                        result.headers["X-RateLimit-Reset"] = str(int(earliest_reset))

                return result

            except Exception as e:
                logger.error(f"Error in rate limiting: {str(e)}")
                # Don't fail the request due to rate limiting errors
                return await func(req, *args, **kwargs)

        return wrapper

    return decorator
