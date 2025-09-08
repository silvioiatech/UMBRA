"""
Cache System - Advanced caching for Creator v1 (CRT4)
Provides multi-level caching with TTL, size limits, and intelligent invalidation
"""

import logging
import time
import json
import hashlib
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from collections import defaultdict, OrderedDict

from ...core.config import UmbraConfig

logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    """Cache levels by speed and persistence"""
    MEMORY = "memory"           # Fastest, in-memory cache
    REDIS = "redis"            # Fast, shared cache
    DISK = "disk"              # Slower, persistent cache
    DISTRIBUTED = "distributed" # Slowest, cross-instance cache

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    ttl_seconds: Optional[int]
    size_bytes: int
    tags: List[str]
    level: CacheLevel
    compressed: bool = False
    metadata: Dict[str, Any] = None

@dataclass
class CacheStats:
    """Cache statistics"""
    total_entries: int
    total_size_bytes: int
    hit_count: int
    miss_count: int
    eviction_count: int
    hit_rate: float
    average_size: float
    memory_usage_mb: float
    popular_keys: List[str]
    recent_misses: List[str]

class LRUCache:
    """LRU (Least Recently Used) cache implementation"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.hit_count = 0
        self.miss_count = 0
        self.eviction_count = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key in self.cache:
            # Move to end (most recently used)
            value = self.cache.pop(key)
            self.cache[key] = value
            self.hit_count += 1
            return value
        else:
            self.miss_count += 1
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Set item in cache"""
        if key in self.cache:
            # Update existing
            self.cache.pop(key)
        elif len(self.cache) >= self.max_size:
            # Evict least recently used
            self.cache.popitem(last=False)
            self.eviction_count += 1
        
        self.cache[key] = value
    
    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all items"""
        self.cache.clear()
    
    def size(self) -> int:
        """Get cache size"""
        return len(self.cache)
    
    def hit_rate(self) -> float:
        """Calculate hit rate"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0

class CreatorCache:
    """Advanced multi-level cache system for Creator v1"""
    
    def __init__(self, config: UmbraConfig):
        self.config = config
        
        # Cache configuration
        self.enabled = config.get("CREATOR_CACHE_ENABLED", True)
        self.default_ttl = config.get("CREATOR_CACHE_DEFAULT_TTL_SECONDS", 3600)  # 1 hour
        self.max_memory_size = config.get("CREATOR_CACHE_MAX_MEMORY_MB", 100) * 1024 * 1024  # 100MB
        self.max_entries = config.get("CREATOR_CACHE_MAX_ENTRIES", 10000)
        self.compression_threshold = config.get("CREATOR_CACHE_COMPRESSION_THRESHOLD_BYTES", 1024)
        
        # Multi-level cache storage
        self.memory_cache = LRUCache(max_size=min(self.max_entries, 5000))
        self.disk_cache_enabled = config.get("CREATOR_CACHE_DISK_ENABLED", False)
        self.redis_cache_enabled = config.get("CREATOR_CACHE_REDIS_ENABLED", False)
        
        # Cache entries metadata
        self.entries: Dict[str, CacheEntry] = {}
        
        # Statistics
        self.stats = CacheStats(
            total_entries=0,
            total_size_bytes=0,
            hit_count=0,
            miss_count=0,
            eviction_count=0,
            hit_rate=0.0,
            average_size=0.0,
            memory_usage_mb=0.0,
            popular_keys=[],
            recent_misses=[]
        )
        
        # Tag-based invalidation
        self.tag_to_keys: Dict[str, set] = defaultdict(set)
        
        # Cleanup task
        self.cleanup_task = None
        if self.enabled:
            self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        logger.info(f"Creator cache initialized (enabled: {self.enabled}, max_memory: {self.max_memory_size//1024//1024}MB)")
    
    async def get(self, key: str, level: CacheLevel = CacheLevel.MEMORY) -> Optional[Any]:
        """Get item from cache"""
        if not self.enabled:
            return None
        
        try:
            cache_key = self._normalize_key(key)
            
            # Try memory cache first
            if level == CacheLevel.MEMORY or level == CacheLevel.REDIS:
                value = self.memory_cache.get(cache_key)
                if value is not None:
                    entry = self.entries.get(cache_key)
                    if entry and self._is_valid(entry):
                        # Update access stats
                        entry.last_accessed = time.time()
                        entry.access_count += 1
                        self.stats.hit_count += 1
                        self._update_hit_rate()
                        
                        return self._decompress_if_needed(value, entry.compressed)
            
            # Try Redis cache (if enabled)
            if self.redis_cache_enabled and level in [CacheLevel.REDIS, CacheLevel.DISTRIBUTED]:
                value = await self._get_from_redis(cache_key)
                if value is not None:
                    # Promote to memory cache
                    await self.set(key, value, ttl_seconds=self.default_ttl, level=CacheLevel.MEMORY)
                    self.stats.hit_count += 1
                    self._update_hit_rate()
                    return value
            
            # Try disk cache (if enabled)
            if self.disk_cache_enabled and level == CacheLevel.DISK:
                value = await self._get_from_disk(cache_key)
                if value is not None:
                    # Promote to memory cache
                    await self.set(key, value, ttl_seconds=self.default_ttl, level=CacheLevel.MEMORY)
                    self.stats.hit_count += 1
                    self._update_hit_rate()
                    return value
            
            # Cache miss
            self.stats.miss_count += 1
            self._track_miss(key)
            self._update_hit_rate()
            return None
            
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, 
                 tags: List[str] = None, level: CacheLevel = CacheLevel.MEMORY) -> bool:
        """Set item in cache"""
        if not self.enabled:
            return False
        
        try:
            cache_key = self._normalize_key(key)
            ttl = ttl_seconds or self.default_ttl
            tags = tags or []
            
            # Calculate size
            serialized_value = self._serialize_value(value)
            size_bytes = len(serialized_value.encode('utf-8'))
            
            # Check if compression needed
            compressed = False
            if size_bytes > self.compression_threshold:
                compressed_value = self._compress_value(serialized_value)
                if len(compressed_value) < size_bytes:
                    serialized_value = compressed_value
                    compressed = True
                    size_bytes = len(compressed_value)
            
            # Check memory limits
            if self.stats.total_size_bytes + size_bytes > self.max_memory_size:
                await self._evict_entries(size_bytes)
            
            # Create cache entry
            entry = CacheEntry(
                key=cache_key,
                value=serialized_value,
                created_at=time.time(),
                last_accessed=time.time(),
                access_count=1,
                ttl_seconds=ttl,
                size_bytes=size_bytes,
                tags=tags,
                level=level,
                compressed=compressed,
                metadata={"original_size": len(self._serialize_value(value).encode('utf-8'))}
            )
            
            # Store in appropriate level
            if level == CacheLevel.MEMORY:
                self.memory_cache.set(cache_key, serialized_value)
                self.entries[cache_key] = entry
                
                # Update tag mappings
                for tag in tags:
                    self.tag_to_keys[tag].add(cache_key)
                
                # Update stats
                self.stats.total_entries += 1
                self.stats.total_size_bytes += size_bytes
                self._update_memory_usage()
            
            elif level == CacheLevel.REDIS and self.redis_cache_enabled:
                await self._set_in_redis(cache_key, serialized_value, ttl)
            
            elif level == CacheLevel.DISK and self.disk_cache_enabled:
                await self._set_on_disk(cache_key, serialized_value, ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete item from cache"""
        if not self.enabled:
            return False
        
        try:
            cache_key = self._normalize_key(key)
            
            # Remove from memory
            if self.memory_cache.delete(cache_key):
                entry = self.entries.pop(cache_key, None)
                if entry:
                    # Update stats
                    self.stats.total_entries -= 1
                    self.stats.total_size_bytes -= entry.size_bytes
                    
                    # Remove tag mappings
                    for tag in entry.tags:
                        self.tag_to_keys[tag].discard(cache_key)
                
                self._update_memory_usage()
            
            # Remove from other levels
            if self.redis_cache_enabled:
                await self._delete_from_redis(cache_key)
            
            if self.disk_cache_enabled:
                await self._delete_from_disk(cache_key)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {e}")
            return False
    
    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate all cache entries with specified tags"""
        if not self.enabled:
            return 0
        
        try:
            keys_to_delete = set()
            
            for tag in tags:
                if tag in self.tag_to_keys:
                    keys_to_delete.update(self.tag_to_keys[tag])
            
            count = 0
            for key in keys_to_delete:
                if await self.delete(key):
                    count += 1
            
            logger.info(f"Invalidated {count} cache entries with tags: {tags}")
            return count
            
        except Exception as e:
            logger.error(f"Tag-based invalidation failed: {e}")
            return 0
    
    async def clear(self, level: Optional[CacheLevel] = None) -> bool:
        """Clear cache entries"""
        if not self.enabled:
            return False
        
        try:
            if level is None or level == CacheLevel.MEMORY:
                self.memory_cache.clear()
                self.entries.clear()
                self.tag_to_keys.clear()
                self.stats.total_entries = 0
                self.stats.total_size_bytes = 0
                self._update_memory_usage()
            
            if level is None or level == CacheLevel.REDIS:
                if self.redis_cache_enabled:
                    await self._clear_redis()
            
            if level is None or level == CacheLevel.DISK:
                if self.disk_cache_enabled:
                    await self._clear_disk()
            
            logger.info(f"Cache cleared (level: {level or 'all'})")
            return True
            
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "enabled": self.enabled,
            "total_entries": self.stats.total_entries,
            "total_size_mb": self.stats.total_size_bytes / 1024 / 1024,
            "memory_usage_mb": self.stats.memory_usage_mb,
            "hit_count": self.stats.hit_count,
            "miss_count": self.stats.miss_count,
            "hit_rate": self.stats.hit_rate,
            "eviction_count": self.stats.eviction_count,
            "memory_cache_size": self.memory_cache.size(),
            "memory_cache_hit_rate": self.memory_cache.hit_rate(),
            "popular_keys": self._get_popular_keys(10),
            "recent_misses": self.stats.recent_misses[-10:],
            "tags_count": len(self.tag_to_keys),
            "average_entry_size_kb": self.stats.average_size / 1024 if self.stats.average_size > 0 else 0,
            "levels_enabled": {
                "memory": True,
                "redis": self.redis_cache_enabled,
                "disk": self.disk_cache_enabled
            }
        }
    
    async def optimize(self) -> Dict[str, Any]:
        """Optimize cache performance"""
        optimization_results = {
            "entries_before": self.stats.total_entries,
            "size_before_mb": self.stats.total_size_bytes / 1024 / 1024,
            "actions_taken": []
        }
        
        try:
            # Remove expired entries
            expired_count = await self._remove_expired_entries()
            if expired_count > 0:
                optimization_results["actions_taken"].append(f"Removed {expired_count} expired entries")
            
            # Compress large entries
            compressed_count = await self._compress_large_entries()
            if compressed_count > 0:
                optimization_results["actions_taken"].append(f"Compressed {compressed_count} large entries")
            
            # Promote frequently accessed entries
            promoted_count = await self._promote_hot_entries()
            if promoted_count > 0:
                optimization_results["actions_taken"].append(f"Promoted {promoted_count} hot entries")
            
            # Update stats
            optimization_results.update({
                "entries_after": self.stats.total_entries,
                "size_after_mb": self.stats.total_size_bytes / 1024 / 1024,
                "optimization_time": time.time()
            })
            
            logger.info(f"Cache optimization completed: {optimization_results}")
            return optimization_results
            
        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
            return {"error": str(e)}
    
    def _normalize_key(self, key: str) -> str:
        """Normalize cache key"""
        # Create consistent hash for key
        return hashlib.md5(key.encode('utf-8')).hexdigest()
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value for storage"""
        try:
            return json.dumps(value, default=str, ensure_ascii=False)
        except Exception:
            return str(value)
    
    def _compress_value(self, value: str) -> bytes:
        """Compress value using gzip"""
        import gzip
        return gzip.compress(value.encode('utf-8'))
    
    def _decompress_if_needed(self, value: Union[str, bytes], compressed: bool) -> Any:
        """Decompress value if needed and deserialize"""
        try:
            if compressed and isinstance(value, bytes):
                import gzip
                decompressed = gzip.decompress(value).decode('utf-8')
                return json.loads(decompressed)
            elif isinstance(value, str):
                return json.loads(value)
            else:
                return value
        except Exception:
            return value
    
    def _is_valid(self, entry: CacheEntry) -> bool:
        """Check if cache entry is still valid"""
        if entry.ttl_seconds is None:
            return True
        
        age = time.time() - entry.created_at
        return age < entry.ttl_seconds
    
    def _update_hit_rate(self) -> None:
        """Update hit rate statistics"""
        total = self.stats.hit_count + self.stats.miss_count
        self.stats.hit_rate = self.stats.hit_count / total if total > 0 else 0.0
    
    def _update_memory_usage(self) -> None:
        """Update memory usage statistics"""
        self.stats.memory_usage_mb = self.stats.total_size_bytes / 1024 / 1024
        self.stats.average_size = (
            self.stats.total_size_bytes / self.stats.total_entries 
            if self.stats.total_entries > 0 else 0.0
        )
    
    def _track_miss(self, key: str) -> None:
        """Track cache miss"""
        if len(self.stats.recent_misses) >= 100:
            self.stats.recent_misses.pop(0)
        self.stats.recent_misses.append(key)
    
    def _get_popular_keys(self, limit: int) -> List[str]:
        """Get most accessed cache keys"""
        entries_with_access = [
            (entry.key, entry.access_count) 
            for entry in self.entries.values()
        ]
        entries_with_access.sort(key=lambda x: x[1], reverse=True)
        return [key for key, _ in entries_with_access[:limit]]
    
    async def _evict_entries(self, needed_bytes: int) -> None:
        """Evict entries to make space"""
        # Simple LRU eviction
        entries_by_access = sorted(
            self.entries.items(),
            key=lambda x: x[1].last_accessed
        )
        
        freed_bytes = 0
        for key, entry in entries_by_access:
            if freed_bytes >= needed_bytes:
                break
            
            await self.delete(key)
            freed_bytes += entry.size_bytes
            self.stats.eviction_count += 1
    
    async def _remove_expired_entries(self) -> int:
        """Remove expired cache entries"""
        expired_keys = []
        
        for key, entry in self.entries.items():
            if not self._is_valid(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            await self.delete(key)
        
        return len(expired_keys)
    
    async def _compress_large_entries(self) -> int:
        """Compress large uncompressed entries"""
        compressed_count = 0
        
        for key, entry in list(self.entries.items()):
            if (not entry.compressed and 
                entry.size_bytes > self.compression_threshold):
                
                # Re-compress and update
                compressed_value = self._compress_value(entry.value)
                if len(compressed_value) < entry.size_bytes:
                    old_size = entry.size_bytes
                    entry.value = compressed_value
                    entry.compressed = True
                    entry.size_bytes = len(compressed_value)
                    
                    # Update stats
                    self.stats.total_size_bytes -= (old_size - entry.size_bytes)
                    compressed_count += 1
        
        return compressed_count
    
    async def _promote_hot_entries(self) -> int:
        """Promote frequently accessed entries to higher cache levels"""
        # Placeholder for promotion logic
        return 0
    
    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup task"""
        while self.enabled:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._remove_expired_entries()
                
                # Optimize if cache is getting full
                if self.stats.total_size_bytes > self.max_memory_size * 0.8:
                    await self.optimize()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic cleanup failed: {e}")
    
    # Placeholder methods for Redis/Disk cache (would need real implementations)
    async def _get_from_redis(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        # Placeholder - would implement Redis connection
        return None
    
    async def _set_in_redis(self, key: str, value: str, ttl: int) -> bool:
        """Set value in Redis cache"""
        # Placeholder - would implement Redis connection
        return False
    
    async def _delete_from_redis(self, key: str) -> bool:
        """Delete value from Redis cache"""
        # Placeholder - would implement Redis connection
        return False
    
    async def _clear_redis(self) -> bool:
        """Clear Redis cache"""
        # Placeholder - would implement Redis connection
        return False
    
    async def _get_from_disk(self, key: str) -> Optional[Any]:
        """Get value from disk cache"""
        # Placeholder - would implement disk cache
        return None
    
    async def _set_on_disk(self, key: str, value: str, ttl: int) -> bool:
        """Set value on disk cache"""
        # Placeholder - would implement disk cache
        return False
    
    async def _delete_from_disk(self, key: str) -> bool:
        """Delete value from disk cache"""
        # Placeholder - would implement disk cache
        return False
    
    async def _clear_disk(self) -> bool:
        """Clear disk cache"""
        # Placeholder - would implement disk cache
        return False
    
    def __del__(self):
        """Cleanup on deletion"""
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()

# Decorator for caching function results
def cache_result(cache: CreatorCache, ttl_seconds: Optional[int] = None, 
                tags: List[str] = None, key_func: Optional[Callable] = None):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            result = await cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl_seconds=ttl_seconds, tags=tags or [])
            
            return result
        
        return wrapper
    return decorator

# Context manager for cache transactions
class CacheTransaction:
    """Context manager for cache transactions"""
    
    def __init__(self, cache: CreatorCache):
        self.cache = cache
        self.operations = []
        self.committed = False
    
    async def set(self, key: str, value: Any, **kwargs):
        """Queue set operation"""
        self.operations.append(("set", key, value, kwargs))
    
    async def delete(self, key: str):
        """Queue delete operation"""
        self.operations.append(("delete", key, None, {}))
    
    async def commit(self):
        """Commit all operations"""
        try:
            for op_type, key, value, kwargs in self.operations:
                if op_type == "set":
                    await self.cache.set(key, value, **kwargs)
                elif op_type == "delete":
                    await self.cache.delete(key)
            
            self.committed = True
            
        except Exception as e:
            logger.error(f"Cache transaction commit failed: {e}")
            raise
    
    async def rollback(self):
        """Rollback operations (no-op for now)"""
        self.operations.clear()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self.committed and exc_type is None:
            await self.commit()
        elif exc_type is not None:
            await self.rollback()
