"""Authentication endpoints."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from src.api.middleware.jwt_auth import (
    create_access_token,
    verify_password,
    hash_password,
    TokenData
)
from typing import Optional
import os

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Mock user database (replace with real database in production)
USERS_DB: dict = {
    "demo_user": {
        "user_id": "user-001",
        "username": "demo_user",
        "email": "demo@example.com",
        "hashed_password": hash_password("demo_password_123"),
        "is_active": True
    }
}


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token expiration time in seconds")
    user_id: str
    username: str


class RegisterRequest(BaseModel):
    """User registration schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class RegisterResponse(BaseModel):
    """Registration response schema."""
    success: bool
    message: str
    user_id: Optional[str] = None
    username: Optional[str] = None


@router.post("/login", response_model=TokenResponse, status_code=200)
async def login(request: LoginRequest) -> TokenResponse:
    """
    Authenticate user and return JWT access token.
    
    **Credentials for testing:**
    - Username: `demo_user`
    - Password: `demo_password_123`
    """
    user = USERS_DB.get(request.username)
    
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    access_token = create_access_token(
        user_id=user["user_id"],
        username=user["username"],
        email=user["email"]
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=86400,
        user_id=user["user_id"],
        username=user["username"]
    )


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(request: RegisterRequest) -> RegisterResponse:
    """Register new user account."""
    if request.username in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )
    
    for user in USERS_DB.values():
        if user["email"] == request.email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
    
    user_id = f"user-{len(USERS_DB) + 1:03d}"
    USERS_DB[request.username] = {
        "user_id": user_id,
        "username": request.username,
        "email": request.email,
        "hashed_password": hash_password(request.password),
        "is_active": True
    }
    
    return RegisterResponse(
        success=True,
        message="User registered successfully",
        user_id=user_id,
        username=request.username
    )
