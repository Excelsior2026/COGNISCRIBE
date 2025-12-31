"""Redis cache configuration and utilities."""
import redis
from redis import Redis
import json
import os
from typing import Optional, Any
from datetime import timedelta

# Redis connection configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class RedisClient:
    """Redis client wrapper for task and cache management."""
    
    def __init__(self, url: str = REDIS_URL):
        """Initialize Redis connection."""
        self.redis = redis.from_url(url, decode_responses=True)
        self._test_connection()
    
    def _test_connection(self):
        """Test Redis connection."""
        try:
            self.redis.ping()
            print("✅ Connected to Redis")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            raise
    
    def set_task(self, task_id: str, data: dict, ttl: int = 86400) -> bool:
        """Store task in Redis with TTL (default 24 hours)."""
        try:
            self.redis.hset(f"task:{task_id}", mapping=data)
            self.redis.expire(f"task:{task_id}", ttl)
            return True
        except Exception as e:
            print(f"❌ Error setting task: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[dict]:
        """Retrieve task from Redis."""
        try:
            data = self.redis.hgetall(f"task:{task_id}")
            return data if data else None
        except Exception as e:
            print(f"❌ Error getting task: {e}")
            return None
    
    def update_task(self, task_id: str, data: dict) -> bool:
        """Update task in Redis."""
        try:
            self.redis.hset(f"task:{task_id}", mapping=data)
            return True
        except Exception as e:
            print(f"❌ Error updating task: {e}")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """Delete task from Redis."""
        try:
            self.redis.delete(f"task:{task_id}")
            return True
        except Exception as e:
            print(f"❌ Error deleting task: {e}")
            return False
    
    def set_cache(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Store value in cache with TTL (default 1 hour)."""
        try:
            if isinstance(value, dict):
                value = json.dumps(value)
            self.redis.set(f"cache:{key}", value, ex=ttl)
            return True
        except Exception as e:
            print(f"❌ Error setting cache: {e}")
            return False
    
    def get_cache(self, key: str) -> Optional[Any]:
        """Retrieve value from cache."""
        try:
            value = self.redis.get(f"cache:{key}")
            if value:
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except Exception as e:
            print(f"❌ Error getting cache: {e}")
            return None
    
    def delete_cache(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            self.redis.delete(f"cache:{key}")
            return True
        except Exception as e:
            print(f"❌ Error deleting cache: {e}")
            return False
    
    def increment_counter(self, key: str, amount: int = 1) -> int:
        """Increment counter in Redis."""
        try:
            return self.redis.incrby(f"counter:{key}", amount)
        except Exception as e:
            print(f"❌ Error incrementing counter: {e}")
            return 0
    
    def get_counter(self, key: str) -> int:
        """Get counter value."""
        try:
            value = self.redis.get(f"counter:{key}")
            return int(value) if value else 0
        except Exception as e:
            print(f"❌ Error getting counter: {e}")
            return 0
    
    def set_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Set rate limit with sliding window."""
        try:
            pipe = self.redis.pipeline()
            pipe.incr(f"ratelimit:{key}")
            pipe.expire(f"ratelimit:{key}", window)
            result = pipe.execute()
            return result[0] <= limit
        except Exception as e:
            print(f"❌ Error setting rate limit: {e}")
            return False
    
    def get_rate_limit(self, key: str) -> int:
        """Get current rate limit count."""
        try:
            value = self.redis.get(f"ratelimit:{key}")
            return int(value) if value else 0
        except Exception as e:
            print(f"❌ Error getting rate limit: {e}")
            return 0
    
    def close(self):
        """Close Redis connection."""
        try:
            self.redis.close()
            print("✅ Redis connection closed")
        except Exception as e:
            print(f"❌ Error closing Redis: {e}")


# Global Redis client instance
redis_client: Optional[RedisClient] = None


def get_redis() -> RedisClient:
    """Get or create Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = RedisClient()
    return redis_client
