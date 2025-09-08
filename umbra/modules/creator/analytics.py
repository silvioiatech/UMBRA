"""
Analytics and Monitoring - Track usage, performance, and costs for Creator module
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum

from ...core.config import UmbraConfig

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Types of tracked events"""
    GENERATION_START = "generation_start"
    GENERATION_COMPLETE = "generation_complete"
    GENERATION_ERROR = "generation_error"
    PROVIDER_SWITCH = "provider_switch"
    COST_INCURRED = "cost_incurred"
    RATE_LIMIT = "rate_limit"
    VALIDATION_FAILED = "validation_failed"
    TEMPLATE_USED = "template_used"
    EXPORT_CREATED = "export_created"

@dataclass
class Event:
    """Analytics event"""
    timestamp: float
    event_type: EventType
    action: str
    provider: Optional[str]
    model: Optional[str]
    success: bool
    duration_ms: Optional[float]
    cost_usd: Optional[float]
    tokens_used: Optional[int]
    metadata: Dict[str, Any]
    error_type: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class ProviderStats:
    """Provider performance statistics"""
    provider_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_cost_usd: float
    avg_response_time_ms: float
    total_tokens: int
    last_used: datetime
    error_types: Dict[str, int]

@dataclass
class ActionStats:
    """Action performance statistics"""
    action_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_cost_usd: float
    avg_response_time_ms: float
    median_response_time_ms: float
    p95_response_time_ms: float
    total_tokens: int
    popular_providers: Dict[str, int]

class CreatorAnalytics:
    """Analytics and monitoring for Creator module"""
    
    def __init__(self, config: UmbraConfig):
        self.config = config
        
        # Analytics settings
        self.enabled = config.get("CREATOR_ANALYTICS_ENABLED", True)
        self.retention_days = config.get("CREATOR_ANALYTICS_RETENTION_DAYS", 30)
        self.cost_tracking = config.get("CREATOR_COST_TRACKING_ENABLED", True)
        self.cost_alert_threshold = config.get("CREATOR_COST_ALERT_THRESHOLD_USD", 100.0)
        self.performance_monitoring = config.get("CREATOR_PERFORMANCE_MONITORING", True)
        self.slow_request_threshold = config.get("CREATOR_SLOW_REQUEST_THRESHOLD_MS", 5000)
        
        # Event storage (in-memory for now, could be moved to persistent storage)
        self.events = deque(maxlen=10000)  # Keep last 10k events
        self.daily_stats = defaultdict(lambda: {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_cost_usd": 0.0,
            "total_tokens": 0,
            "actions": defaultdict(int),
            "providers": defaultdict(int),
            "errors": defaultdict(int)
        })
        
        # Performance tracking
        self.response_times = defaultdict(lambda: deque(maxlen=1000))  # Last 1k per action
        self.provider_performance = defaultdict(lambda: {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "total_time": 0,
            "total_cost": 0,
            "errors": defaultdict(int)
        })
        
        # Cost tracking
        self.daily_costs = defaultdict(float)
        self.monthly_costs = defaultdict(float)
        self.provider_costs = defaultdict(float)
        
        logger.info(f"Creator analytics initialized (enabled: {self.enabled})")
    
    def track_event(self, event: Event) -> None:
        """Track an analytics event"""
        if not self.enabled:
            return
        
        try:
            # Add to events
            self.events.append(event)
            
            # Update daily stats
            today = datetime.now().strftime("%Y-%m-%d")
            daily = self.daily_stats[today]
            
            daily["total_requests"] += 1
            if event.success:
                daily["successful_requests"] += 1
            else:
                daily["failed_requests"] += 1
                if event.error_type:
                    daily["errors"][event.error_type] += 1
            
            if event.cost_usd:
                daily["total_cost_usd"] += event.cost_usd
                self.daily_costs[today] += event.cost_usd
                
                # Monthly cost tracking
                month = datetime.now().strftime("%Y-%m")
                self.monthly_costs[month] += event.cost_usd
                
                # Provider cost tracking
                if event.provider:
                    self.provider_costs[event.provider] += event.cost_usd
            
            if event.tokens_used:
                daily["total_tokens"] += event.tokens_used
            
            daily["actions"][event.action] += 1
            if event.provider:
                daily["providers"][event.provider] += 1
            
            # Update performance tracking
            if event.duration_ms is not None:
                self.response_times[event.action].append(event.duration_ms)
                
                # Check for slow requests
                if (self.performance_monitoring and 
                    event.duration_ms > self.slow_request_threshold):
                    logger.warning(f"Slow request detected: {event.action} took {event.duration_ms}ms")
            
            # Update provider performance
            if event.provider:
                perf = self.provider_performance[event.provider]
                perf["requests"] += 1
                
                if event.success:
                    perf["successes"] += 1
                else:
                    perf["failures"] += 1
                    if event.error_type:
                        perf["errors"][event.error_type] += 1
                
                if event.duration_ms:
                    perf["total_time"] += event.duration_ms
                
                if event.cost_usd:
                    perf["total_cost"] += event.cost_usd
            
            # Cost alerts
            if (self.cost_tracking and event.cost_usd and 
                self.daily_costs[today] > self.cost_alert_threshold):
                logger.warning(f"Daily cost threshold exceeded: ${self.daily_costs[today]:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to track analytics event: {e}")
    
    def track_generation_start(self, action: str, provider: str = None, 
                             metadata: Dict[str, Any] = None, user_id: str = None) -> str:
        """Track the start of a generation request"""
        event_id = f"{action}_{time.time()}"
        
        event = Event(
            timestamp=time.time(),
            event_type=EventType.GENERATION_START,
            action=action,
            provider=provider,
            model=metadata.get("model") if metadata else None,
            success=True,  # Start event is always successful
            duration_ms=None,
            cost_usd=None,
            tokens_used=None,
            metadata=metadata or {},
            user_id=user_id,
            session_id=metadata.get("session_id") if metadata else None
        )
        
        self.track_event(event)
        return event_id
    
    def track_generation_complete(self, action: str, provider: str, model: str,
                                duration_ms: float, cost_usd: float = None,
                                tokens_used: int = None, metadata: Dict[str, Any] = None,
                                user_id: str = None) -> None:
        """Track successful generation completion"""
        event = Event(
            timestamp=time.time(),
            event_type=EventType.GENERATION_COMPLETE,
            action=action,
            provider=provider,
            model=model,
            success=True,
            duration_ms=duration_ms,
            cost_usd=cost_usd,
            tokens_used=tokens_used,
            metadata=metadata or {},
            user_id=user_id
        )
        
        self.track_event(event)
    
    def track_generation_error(self, action: str, provider: str, error_type: str,
                             duration_ms: float = None, metadata: Dict[str, Any] = None,
                             user_id: str = None) -> None:
        """Track generation error"""
        event = Event(
            timestamp=time.time(),
            event_type=EventType.GENERATION_ERROR,
            action=action,
            provider=provider,
            model=None,
            success=False,
            duration_ms=duration_ms,
            cost_usd=None,
            tokens_used=None,
            metadata=metadata or {},
            error_type=error_type,
            user_id=user_id
        )
        
        self.track_event(event)
    
    def track_provider_switch(self, action: str, from_provider: str, to_provider: str,
                            reason: str, metadata: Dict[str, Any] = None) -> None:
        """Track provider failover/switching"""
        event = Event(
            timestamp=time.time(),
            event_type=EventType.PROVIDER_SWITCH,
            action=action,
            provider=to_provider,
            model=None,
            success=True,
            duration_ms=None,
            cost_usd=None,
            tokens_used=None,
            metadata={
                "from_provider": from_provider,
                "reason": reason,
                **(metadata or {})
            }
        )
        
        self.track_event(event)
    
    def track_cost(self, action: str, provider: str, cost_usd: float,
                  tokens_used: int = None, metadata: Dict[str, Any] = None) -> None:
        """Track cost incurrence"""
        event = Event(
            timestamp=time.time(),
            event_type=EventType.COST_INCURRED,
            action=action,
            provider=provider,
            model=metadata.get("model") if metadata else None,
            success=True,
            duration_ms=None,
            cost_usd=cost_usd,
            tokens_used=tokens_used,
            metadata=metadata or {}
        )
        
        self.track_event(event)
    
    def get_daily_stats(self, date: str = None) -> Dict[str, Any]:
        """Get statistics for a specific day"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        return dict(self.daily_stats.get(date, {}))
    
    def get_weekly_stats(self, weeks_back: int = 1) -> Dict[str, Any]:
        """Get aggregated statistics for the past N weeks"""
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks_back)
        
        weekly_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_cost_usd": 0.0,
            "total_tokens": 0,
            "actions": defaultdict(int),
            "providers": defaultdict(int),
            "errors": defaultdict(int),
            "daily_breakdown": {}
        }
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            daily_data = self.daily_stats.get(date_str, {})
            
            weekly_stats["daily_breakdown"][date_str] = daily_data
            
            # Aggregate
            for key in ["total_requests", "successful_requests", "failed_requests", "total_cost_usd", "total_tokens"]:
                weekly_stats[key] += daily_data.get(key, 0)
            
            # Aggregate nested dictionaries
            for action, count in daily_data.get("actions", {}).items():
                weekly_stats["actions"][action] += count
            
            for provider, count in daily_data.get("providers", {}).items():
                weekly_stats["providers"][provider] += count
            
            for error, count in daily_data.get("errors", {}).items():
                weekly_stats["errors"][error] += count
            
            current_date += timedelta(days=1)
        
        return dict(weekly_stats)
    
    def get_provider_stats(self) -> Dict[str, ProviderStats]:
        """Get performance statistics for all providers"""
        stats = {}
        
        for provider, perf in self.provider_performance.items():
            if perf["requests"] > 0:
                stats[provider] = ProviderStats(
                    provider_name=provider,
                    total_requests=perf["requests"],
                    successful_requests=perf["successes"],
                    failed_requests=perf["failures"],
                    total_cost_usd=perf["total_cost"],
                    avg_response_time_ms=perf["total_time"] / perf["requests"] if perf["requests"] > 0 else 0,
                    total_tokens=0,  # Would need to track this separately
                    last_used=datetime.now(),  # Placeholder
                    error_types=dict(perf["errors"])
                )
        
        return stats
    
    def get_action_stats(self) -> Dict[str, ActionStats]:
        """Get performance statistics for all actions"""
        stats = {}
        
        # Aggregate data by action
        action_data = defaultdict(lambda: {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "total_cost": 0,
            "response_times": [],
            "providers": defaultdict(int),
            "tokens": 0
        })
        
        for event in self.events:
            data = action_data[event.action]
            data["requests"] += 1
            
            if event.success:
                data["successes"] += 1
            else:
                data["failures"] += 1
            
            if event.cost_usd:
                data["total_cost"] += event.cost_usd
            
            if event.duration_ms is not None:
                data["response_times"].append(event.duration_ms)
            
            if event.provider:
                data["providers"][event.provider] += 1
            
            if event.tokens_used:
                data["tokens"] += event.tokens_used
        
        # Convert to ActionStats objects
        for action, data in action_data.items():
            response_times = sorted(data["response_times"])
            n = len(response_times)
            
            stats[action] = ActionStats(
                action_name=action,
                total_requests=data["requests"],
                successful_requests=data["successes"],
                failed_requests=data["failures"],
                total_cost_usd=data["total_cost"],
                avg_response_time_ms=sum(response_times) / n if n > 0 else 0,
                median_response_time_ms=response_times[n // 2] if n > 0 else 0,
                p95_response_time_ms=response_times[int(n * 0.95)] if n > 0 else 0,
                total_tokens=data["tokens"],
                popular_providers=dict(data["providers"])
            )
        
        return stats
    
    def get_cost_breakdown(self, period: str = "daily") -> Dict[str, Any]:
        """Get cost breakdown by period"""
        if period == "daily":
            return dict(self.daily_costs)
        elif period == "monthly":
            return dict(self.monthly_costs)
        elif period == "provider":
            return dict(self.provider_costs)
        else:
            return {}
    
    def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """Get current performance alerts"""
        alerts = []
        
        # Check for high error rates
        today = datetime.now().strftime("%Y-%m-%d")
        daily = self.daily_stats.get(today, {})
        
        total_requests = daily.get("total_requests", 0)
        failed_requests = daily.get("failed_requests", 0)
        
        if total_requests > 10 and failed_requests / total_requests > 0.1:  # >10% error rate
            alerts.append({
                "type": "high_error_rate",
                "message": f"High error rate today: {failed_requests}/{total_requests} ({failed_requests/total_requests*100:.1f}%)",
                "severity": "warning"
            })
        
        # Check for high costs
        daily_cost = self.daily_costs.get(today, 0)
        if daily_cost > self.cost_alert_threshold:
            alerts.append({
                "type": "high_cost",
                "message": f"Daily cost threshold exceeded: ${daily_cost:.2f}",
                "severity": "critical"
            })
        
        # Check for slow providers
        for provider, perf in self.provider_performance.items():
            if perf["requests"] > 5:  # Only check providers with reasonable volume
                avg_time = perf["total_time"] / perf["requests"]
                if avg_time > self.slow_request_threshold:
                    alerts.append({
                        "type": "slow_provider",
                        "message": f"Provider {provider} is slow: {avg_time:.0f}ms average",
                        "severity": "warning"
                    })
        
        return alerts
    
    def export_analytics(self, format: str = "json", period: str = "week") -> str:
        """Export analytics data in specified format"""
        try:
            if period == "week":
                data = self.get_weekly_stats()
            elif period == "month":
                data = self.get_weekly_stats(weeks_back=4)
            else:
                data = self.get_daily_stats()
            
            # Add additional context
            export_data = {
                "period": period,
                "exported_at": datetime.now().isoformat(),
                "stats": data,
                "provider_stats": {k: asdict(v) for k, v in self.get_provider_stats().items()},
                "action_stats": {k: asdict(v) for k, v in self.get_action_stats().items()},
                "cost_breakdown": self.get_cost_breakdown(),
                "alerts": self.get_performance_alerts()
            }
            
            if format == "json":
                return json.dumps(export_data, indent=2, default=str)
            else:
                # Could add CSV, HTML, or other formats
                return json.dumps(export_data, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to export analytics: {e}")
            return "{\"error\": \"Export failed\"}"
    
    def reset_stats(self, confirm: bool = False) -> bool:
        """Reset all analytics data (use with caution)"""
        if not confirm:
            logger.warning("Reset not confirmed - use reset_stats(confirm=True)")
            return False
        
        try:
            self.events.clear()
            self.daily_stats.clear()
            self.response_times.clear()
            self.provider_performance.clear()
            self.daily_costs.clear()
            self.monthly_costs.clear()
            self.provider_costs.clear()
            
            logger.info("Analytics data reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset analytics data: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status of the Creator module"""
        today = datetime.now().strftime("%Y-%m-%d")
        daily = self.daily_stats.get(today, {})
        
        total_requests = daily.get("total_requests", 0)
        failed_requests = daily.get("failed_requests", 0)
        
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        daily_cost = self.daily_costs.get(today, 0)
        
        # Determine health status
        if error_rate > 20 or daily_cost > self.cost_alert_threshold * 2:
            health = "critical"
        elif error_rate > 10 or daily_cost > self.cost_alert_threshold:
            health = "warning"
        elif total_requests > 0:
            health = "healthy"
        else:
            health = "unknown"
        
        return {
            "status": health,
            "error_rate_percent": round(error_rate, 2),
            "daily_cost_usd": round(daily_cost, 2),
            "total_requests_today": total_requests,
            "active_providers": len([p for p, perf in self.provider_performance.items() if perf["requests"] > 0]),
            "alerts_count": len(self.get_performance_alerts()),
            "last_updated": datetime.now().isoformat()
        }

# Context manager for automatic analytics tracking
class track_operation:
    """Context manager to automatically track generation operations"""
    
    def __init__(self, analytics: CreatorAnalytics, action: str, provider: str = None,
                 metadata: Dict[str, Any] = None, user_id: str = None):
        self.analytics = analytics
        self.action = action
        self.provider = provider
        self.metadata = metadata or {}
        self.user_id = user_id
        self.start_time = None
        self.event_id = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.event_id = self.analytics.track_generation_start(
            self.action, self.provider, self.metadata, self.user_id
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        duration_ms = (end_time - self.start_time) * 1000
        
        if exc_type is None:
            # Success
            self.analytics.track_generation_complete(
                action=self.action,
                provider=self.provider or "unknown",
                model=self.metadata.get("model", "unknown"),
                duration_ms=duration_ms,
                cost_usd=self.metadata.get("cost"),
                tokens_used=self.metadata.get("tokens"),
                metadata=self.metadata,
                user_id=self.user_id
            )
        else:
            # Error
            error_type = exc_type.__name__ if exc_type else "unknown"
            self.analytics.track_generation_error(
                action=self.action,
                provider=self.provider or "unknown",
                error_type=error_type,
                duration_ms=duration_ms,
                metadata={**self.metadata, "error_message": str(exc_val) if exc_val else ""},
                user_id=self.user_id
            )
        
        return False  # Don't suppress exceptions
