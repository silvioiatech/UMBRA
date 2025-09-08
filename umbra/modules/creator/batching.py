"""
Intelligent Batching System - Advanced request batching for Creator v1 (CRT4)
Optimizes API calls by intelligently batching similar requests together
"""

import logging
import time
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
from collections import defaultdict, deque

from ...core.config import UmbraConfig
from .analytics import CreatorAnalytics
from .errors import CreatorError, BatchingError

logger = logging.getLogger(__name__)

class BatchStrategy(Enum):
    """Batching strategies"""
    TIME_BASED = "time_based"          # Wait for time window
    SIZE_BASED = "size_based"          # Wait for batch size
    HYBRID = "hybrid"                  # Combination of time and size
    PRIORITY_BASED = "priority_based"  # Priority-driven batching
    ADAPTIVE = "adaptive"              # Adaptive based on load

class BatchPriority(Enum):
    """Request priorities"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class BatchRequest:
    """Individual request in a batch"""
    id: str
    action: str
    params: Dict[str, Any]
    user_id: Optional[str]
    priority: BatchPriority
    created_at: float
    timeout_at: float
    callback: Optional[Callable] = None
    context: Dict[str, Any] = field(default_factory=dict)
    estimated_cost: float = 0.0
    estimated_tokens: int = 0

@dataclass
class BatchJob:
    """Collection of requests to be processed together"""
    id: str
    action: str
    requests: List[BatchRequest]
    created_at: float
    processed_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: str = "pending"  # pending, processing, completed, failed
    results: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    total_cost: float = 0.0
    total_tokens: int = 0

@dataclass
class BatchConfig:
    """Configuration for a specific action's batching"""
    action: str
    enabled: bool = True
    strategy: BatchStrategy = BatchStrategy.HYBRID
    max_batch_size: int = 10
    max_wait_time_ms: int = 5000
    min_batch_size: int = 1
    priority_threshold: BatchPriority = BatchPriority.NORMAL
    cost_threshold: float = 1.0
    token_threshold: int = 10000
    similarity_threshold: float = 0.8
    merge_function: Optional[Callable] = None
    split_function: Optional[Callable] = None

class IntelligentBatcher:
    """Advanced request batching system"""
    
    def __init__(self, config: UmbraConfig, analytics: Optional[CreatorAnalytics] = None):
        self.config = config
        self.analytics = analytics
        
        # Batching configuration
        self.enabled = config.get("CREATOR_BATCHING_ENABLED", True)
        self.global_max_batch_size = config.get("CREATOR_GLOBAL_MAX_BATCH_SIZE", 20)
        self.global_max_wait_time_ms = config.get("CREATOR_GLOBAL_MAX_WAIT_TIME_MS", 10000)
        self.adaptive_enabled = config.get("CREATOR_BATCHING_ADAPTIVE", True)
        
        # Batch storage
        self.pending_requests: Dict[str, List[BatchRequest]] = defaultdict(list)
        self.active_batches: Dict[str, BatchJob] = {}
        self.completed_batches: deque = deque(maxlen=1000)
        
        # Configuration for different actions
        self.batch_configs: Dict[str, BatchConfig] = {}
        
        # Performance tracking
        self.batch_stats = {
            "total_batches": 0,
            "total_requests": 0,
            "avg_batch_size": 0.0,
            "avg_wait_time_ms": 0.0,
            "cost_savings": 0.0,
            "token_savings": 0
        }
        
        # Adaptive parameters
        self.load_history = deque(maxlen=100)
        self.response_time_history = deque(maxlen=100)
        
        # Initialize default configurations
        self._initialize_default_configs()
        
        # Start processing loops
        if self.enabled:
            self.batch_processor_task = asyncio.create_task(self._batch_processor_loop())
            self.adaptive_tuner_task = asyncio.create_task(self._adaptive_tuner_loop())
        
        logger.info(f"Intelligent batcher initialized (enabled: {self.enabled})")
    
    def _initialize_default_configs(self):
        """Initialize default batch configurations for common actions"""
        
        # Text generation batching
        self.batch_configs["generate_post"] = BatchConfig(
            action="generate_post",
            strategy=BatchStrategy.HYBRID,
            max_batch_size=5,
            max_wait_time_ms=3000,
            min_batch_size=2,
            cost_threshold=0.5,
            token_threshold=5000,
            similarity_threshold=0.7
        )
        
        self.batch_configs["generate_hashtags"] = BatchConfig(
            action="generate_hashtags",
            strategy=BatchStrategy.SIZE_BASED,
            max_batch_size=10,
            max_wait_time_ms=2000,
            min_batch_size=3,
            similarity_threshold=0.8
        )
        
        self.batch_configs["generate_title_variations"] = BatchConfig(
            action="generate_title_variations",
            strategy=BatchStrategy.TIME_BASED,
            max_batch_size=8,
            max_wait_time_ms=4000,
            min_batch_size=2
        )
        
        # Image generation batching
        self.batch_configs["generate_image"] = BatchConfig(
            action="generate_image",
            strategy=BatchStrategy.PRIORITY_BASED,
            max_batch_size=4,
            max_wait_time_ms=8000,
            min_batch_size=1,
            priority_threshold=BatchPriority.HIGH,
            cost_threshold=2.0,
            similarity_threshold=0.6
        )
        
        # Validation batching
        self.batch_configs["validate_content"] = BatchConfig(
            action="validate_content",
            strategy=BatchStrategy.SIZE_BASED,
            max_batch_size=15,
            max_wait_time_ms=1000,
            min_batch_size=5
        )
    
    async def add_request(self, action: str, params: Dict[str, Any], 
                         user_id: Optional[str] = None,
                         priority: BatchPriority = BatchPriority.NORMAL,
                         timeout_seconds: int = 30,
                         callback: Optional[Callable] = None,
                         context: Dict[str, Any] = None) -> str:
        """Add request to batching queue"""
        if not self.enabled:
            # If batching disabled, process immediately
            return await self._process_immediate(action, params, user_id, callback, context or {})
        
        # Generate unique request ID
        request_id = self._generate_request_id(action, params, user_id)
        
        # Create batch request
        request = BatchRequest(
            id=request_id,
            action=action,
            params=params,
            user_id=user_id,
            priority=priority,
            created_at=time.time(),
            timeout_at=time.time() + timeout_seconds,
            callback=callback,
            context=context or {},
            estimated_cost=self._estimate_request_cost(action, params),
            estimated_tokens=self._estimate_request_tokens(action, params)
        )
        
        # Add to pending queue
        self.pending_requests[action].append(request)
        
        # Check if immediate processing needed
        config = self.batch_configs.get(action)
        if config and self._should_process_immediately(action, request):
            await self._trigger_batch_processing(action)
        
        logger.debug(f"Added request {request_id} to batch queue for action {action}")
        return request_id
    
    async def _batch_processor_loop(self):
        """Main batch processing loop"""
        while self.enabled:
            try:
                current_time = time.time()
                
                # Check each action for ready batches
                for action in list(self.pending_requests.keys()):
                    if not self.pending_requests[action]:
                        continue
                    
                    config = self.batch_configs.get(action)
                    if not config or not config.enabled:
                        # Process immediately if no config
                        await self._process_unbatched_requests(action)
                        continue
                    
                    # Check if batch is ready
                    if self._is_batch_ready(action, current_time):
                        await self._process_batch(action)
                
                # Remove expired requests
                await self._cleanup_expired_requests(current_time)
                
                # Sleep briefly before next iteration
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Batch processor loop error: {e}")
                await asyncio.sleep(1)
    
    def _is_batch_ready(self, action: str, current_time: float) -> bool:
        """Check if batch is ready for processing"""
        requests = self.pending_requests[action]
        if not requests:
            return False
        
        config = self.batch_configs.get(action)
        if not config:
            return True
        
        # Size-based check
        if len(requests) >= config.max_batch_size:
            return True
        
        # Time-based check
        oldest_request = min(requests, key=lambda r: r.created_at)
        wait_time_ms = (current_time - oldest_request.created_at) * 1000
        
        if wait_time_ms >= config.max_wait_time_ms:
            return True
        
        # Priority-based check
        if config.strategy == BatchStrategy.PRIORITY_BASED:
            urgent_requests = [r for r in requests if r.priority == BatchPriority.URGENT]
            if urgent_requests:
                return True
        
        # Hybrid strategy check
        if config.strategy == BatchStrategy.HYBRID:
            if (len(requests) >= config.min_batch_size and 
                wait_time_ms >= config.max_wait_time_ms / 2):
                return True
        
        # Cost/token threshold check
        total_cost = sum(r.estimated_cost for r in requests)
        total_tokens = sum(r.estimated_tokens for r in requests)
        
        if (total_cost >= config.cost_threshold or 
            total_tokens >= config.token_threshold):
            return True
        
        return False
    
    def _should_process_immediately(self, action: str, request: BatchRequest) -> bool:
        """Check if request should bypass batching"""
        config = self.batch_configs.get(action)
        if not config:
            return True
        
        # Urgent priority always processes immediately
        if request.priority == BatchPriority.URGENT:
            return True
        
        # Check if timeout is very short
        if request.timeout_at - request.created_at < 1.0:
            return True
        
        # Check current load
        current_load = len(self.active_batches)
        if current_load > 10:  # High load, process immediately
            return True
        
        return False
    
    async def _process_batch(self, action: str):
        """Process a batch of requests"""
        requests = self.pending_requests[action]
        if not requests:
            return
        
        config = self.batch_configs.get(action)
        if not config:
            return await self._process_unbatched_requests(action)
        
        # Create batch job
        batch_id = self._generate_batch_id(action)
        
        # Sort requests by priority and creation time
        sorted_requests = sorted(
            requests,
            key=lambda r: (r.priority.value, -r.created_at),
            reverse=True
        )
        
        # Take up to max_batch_size requests
        batch_requests = sorted_requests[:config.max_batch_size]
        
        # Remove processed requests from pending
        for req in batch_requests:
            if req in self.pending_requests[action]:
                self.pending_requests[action].remove(req)
        
        # Create batch job
        batch = BatchJob(
            id=batch_id,
            action=action,
            requests=batch_requests,
            created_at=time.time()
        )
        
        self.active_batches[batch_id] = batch
        
        # Process batch
        try:
            await self._execute_batch(batch, config)
        except Exception as e:
            logger.error(f"Batch execution failed for {batch_id}: {e}")
            batch.status = "failed"
            
            # Handle individual request failures
            for request in batch.requests:
                if request.callback:
                    try:
                        await request.callback({
                            "success": False,
                            "error": f"Batch execution failed: {e}",
                            "request_id": request.id
                        })
                    except Exception as callback_error:
                        logger.error(f"Callback failed for request {request.id}: {callback_error}")
        
        finally:
            # Move to completed batches
            self.active_batches.pop(batch_id, None)
            self.completed_batches.append(batch)
            
            # Update stats
            self._update_batch_stats(batch)
    
    async def _execute_batch(self, batch: BatchJob, config: BatchConfig):
        """Execute a batch of requests"""
        batch.status = "processing"
        batch.processed_at = time.time()
        
        # Group similar requests if possible
        request_groups = self._group_similar_requests(batch.requests, config)
        
        # Process each group
        for group in request_groups:
            try:
                # Check if requests can be merged
                if config.merge_function and len(group) > 1:
                    merged_result = await self._process_merged_requests(group, config)
                    
                    # Split results back to individual requests
                    if config.split_function:
                        individual_results = config.split_function(merged_result, group)
                    else:
                        # Default: give same result to all
                        individual_results = {req.id: merged_result for req in group}
                else:
                    # Process requests individually
                    individual_results = {}
                    for request in group:
                        result = await self._process_single_request(request)
                        individual_results[request.id] = result
                
                # Store results and call callbacks
                for request in group:
                    result = individual_results.get(request.id, {
                        "success": False,
                        "error": "No result generated"
                    })
                    
                    batch.results[request.id] = result
                    
                    if request.callback:
                        await request.callback(result)
            
            except Exception as e:
                logger.error(f"Request group processing failed: {e}")
                
                # Mark all requests in group as failed
                for request in group:
                    error_result = {
                        "success": False,
                        "error": str(e),
                        "request_id": request.id
                    }
                    
                    batch.errors[request.id] = str(e)
                    
                    if request.callback:
                        try:
                            await request.callback(error_result)
                        except Exception as callback_error:
                            logger.error(f"Callback failed for request {request.id}: {callback_error}")
        
        batch.status = "completed"
        batch.completed_at = time.time()
    
    def _group_similar_requests(self, requests: List[BatchRequest], 
                              config: BatchConfig) -> List[List[BatchRequest]]:
        """Group similar requests together"""
        if config.similarity_threshold <= 0:
            return [[req] for req in requests]  # No grouping
        
        groups = []
        ungrouped = requests.copy()
        
        while ungrouped:
            current = ungrouped.pop(0)
            group = [current]
            
            # Find similar requests
            to_remove = []
            for req in ungrouped:
                if self._calculate_similarity(current, req) >= config.similarity_threshold:
                    group.append(req)
                    to_remove.append(req)
            
            # Remove grouped requests
            for req in to_remove:
                ungrouped.remove(req)
            
            groups.append(group)
        
        return groups
    
    def _calculate_similarity(self, req1: BatchRequest, req2: BatchRequest) -> float:
        """Calculate similarity between two requests"""
        if req1.action != req2.action:
            return 0.0
        
        # Compare parameters
        params1_str = json.dumps(req1.params, sort_keys=True, default=str)
        params2_str = json.dumps(req2.params, sort_keys=True, default=str)
        
        if params1_str == params2_str:
            return 1.0
        
        # Simple string-based similarity
        common_chars = sum(1 for a, b in zip(params1_str, params2_str) if a == b)
        max_length = max(len(params1_str), len(params2_str))
        
        if max_length == 0:
            return 1.0
        
        return common_chars / max_length
    
    async def _process_merged_requests(self, requests: List[BatchRequest], 
                                     config: BatchConfig) -> Dict[str, Any]:
        """Process multiple similar requests as one merged request"""
        # Use custom merge function if available
        if config.merge_function:
            return await config.merge_function(requests)
        
        # Default merge: combine parameters
        merged_params = {}
        for request in requests:
            for key, value in request.params.items():
                if key not in merged_params:
                    merged_params[key] = []
                if isinstance(value, list):
                    merged_params[key].extend(value)
                else:
                    merged_params[key].append(value)
        
        # Process as single request
        merged_request = BatchRequest(
            id="merged",
            action=requests[0].action,
            params=merged_params,
            user_id=requests[0].user_id,
            priority=max(req.priority for req in requests),
            created_at=min(req.created_at for req in requests),
            timeout_at=max(req.timeout_at for req in requests)
        )
        
        return await self._process_single_request(merged_request)
    
    async def _process_single_request(self, request: BatchRequest) -> Dict[str, Any]:
        """Process a single request"""
        try:
            # This would integrate with the actual Creator service
            # For now, return a placeholder result
            
            start_time = time.time()
            
            # Simulate processing
            await asyncio.sleep(0.1)
            
            processing_time = (time.time() - start_time) * 1000
            
            result = {
                "success": True,
                "request_id": request.id,
                "action": request.action,
                "processing_time_ms": processing_time,
                "data": f"Processed {request.action} with params {request.params}"
            }
            
            # Track analytics
            if self.analytics:
                self.analytics.track_generation_complete(
                    request.action,
                    "batch_processor",
                    "batch_model",
                    processing_time,
                    request.estimated_cost,
                    request.estimated_tokens
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Single request processing failed for {request.id}: {e}")
            return {
                "success": False,
                "request_id": request.id,
                "error": str(e)
            }
    
    async def _process_immediate(self, action: str, params: Dict[str, Any],
                               user_id: Optional[str], callback: Optional[Callable],
                               context: Dict[str, Any]) -> str:
        """Process request immediately without batching"""
        request_id = self._generate_request_id(action, params, user_id)
        
        request = BatchRequest(
            id=request_id,
            action=action,
            params=params,
            user_id=user_id,
            priority=BatchPriority.URGENT,
            created_at=time.time(),
            timeout_at=time.time() + 30,
            callback=callback,
            context=context
        )
        
        result = await self._process_single_request(request)
        
        if callback:
            await callback(result)
        
        return request_id
    
    async def _process_unbatched_requests(self, action: str):
        """Process requests without batching configuration"""
        requests = self.pending_requests[action].copy()
        self.pending_requests[action].clear()
        
        for request in requests:
            try:
                result = await self._process_single_request(request)
                if request.callback:
                    await request.callback(result)
            except Exception as e:
                logger.error(f"Unbatched request processing failed for {request.id}: {e}")
                if request.callback:
                    await request.callback({
                        "success": False,
                        "request_id": request.id,
                        "error": str(e)
                    })
    
    async def _cleanup_expired_requests(self, current_time: float):
        """Remove expired requests from queues"""
        for action in list(self.pending_requests.keys()):
            expired = []
            for request in self.pending_requests[action]:
                if request.timeout_at <= current_time:
                    expired.append(request)
            
            for request in expired:
                self.pending_requests[action].remove(request)
                
                # Notify callback of timeout
                if request.callback:
                    try:
                        await request.callback({
                            "success": False,
                            "request_id": request.id,
                            "error": "Request timeout"
                        })
                    except Exception as e:
                        logger.error(f"Timeout callback failed for {request.id}: {e}")
            
            if expired:
                logger.warning(f"Expired {len(expired)} requests for action {action}")
    
    async def _adaptive_tuner_loop(self):
        """Adaptive tuning loop for optimizing batch parameters"""
        if not self.adaptive_enabled:
            return
        
        while self.enabled:
            try:
                await asyncio.sleep(60)  # Tune every minute
                
                # Collect performance metrics
                current_load = len(self.active_batches)
                self.load_history.append(current_load)
                
                # Adjust batch parameters based on load
                if len(self.load_history) >= 10:
                    avg_load = sum(self.load_history) / len(self.load_history)
                    
                    # High load: reduce wait times, increase batch sizes
                    if avg_load > 5:
                        self._adjust_batch_configs(factor=0.8, increase_size=True)
                    # Low load: increase wait times, reduce batch sizes
                    elif avg_load < 2:
                        self._adjust_batch_configs(factor=1.2, increase_size=False)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Adaptive tuner error: {e}")
    
    def _adjust_batch_configs(self, factor: float, increase_size: bool):
        """Adjust batch configurations based on performance"""
        for config in self.batch_configs.values():
            if config.strategy in [BatchStrategy.HYBRID, BatchStrategy.TIME_BASED]:
                # Adjust wait time
                new_wait_time = int(config.max_wait_time_ms * factor)
                config.max_wait_time_ms = max(500, min(30000, new_wait_time))
            
            if increase_size and config.max_batch_size < self.global_max_batch_size:
                config.max_batch_size = min(config.max_batch_size + 1, self.global_max_batch_size)
            elif not increase_size and config.max_batch_size > 1:
                config.max_batch_size = max(config.max_batch_size - 1, 1)
        
        logger.info(f"Adjusted batch configs: factor={factor}, increase_size={increase_size}")
    
    def _generate_request_id(self, action: str, params: Dict[str, Any], user_id: Optional[str]) -> str:
        """Generate unique request ID"""
        content = f"{action}_{json.dumps(params, sort_keys=True)}_{user_id}_{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _generate_batch_id(self, action: str) -> str:
        """Generate unique batch ID"""
        return f"batch_{action}_{int(time.time() * 1000)}_{id(self) % 10000}"
    
    def _estimate_request_cost(self, action: str, params: Dict[str, Any]) -> float:
        """Estimate cost for a request"""
        # Placeholder cost estimation
        cost_map = {
            "generate_post": 0.01,
            "generate_image": 0.05,
            "generate_video": 0.20,
            "generate_hashtags": 0.005,
            "validate_content": 0.002
        }
        return cost_map.get(action, 0.01)
    
    def _estimate_request_tokens(self, action: str, params: Dict[str, Any]) -> int:
        """Estimate token usage for a request"""
        # Placeholder token estimation
        base_tokens = {
            "generate_post": 200,
            "generate_image": 100,
            "generate_video": 500,
            "generate_hashtags": 50,
            "validate_content": 100
        }
        
        base = base_tokens.get(action, 100)
        
        # Add tokens based on input length
        input_text = str(params.get("topic", "")) + str(params.get("prompt", ""))
        input_tokens = len(input_text.split()) * 1.3
        
        return int(base + input_tokens)
    
    def _update_batch_stats(self, batch: BatchJob):
        """Update batching statistics"""
        self.batch_stats["total_batches"] += 1
        self.batch_stats["total_requests"] += len(batch.requests)
        
        # Update averages
        total_requests = self.batch_stats["total_requests"]
        total_batches = self.batch_stats["total_batches"]
        
        self.batch_stats["avg_batch_size"] = total_requests / total_batches
        
        if batch.processed_at and batch.created_at:
            wait_time_ms = (batch.processed_at - batch.created_at) * 1000
            
            # Exponential moving average for wait time
            if self.batch_stats["avg_wait_time_ms"] == 0:
                self.batch_stats["avg_wait_time_ms"] = wait_time_ms
            else:
                self.batch_stats["avg_wait_time_ms"] = (
                    0.9 * self.batch_stats["avg_wait_time_ms"] + 
                    0.1 * wait_time_ms
                )
    
    async def _trigger_batch_processing(self, action: str):
        """Manually trigger batch processing for an action"""
        if action in self.pending_requests and self.pending_requests[action]:
            await self._process_batch(action)
    
    def add_batch_config(self, config: BatchConfig) -> None:
        """Add or update batch configuration"""
        self.batch_configs[config.action] = config
        logger.info(f"Added batch config for action: {config.action}")
    
    def get_batch_stats(self) -> Dict[str, Any]:
        """Get batching statistics"""
        pending_count = sum(len(reqs) for reqs in self.pending_requests.values())
        
        return {
            **self.batch_stats,
            "enabled": self.enabled,
            "pending_requests": pending_count,
            "active_batches": len(self.active_batches),
            "configured_actions": len(self.batch_configs),
            "adaptive_enabled": self.adaptive_enabled,
            "current_load": len(self.active_batches),
            "avg_load": sum(self.load_history) / len(self.load_history) if self.load_history else 0
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        status = {}
        
        for action, requests in self.pending_requests.items():
            if requests:
                status[action] = {
                    "pending_count": len(requests),
                    "oldest_request_age_ms": (time.time() - min(r.created_at for r in requests)) * 1000,
                    "priority_distribution": {
                        priority.name: sum(1 for r in requests if r.priority == priority)
                        for priority in BatchPriority
                    }
                }
        
        return status
    
    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'batch_processor_task') and self.batch_processor_task and not self.batch_processor_task.done():
            self.batch_processor_task.cancel()
        if hasattr(self, 'adaptive_tuner_task') and self.adaptive_tuner_task and not self.adaptive_tuner_task.done():
            self.adaptive_tuner_task.cancel()

# Exception classes
class BatchingError(CreatorError):
    """Batching-specific error"""
    pass

# Utility functions for common merge/split operations
async def text_generation_merge(requests: List[BatchRequest]) -> Dict[str, Any]:
    """Merge multiple text generation requests"""
    topics = [req.params.get("topic", "") for req in requests]
    platform = requests[0].params.get("platform", "")
    tone = requests[0].params.get("tone", "")
    
    # Combine topics
    combined_topic = " | ".join(filter(None, topics))
    
    merged_params = {
        "topic": combined_topic,
        "platform": platform,
        "tone": tone,
        "batch_count": len(requests)
    }
    
    # This would call the actual text generation service
    return {
        "success": True,
        "generated_texts": [f"Generated text for: {topic}" for topic in topics],
        "params_used": merged_params
    }

def text_generation_split(merged_result: Dict[str, Any], 
                         requests: List[BatchRequest]) -> Dict[str, Dict[str, Any]]:
    """Split merged text generation result back to individual results"""
    texts = merged_result.get("generated_texts", [])
    
    results = {}
    for i, request in enumerate(requests):
        if i < len(texts):
            results[request.id] = {
                "success": True,
                "content": texts[i],
                "request_id": request.id
            }
        else:
            results[request.id] = {
                "success": False,
                "error": "No text generated for this request",
                "request_id": request.id
            }
    
    return results
