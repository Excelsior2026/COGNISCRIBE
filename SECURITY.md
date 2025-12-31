# COGNISCRIBE Security Guide

## Authentication

COGNISCRIBE uses JWT (JSON Web Tokens) for API authentication.

### Getting Started

#### 1. Login to Get Access Token

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "password": "demo_password_123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_id": "user-001",
  "username": "demo_user"
}
```

#### 2. Use Token for API Requests

```bash
curl -X POST "http://localhost:8000/api/pipeline" \
  -H "Authorization: Bearer <your_access_token>" \
  -F "file=@lecture.mp3" \
  -F "ratio=0.15"
```

### Register New User

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "secure_password_123"
  }'
```

## Configuration

### Environment Variables

Set these in your `.env` file:

```
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_EXPIRE_HOURS=24
COGNISCRIBE_AUTH_ENABLED=true
```

### Generating Secure Secret Key

```python
import secrets
secret = secrets.token_urlsafe(32)
print(f"JWT_SECRET_KEY={secret}")
```

## Password Security

- Passwords are hashed using bcrypt with automatic salt
- Minimum 8 characters required
- Never transmitted in plaintext
- Never logged or stored in plain text

## Token Security

- Tokens expire after 24 hours (configurable)
- Tokens are signed using HS256 algorithm
- Tokens contain user metadata but no sensitive information
- Invalid or expired tokens return 401 Unauthorized

## API Security

### Rate Limiting

All endpoints are rate-limited to 10 requests per minute per IP address.

### File Validation

- File extension validation
- File signature verification
- Maximum file size: 500 MB (configurable)
- Only audio formats supported

### CORS

Cross-Origin Resource Sharing is configured for:
- Local development: http://localhost:*
- Production: Configure via CORS_ORIGINS environment variable

## Best Practices

1. **Never commit secrets** - Use .env files (add to .gitignore)
2. **Rotate secret key regularly** - Change JWT_SECRET_KEY periodically
3. **Use HTTPS in production** - Always use TLS/SSL
4. **Monitor token usage** - Implement audit logging
5. **Implement token refresh** - Consider shorter token expiration
6. **Rate limit by user** - Not just by IP address (Phase 3)

## Compliance

COGNISCRIBE implements:
- ✅ Password hashing (bcrypt)
- ✅ JWT token security
- ✅ Input validation
- ✅ CORS security headers
- ✅ Rate limiting per IP
- ⏳ Rate limiting per user (Phase 3)
- ⏳ Encryption at rest (Phase 2b)
- ⏳ Comprehensive audit logging (Phase 2b)
