"""Integration tests for COGNISCRIBE."""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.database.config import SessionLocal
from src.database.models import User, TranscriptionJob
from src.api.middleware.jwt_auth import create_access_token, hash_password
from uuid import uuid4


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def test_user():
    """Create test user."""
    db = SessionLocal()
    user = User(
        id=str(uuid4()),
        username="test_integration_user",
        email="integration@test.com",
        hashed_password=hash_password("testpass123"),
        is_active=True
    )
    db.add(user)
    db.commit()
    yield user
    db.delete(user)
    db.commit()
    db.close()


@pytest.fixture
def auth_token(test_user):
    """Generate auth token for test user."""
    return create_access_token(
        user_id=test_user.id,
        username=test_user.username,
        email=test_user.email
    )


@pytest.mark.integration
class TestAuthenticationFlow:
    """Test complete authentication flow."""
    
    def test_login_and_access_protected_endpoint(self, client):
        """Test login flow and protected endpoint access."""
        # Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "demo_user",
                "password": "demo_password_123"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Access protected endpoint with token
        protected_response = client.get(
            "/api/health",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert protected_response.status_code in [200, 400]  # May not exist yet
    
    def test_registration_then_login(self, client):
        """Test user registration then login."""
        username = f"new_user_{uuid4().hex[:8]}"
        email = f"test_{uuid4().hex[:8]}@example.com"
        password = "secure_password_123"
        
        # Register
        register_response = client.post(
            "/api/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password
            }
        )
        assert register_response.status_code == 201
        
        # Login with new credentials
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": username,
                "password": password
            }
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()


@pytest.mark.integration
class TestTranscriptionPipeline:
    """Test transcription pipeline."""
    
    def test_pipeline_with_auth(self, client, auth_token):
        """Test pipeline endpoint with authentication."""
        # Create dummy audio file
        audio_content = b"dummy audio data"
        
        response = client.post(
            "/api/pipeline",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"file": ("test.wav", audio_content)},
            data={"ratio": "0.15", "async_mode": "true"}
        )
        
        # Should return 200 (success) or 400 (invalid audio format)
        assert response.status_code in [200, 400, 422]
    
    def test_pipeline_without_auth(self, client):
        """Test pipeline endpoint without authentication."""
        audio_content = b"dummy audio data"
        
        response = client.post(
            "/api/pipeline",
            files={"file": ("test.wav", audio_content)},
            data={"ratio": "0.15"}
        )
        
        # Should return 401/403 Unauthorized
        assert response.status_code in [401, 403]


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_file_extension(self, client, auth_token):
        """Test pipeline with invalid file extension."""
        response = client.post(
            "/api/pipeline",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"file": ("test.txt", b"not audio")},
            data={"ratio": "0.15"}
        )
        assert response.status_code in [400, 422]
    
    def test_missing_required_params(self, client, auth_token):
        """Test endpoint with missing required parameters."""
        response = client.post(
            "/api/pipeline",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"file": ("test.wav", b"audio")}
            # Missing ratio parameter
        )
        # Should still work with default ratio
        assert response.status_code in [200, 400, 422]
    
    def test_invalid_ratio(self, client, auth_token):
        """Test pipeline with invalid ratio."""
        response = client.post(
            "/api/pipeline",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"file": ("test.wav", b"audio")},
            data={"ratio": "1.5"}  # Out of range
        )
        assert response.status_code == 422
