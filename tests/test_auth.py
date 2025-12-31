"""Tests for authentication endpoints."""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.middleware.jwt_auth import create_access_token, hash_password


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Create a valid JWT token for testing."""
    return create_access_token(
        user_id="test-user-001",
        username="testuser",
        email="test@example.com"
    )


class TestAuthLogin:
    """Test authentication login endpoint."""

    def test_login_success(self, client):
        """Test successful login with valid credentials."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "demo_user",
                "password": "demo_password_123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["username"] == "demo_user"
        assert "expires_in" in data

    def test_login_invalid_username(self, client):
        """Test login with invalid username."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent_user",
                "password": "password123"
            }
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid username or password"

    def test_login_invalid_password(self, client):
        """Test login with invalid password."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "demo_user",
                "password": "wrong_password"
            }
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid username or password"

    def test_login_missing_fields(self, client):
        """Test login with missing required fields."""
        response = client.post(
            "/api/auth/login",
            json={"username": "demo_user"}
        )
        assert response.status_code == 422

    def test_login_password_too_short(self, client):
        """Test login with password below minimum length."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "demo_user",
                "password": "short"
            }
        )
        assert response.status_code == 422


class TestAuthRegister:
    """Test user registration endpoint."""

    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser_001",
                "email": "newuser@example.com",
                "password": "secure_password_123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["username"] == "newuser_001"
        assert "user_id" in data

    def test_register_duplicate_username(self, client):
        """Test registration with existing username."""
        client.post(
            "/api/auth/register",
            json={
                "username": "duplicate_test",
                "email": "user1@example.com",
                "password": "password_123"
            }
        )
        
        response = client.post(
            "/api/auth/register",
            json={
                "username": "duplicate_test",
                "email": "user2@example.com",
                "password": "password_123"
            }
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "not-an-email",
                "password": "password_123"
            }
        )
        assert response.status_code == 422

    def test_register_password_too_short(self, client):
        """Test registration with password below minimum."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "short"
            }
        )
        assert response.status_code == 422


class TestTokenValidation:
    """Test JWT token validation."""

    def test_token_validation_success(self, client, valid_token):
        """Test successful token validation."""
        response = client.get(
            "/api/pipeline",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        assert response.status_code != 401

    def test_token_missing(self, client):
        """Test request without token."""
        response = client.post(
            "/api/pipeline",
            files={"file": ("test.wav", b"data")}
        )
        assert response.status_code in [401, 403]

    def test_token_invalid(self, client):
        """Test request with invalid token."""
        response = client.post(
            "/api/pipeline",
            headers={"Authorization": "Bearer invalid.token.here"},
            files={"file": ("test.wav", b"data")}
        )
        assert response.status_code == 401

    def test_token_expired(self, client):
        """Test request with expired token."""
        from datetime import timedelta
        expired_token = create_access_token(
            user_id="test-user",
            username="testuser",
            expires_delta=timedelta(seconds=-1)
        )
        
        response = client.post(
            "/api/pipeline",
            headers={"Authorization": f"Bearer {expired_token}"},
            files={"file": ("test.wav", b"data")}
        )
        assert response.status_code == 401
