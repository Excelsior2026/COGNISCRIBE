"""Performance tests for COGNISCRIBE."""
import pytest
import time
from fastapi.testclient import TestClient
from src.api.main import app
from src.cache.redis_config import get_redis
from src.services.task_manager import TaskManager


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.mark.slow
class TestTaskManagerPerformance:
    """Test TaskManager performance."""
    
    def test_create_task_performance(self):
        """Test task creation performance."""
        task_manager = TaskManager()
        
        start_time = time.time()
        for i in range(100):
            task_manager.create_task(
                user_id="user-001",
                filename=f"file_{i}.wav",
                file_size_bytes=1000000,
                file_path=f"/storage/file_{i}.wav",
                ratio=0.15
            )
        elapsed = time.time() - start_time
        
        # Should create 100 tasks in less than 5 seconds
        assert elapsed < 5.0
        assert elapsed / 100 < 0.05  # < 50ms per task
    
    def test_get_task_performance(self):
        """Test task retrieval performance."""
        task_manager = TaskManager()
        task_id = task_manager.create_task(
            user_id="user-001",
            filename="test.wav",
            file_size_bytes=1000000,
            file_path="/storage/test.wav",
            ratio=0.15
        )
        
        start_time = time.time()
        for _ in range(1000):
            task_manager.get_task(task_id)
        elapsed = time.time() - start_time
        
        # Should retrieve 1000 times in less than 1 second
        assert elapsed < 1.0
        assert elapsed / 1000 < 0.001  # < 1ms per retrieval


@pytest.mark.slow
class TestRedisPerformance:
    """Test Redis performance."""
    
    def test_redis_set_get_performance(self):
        """Test Redis set/get performance."""
        redis = get_redis()
        
        start_time = time.time()
        for i in range(1000):
            redis.set_cache(f"key_{i}", f"value_{i}", ttl=3600)
        set_elapsed = time.time() - start_time
        
        start_time = time.time()
        for i in range(1000):
            redis.get_cache(f"key_{i}")
        get_elapsed = time.time() - start_time
        
        # Set should be fast
        assert set_elapsed < 2.0
        # Get should be very fast
        assert get_elapsed < 0.5


@pytest.mark.slow
class TestAPIPerformance:
    """Test API endpoint performance."""
    
    def test_auth_endpoint_performance(self, client):
        """Test auth endpoint response time."""
        start_time = time.time()
        for _ in range(100):
            client.post(
                "/api/auth/login",
                json={
                    "username": "demo_user",
                    "password": "demo_password_123"
                }
            )
        elapsed = time.time() - start_time
        
        # 100 auth requests should take less than 10 seconds
        assert elapsed < 10.0
        assert elapsed / 100 < 0.1  # < 100ms per request
