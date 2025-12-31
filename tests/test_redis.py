"""Tests for Redis cache operations."""
import pytest
from src.cache.redis_config import RedisClient
import fakeredis


@pytest.fixture
def redis_client():
    """Create fake Redis client for testing."""
    # Using fakeredis for testing without actual Redis
    fake_redis = fakeredis.FakeStrictRedis()
    
    client = RedisClient.__new__(RedisClient)
    client.redis = fake_redis
    return client


class TestTaskOperations:
    """Test task operations in Redis."""
    
    def test_set_task(self, redis_client):
        """Test setting task."""
        task_data = {
            "task_id": "task-001",
            "status": "pending",
            "filename": "test.wav"
        }
        result = redis_client.set_task("task-001", task_data)
        assert result is True
    
    def test_get_task(self, redis_client):
        """Test getting task."""
        task_data = {
            "task_id": "task-001",
            "status": "pending",
            "filename": "test.wav"
        }
        redis_client.set_task("task-001", task_data)
        
        retrieved = redis_client.get_task("task-001")
        assert retrieved is not None
        assert retrieved["status"] == "pending"
    
    def test_update_task(self, redis_client):
        """Test updating task."""
        task_data = {
            "task_id": "task-001",
            "status": "pending"
        }
        redis_client.set_task("task-001", task_data)
        
        updated_data = {"status": "completed"}
        redis_client.update_task("task-001", updated_data)
        
        retrieved = redis_client.get_task("task-001")
        assert retrieved["status"] == "completed"
    
    def test_delete_task(self, redis_client):
        """Test deleting task."""
        task_data = {"task_id": "task-001", "status": "pending"}
        redis_client.set_task("task-001", task_data)
        
        result = redis_client.delete_task("task-001")
        assert result is True
        
        retrieved = redis_client.get_task("task-001")
        assert retrieved is None


class TestCacheOperations:
    """Test cache operations in Redis."""
    
    def test_set_cache(self, redis_client):
        """Test setting cache."""
        result = redis_client.set_cache("key1", "value1")
        assert result is True
    
    def test_get_cache(self, redis_client):
        """Test getting cache."""
        redis_client.set_cache("key1", "value1")
        
        value = redis_client.get_cache("key1")
        assert value == "value1"
    
    def test_delete_cache(self, redis_client):
        """Test deleting cache."""
        redis_client.set_cache("key1", "value1")
        
        result = redis_client.delete_cache("key1")
        assert result is True
        
        value = redis_client.get_cache("key1")
        assert value is None


class TestCounterOperations:
    """Test counter operations in Redis."""
    
    def test_increment_counter(self, redis_client):
        """Test incrementing counter."""
        value = redis_client.increment_counter("counter1", 5)
        assert value == 5
        
        value = redis_client.increment_counter("counter1", 3)
        assert value == 8
    
    def test_get_counter(self, redis_client):
        """Test getting counter."""
        redis_client.increment_counter("counter1", 10)
        
        value = redis_client.get_counter("counter1")
        assert value == 10
