"""
Rate Limiting System - Advanced rate limiting for Creator v1 (CRT4)
Provides multi-level rate limiting with quotas, burst handling, and intelligent backoff
"""

import logging
import time
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import json

from ...core.config import UmbraConfig
from .analytics import CreatorAnalytics
from .errors import CreatorError, RateLimitError

logger = logging.getLogger(__name__)

class LimitType(Enum):
    """Types of rate limits"""
    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    REQUESTS_PER_DAY = "requests_per_day"
    TOKENS_PER_MINUTE = "tokens_per_minute"
    TOKENS_PER_HOUR = "tokens_per_hour"
    COST_PER_DAY = "cost_per_day"
    COST_PER_MONTH = "cost_per_month"
    CONCURRENT_REQUESTS = "concurrent_requests"

class LimitScope(Enum):
    """Scope of rate limits"""
    GLOBAL = "global"
    USER = "user"
    ACTION = "action"
    PROVIDER = "provider"
    IP_ADDRESS = "ip"

@dataclass
class RateLimit:
    """Rate limit definition"""
    name: str
    limit_type: LimitType
    scope: LimitScope
    limit_value: Union[int, float]
    window_seconds: int
    burst_allowance: Optional[int] = None
    backoff_factor: float = 1.5
    max_backoff_seconds: int = 300
    enabled: bool = True
    grace_period_seconds: int = 0

@dataclass
class LimitUsage:
    """Current usage for a rate limit"""
    current_count: Union[int, float] = 0
    window_start: float = 0
    last_request_time: float = 0
    burst_used: int = 0
    backoff_until: float = 0
    total_blocked: int = 0
    recent_requests: deque = field(default_factory=lambda: deque(maxlen=1000))

@dataclass
class RateLimitResult:
    """Result of rate limit check"""
    allowed: bool
    limit_name: str
    current_usage: Union[int, float]
    limit_value: Union[int, float]
    reset_time: float
    retry_after_seconds: Optional[float] = None
    burst_available: Optional[int] = None
    backoff_applied: bool = False

class RateLimiter:
    """Advanced rate limiting system"""
    
    def __init__(self, config: UmbraConfig, analytics: Optional[CreatorAnalytics] = None):
        self.config = config
        self.analytics = analytics
        
        # Rate limiting configuration
        self.enabled = config.get("CREATOR_RATE_LIMITING_ENABLED", True)
        self.strict_mode = config.get("CREATOR_RATE_LIMITING_STRICT", False)
        self.logging_enabled = config.get("CREATOR_RATE_LIMITING_LOGGING", True)
        
        # Rate limits storage
        self.limits: Dict[str, RateLimit] = {}
        self.usage: Dict[Tuple[str, str], LimitUsage] = defaultdict(LimitUsage)
        
        # Global tracking
        self.concurrent_requests = 0
        self.max_concurrent = config.get("CREATOR_MAX_CONCURRENT_REQUESTS", 100)
        
        # Initialize default limits
        self._initialize_default_limits()
        
        # Cleanup task
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        logger.info(f"Rate limiter initialized (enabled: {self.enabled}, strict: {self.strict_mode})")
    
    def _initialize_default_limits(self):
        """Initialize default rate limits"""
        
        # Global request limits
        self.limits["global_requests_per_minute"] = RateLimit(
            name="global_requests_per_minute",
            limit_type=LimitType.REQUESTS_PER_MINUTE,
            scope=LimitScope.GLOBAL,
            limit_value=self.config.get("CREATOR_GLOBAL_REQUESTS_PER_MINUTE", 1000),
            window_seconds=60,
            burst_allowance=self.config.get("CREATOR_GLOBAL_BURST_ALLOWANCE", 50),
            enabled=True
        )
        
        self.limits["global_requests_per_hour"] = RateLimit(
            name="global_requests_per_hour",
            limit_type=LimitType.REQUESTS_PER_HOUR,
            scope=LimitScope.GLOBAL,
            limit_value=self.config.get("CREATOR_GLOBAL_REQUESTS_PER_HOUR", 10000),
            window_seconds=3600,
            enabled=True
        )
        
        # User-specific limits
        self.limits["user_requests_per_minute"] = RateLimit(
            name="user_requests_per_minute",
            limit_type=LimitType.REQUESTS_PER_MINUTE,
            scope=LimitScope.USER,
            limit_value=self.config.get("CREATOR_USER_REQUESTS_PER_MINUTE", 60),
            window_seconds=60,
            burst_allowance=10,
            enabled=True
        )
        
        self.limits["user_requests_per_hour"] = RateLimit(
            name="user_requests_per_hour",
            limit_type=LimitType.REQUESTS_PER_HOUR,
            scope=LimitScope.USER,
            limit_value=self.config.get("CREATOR_USER_REQUESTS_PER_HOUR", 1000),
            window_seconds=3600,
            enabled=True
        )
        
        # Token-based limits
        self.limits["user_tokens_per_minute"] = RateLimit(
            name="user_tokens_per_minute",
            limit_type=LimitType.TOKENS_PER_MINUTE,
            scope=LimitScope.USER,
            limit_value=self.config.get("CREATOR_USER_TOKENS_PER_MINUTE", 50000),
            window_seconds=60,
            enabled=True
        )
        
        # Cost-based limits
        self.limits["user_cost_per_day"] = RateLimit(
            name="user_cost_per_day",
            limit_type=LimitType.COST_PER_DAY,
            scope=LimitScope.USER,
            limit_value=self.config.get("CREATOR_USER_COST_LIMIT_USD", 10.0),
            window_seconds=86400,  # 24 hours
            enabled=True
        )
        
        # Action-specific limits
        self.limits["image_generation_per_minute"] = RateLimit(
            name="image_generation_per_minute",
            limit_type=LimitType.REQUESTS_PER_MINUTE,
            scope=LimitScope.ACTION,
            limit_value=self.config.get("CREATOR_IMAGE_REQUESTS_PER_MINUTE", 10),
            window_seconds=60,
            burst_allowance=3,
            enabled=True
        )
        
        self.limits["video_generation_per_hour"] = RateLimit(
            name="video_generation_per_hour",
            limit_type=LimitType.REQUESTS_PER_HOUR,
            scope=LimitScope.ACTION,
            limit_value=self.config.get("CREATOR_VIDEO_REQUESTS_PER_HOUR", 20),
            window_seconds=3600,
            enabled=True
        )
        
        # Concurrent request limit
        self.limits["concurrent_requests"] = RateLimit(
            name="concurrent_requests",
            limit_type=LimitType.CONCURRENT_REQUESTS,
            scope=LimitScope.GLOBAL,
            limit_value=self.max_concurrent,
            window_seconds=0,  # Not applicable for concurrent limits
            enabled=True
        )
    
    async def check_rate_limit(self, identifier: str, action: str, 
                             user_id: Optional[str] = None, 
                             tokens: Optional[int] = None,
                             cost: Optional[float] = None,
                             ip_address: Optional[str] = None) -> RateLimitResult:
        """Check if request is within rate limits"""
        if not self.enabled:
            return RateLimitResult(
                allowed=True,
                limit_name="disabled",
                current_usage=0,
                limit_value=float('inf'),
                reset_time=time.time()
            )
        
        current_time = time.time()
        
        # Check concurrent requests first
        if self.concurrent_requests >= self.max_concurrent:
            return RateLimitResult(
                allowed=False,
                limit_name="concurrent_requests",
                current_usage=self.concurrent_requests,
                limit_value=self.max_concurrent,
                reset_time=current_time,
                retry_after_seconds=1.0
            )
        
        # Check all applicable limits
        applicable_limits = self._get_applicable_limits(action, user_id, ip_address)
        
        for limit in applicable_limits:
            scope_key = self._get_scope_key(limit, identifier, user_id, action, ip_address)
            usage = self.usage[(limit.name, scope_key)]
            
            # Check if in backoff period
            if usage.backoff_until > current_time:
                return RateLimitResult(
                    allowed=False,
                    limit_name=limit.name,
                    current_usage=usage.current_count,
                    limit_value=limit.limit_value,
                    reset_time=usage.backoff_until,
                    retry_after_seconds=usage.backoff_until - current_time,
                    backoff_applied=True
                )
            
            # Check limit based on type
            limit_result = self._check_specific_limit(limit, usage, current_time, tokens, cost)
            
            if not limit_result.allowed:
                # Apply backoff if strict mode
                if self.strict_mode and not limit_result.backoff_applied:
                    self._apply_backoff(usage, limit)
                
                # Track rate limit hit
                usage.total_blocked += 1
                
                if self.analytics:
                    self.analytics.track_event(
                        event_type="rate_limit",
                        action=action,
                        metadata={
                            "limit_name": limit.name,
                            "user_id": user_id,
                            "current_usage": limit_result.current_usage,
                            "limit_value": limit_result.limit_value
                        }
                    )
                
                if self.logging_enabled:
                    logger.warning(f"Rate limit exceeded: {limit.name} for {scope_key}")
                
                return limit_result
        
        # All limits passed
        return RateLimitResult(
            allowed=True,
            limit_name="all_passed",
            current_usage=0,
            limit_value=float('inf'),
            reset_time=current_time
        )
    
    async def record_request(self, identifier: str, action: str,
                           user_id: Optional[str] = None,
                           tokens: Optional[int] = None,
                           cost: Optional[float] = None,
                           ip_address: Optional[str] = None) -> None:
        """Record successful request for rate limiting"""
        if not self.enabled:
            return
        
        current_time = time.time()
        self.concurrent_requests += 1
        
        # Update usage for all applicable limits
        applicable_limits = self._get_applicable_limits(action, user_id, ip_address)
        
        for limit in applicable_limits:
            scope_key = self._get_scope_key(limit, identifier, user_id, action, ip_address)
            usage = self.usage[(limit.name, scope_key)]
            
            # Reset window if needed
            if limit.limit_type != LimitType.CONCURRENT_REQUESTS:
                if current_time - usage.window_start >= limit.window_seconds:
                    usage.current_count = 0
                    usage.window_start = current_time
                    usage.burst_used = 0
            
            # Update count based on limit type
            if limit.limit_type in [LimitType.REQUESTS_PER_MINUTE, LimitType.REQUESTS_PER_HOUR, LimitType.REQUESTS_PER_DAY]:
                usage.current_count += 1
            elif limit.limit_type in [LimitType.TOKENS_PER_MINUTE, LimitType.TOKENS_PER_HOUR] and tokens:
                usage.current_count += tokens
            elif limit.limit_type in [LimitType.COST_PER_DAY, LimitType.COST_PER_MONTH] and cost:
                usage.current_count += cost
            
            usage.last_request_time = current_time
            usage.recent_requests.append(current_time)
    
    async def release_request(self, identifier: str) -> None:
        """Release concurrent request slot"""
        if self.concurrent_requests > 0:
            self.concurrent_requests -= 1
    
    def _get_applicable_limits(self, action: str, user_id: Optional[str], 
                             ip_address: Optional[str]) -> List[RateLimit]:
        """Get limits applicable to this request"""
        applicable = []
        
        for limit in self.limits.values():
            if not limit.enabled:
                continue
            
            if limit.scope == LimitScope.GLOBAL:
                applicable.append(limit)
            elif limit.scope == LimitScope.USER and user_id:
                applicable.append(limit)
            elif limit.scope == LimitScope.ACTION:
                # Check if limit applies to this action
                action_mapping = {
                    "image_generation_per_minute": ["generate_image", "edit_image"],
                    "video_generation_per_hour": ["generate_video"],
                }
                
                if limit.name in action_mapping:
                    if action in action_mapping[limit.name]:
                        applicable.append(limit)
                else:
                    # Generic action limit
                    applicable.append(limit)
            elif limit.scope == LimitScope.IP_ADDRESS and ip_address:
                applicable.append(limit)
        
        return applicable
    
    def _get_scope_key(self, limit: RateLimit, identifier: str, user_id: Optional[str],
                      action: str, ip_address: Optional[str]) -> str:
        """Get unique key for limit scope"""
        if limit.scope == LimitScope.GLOBAL:
            return "global"
        elif limit.scope == LimitScope.USER:
            return user_id or identifier
        elif limit.scope == LimitScope.ACTION:
            return f"{action}:{user_id or identifier}"
        elif limit.scope == LimitScope.PROVIDER:
            return f"provider:{identifier}"
        elif limit.scope == LimitScope.IP_ADDRESS:
            return ip_address or "unknown_ip"
        else:
            return identifier
    
    def _check_specific_limit(self, limit: RateLimit, usage: LimitUsage, 
                            current_time: float, tokens: Optional[int], 
                            cost: Optional[float]) -> RateLimitResult:
        """Check specific limit type"""
        if limit.limit_type == LimitType.CONCURRENT_REQUESTS:
            return RateLimitResult(
                allowed=self.concurrent_requests < limit.limit_value,
                limit_name=limit.name,
                current_usage=self.concurrent_requests,
                limit_value=limit.limit_value,
                reset_time=current_time
            )
        
        # Check if window needs reset
        if current_time - usage.window_start >= limit.window_seconds:
            usage.current_count = 0
            usage.window_start = current_time
            usage.burst_used = 0
        
        # Determine the increment for this request
        increment = 1
        if limit.limit_type in [LimitType.TOKENS_PER_MINUTE, LimitType.TOKENS_PER_HOUR]:
            increment = tokens or 0
        elif limit.limit_type in [LimitType.COST_PER_DAY, LimitType.COST_PER_MONTH]:
            increment = cost or 0
        
        projected_usage = usage.current_count + increment
        
        # Check if within regular limit
        if projected_usage <= limit.limit_value:
            return RateLimitResult(
                allowed=True,
                limit_name=limit.name,
                current_usage=usage.current_count,
                limit_value=limit.limit_value,
                reset_time=usage.window_start + limit.window_seconds
            )
        
        # Check burst allowance
        if limit.burst_allowance and usage.burst_used < limit.burst_allowance:
            burst_remaining = limit.burst_allowance - usage.burst_used
            if increment <= burst_remaining:
                return RateLimitResult(
                    allowed=True,
                    limit_name=limit.name,
                    current_usage=usage.current_count,
                    limit_value=limit.limit_value,
                    reset_time=usage.window_start + limit.window_seconds,
                    burst_available=burst_remaining - increment
                )
        
        # Limit exceeded
        window_remaining = (usage.window_start + limit.window_seconds) - current_time
        retry_after = max(1.0, window_remaining)
        
        return RateLimitResult(
            allowed=False,
            limit_name=limit.name,
            current_usage=usage.current_count,
            limit_value=limit.limit_value,
            reset_time=usage.window_start + limit.window_seconds,
            retry_after_seconds=retry_after
        )
    
    def _apply_backoff(self, usage: LimitUsage, limit: RateLimit) -> None:
        """Apply exponential backoff"""
        backoff_duration = min(
            limit.backoff_factor ** (usage.total_blocked + 1),
            limit.max_backoff_seconds
        )
        usage.backoff_until = time.time() + backoff_duration
        
        if self.logging_enabled:
            logger.info(f"Applied backoff: {backoff_duration}s for limit {limit.name}")
    
    def add_custom_limit(self, limit: RateLimit) -> None:
        """Add custom rate limit"""
        self.limits[limit.name] = limit
        logger.info(f"Added custom rate limit: {limit.name}")
    
    def remove_limit(self, limit_name: str) -> bool:
        """Remove rate limit"""
        if limit_name in self.limits:
            del self.limits[limit_name]
            logger.info(f"Removed rate limit: {limit_name}")
            return True
        return False
    
    def update_limit(self, limit_name: str, **kwargs) -> bool:
        """Update existing rate limit"""
        if limit_name not in self.limits:
            return False
        
        limit = self.limits[limit_name]
        
        for key, value in kwargs.items():
            if hasattr(limit, key):
                setattr(limit, key, value)
        
        logger.info(f"Updated rate limit: {limit_name}")
        return True
    
    def get_usage_stats(self, scope_key: Optional[str] = None) -> Dict[str, Any]:
        """Get usage statistics"""
        stats = {
            "total_limits": len(self.limits),
            "enabled_limits": len([l for l in self.limits.values() if l.enabled]),
            "current_concurrent": self.concurrent_requests,
            "max_concurrent": self.max_concurrent,
            "active_scopes": len(self.usage),
            "limits_overview": {}
        }
        
        # Aggregate stats by limit
        for limit_name, limit in self.limits.items():
            limit_stats = {
                "type": limit.limit_type.value,
                "scope": limit.scope.value,
                "limit_value": limit.limit_value,
                "window_seconds": limit.window_seconds,
                "enabled": limit.enabled,
                "active_users": 0,
                "total_blocked": 0,
                "current_usage": {}
            }
            
            # Collect usage data for this limit
            for (usage_limit_name, usage_scope_key), usage in self.usage.items():
                if usage_limit_name == limit_name:
                    limit_stats["active_users"] += 1
                    limit_stats["total_blocked"] += usage.total_blocked
                    
                    if scope_key is None or usage_scope_key == scope_key:
                        limit_stats["current_usage"][usage_scope_key] = {
                            "current_count": usage.current_count,
                            "window_start": usage.window_start,
                            "last_request": usage.last_request_time,
                            "total_blocked": usage.total_blocked,
                            "recent_requests": len(usage.recent_requests)
                        }
            
            stats["limits_overview"][limit_name] = limit_stats
        
        return stats
    
    def reset_usage(self, limit_name: Optional[str] = None, scope_key: Optional[str] = None) -> int:
        """Reset usage statistics"""
        reset_count = 0
        
        to_remove = []
        for (usage_limit_name, usage_scope_key), usage in self.usage.items():
            should_reset = True
            
            if limit_name and usage_limit_name != limit_name:
                should_reset = False
            
            if scope_key and usage_scope_key != scope_key:
                should_reset = False
            
            if should_reset:
                to_remove.append((usage_limit_name, usage_scope_key))
                reset_count += 1
        
        for key in to_remove:
            del self.usage[key]
        
        logger.info(f"Reset {reset_count} usage records")
        return reset_count
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old usage data"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                current_time = time.time()
                cleanup_threshold = current_time - 86400  # Remove data older than 24 hours
                
                to_remove = []
                for key, usage in self.usage.items():
                    if usage.last_request_time < cleanup_threshold:
                        to_remove.append(key)
                
                for key in to_remove:
                    del self.usage[key]
                
                if to_remove:
                    logger.info(f"Cleaned up {len(to_remove)} old usage records")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Rate limiter cleanup failed: {e}")
    
    def get_limit_config(self) -> Dict[str, Any]:
        """Get current rate limit configuration"""
        return {
            "enabled": self.enabled,
            "strict_mode": self.strict_mode,
            "max_concurrent": self.max_concurrent,
            "limits": {
                name: {
                    "type": limit.limit_type.value,
                    "scope": limit.scope.value,
                    "limit_value": limit.limit_value,
                    "window_seconds": limit.window_seconds,
                    "burst_allowance": limit.burst_allowance,
                    "enabled": limit.enabled
                }
                for name, limit in self.limits.items()
            }
        }
    
    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'cleanup_task') and self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()

# Context manager for rate limiting
class RateLimitedOperation:
    """Context manager for rate-limited operations"""
    
    def __init__(self, rate_limiter: RateLimiter, identifier: str, action: str, **kwargs):
        self.rate_limiter = rate_limiter
        self.identifier = identifier
        self.action = action
        self.kwargs = kwargs
        self.allowed = False
    
    async def __aenter__(self):
        result = await self.rate_limiter.check_rate_limit(
            self.identifier, self.action, **self.kwargs
        )
        
        if not result.allowed:
            if result.retry_after_seconds:
                raise RateLimitError(
                    f"Rate limit exceeded for {result.limit_name}. "
                    f"Retry after {result.retry_after_seconds:.1f} seconds.",
                    limit_name=result.limit_name,
                    retry_after=result.retry_after_seconds,
                    current_usage=result.current_usage,
                    limit_value=result.limit_value
                )
            else:
                raise RateLimitError(
                    f"Rate limit exceeded for {result.limit_name}",
                    limit_name=result.limit_name,
                    current_usage=result.current_usage,
                    limit_value=result.limit_value
                )
        
        self.allowed = True
        await self.rate_limiter.record_request(
            self.identifier, self.action, **self.kwargs
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.allowed:
            await self.rate_limiter.release_request(self.identifier)

# Decorator for rate limiting
def rate_limited(rate_limiter: RateLimiter, action: str, 
                identifier_func: Optional[callable] = None):
    """Decorator for rate limiting functions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract identifier
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                identifier = f"{func.__name__}_{id(args)}"
            
            # Extract additional rate limit parameters
            user_id = kwargs.get('user_id')
            tokens = kwargs.get('tokens')
            cost = kwargs.get('cost')
            
            async with RateLimitedOperation(
                rate_limiter, identifier, action, 
                user_id=user_id, tokens=tokens, cost=cost
            ):
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Custom exception for rate limiting
class RateLimitError(CreatorError):
    """Rate limit exceeded error"""
    
    def __init__(self, message: str, limit_name: str = None, retry_after: float = None,
                 current_usage: Union[int, float] = None, limit_value: Union[int, float] = None):
        super().__init__(message)
        self.limit_name = limit_name
        self.retry_after = retry_after
        self.current_usage = current_usage
        self.limit_value = limit_value
