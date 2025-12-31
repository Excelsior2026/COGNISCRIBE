# COGNISCRIBE Testing & CI/CD Guide

## Testing Overview

COGNISCRIBE implements comprehensive testing at multiple levels:

### Test Types

1. **Unit Tests** - Individual functions and classes
2. **Integration Tests** - Complete workflows
3. **Performance Tests** - Load and response time
4. **Database Tests** - ORM models and queries
5. **Redis Tests** - Cache operations

## Running Tests

### Quick Start

```bash
# Install dev dependencies
make install-dev

# Run all tests
make test

# Run with coverage report
make test-cov

# Run fast tests only (exclude slow tests)
make test-fast
```

### Detailed Testing

```bash
# Unit tests only
pytest tests/test_auth.py tests/test_database.py -v

# Integration tests
pytest tests/test_integration.py -v

# Performance tests (slow)
pytest tests/test_performance.py -v -s

# Specific test class
pytest tests/test_auth.py::TestAuthLogin -v

# Specific test function
pytest tests/test_auth.py::TestAuthLogin::test_login_success -v

# Run with print statements
pytest tests/ -v -s

# Run in parallel (faster)
pytest tests/ -v -n auto
```

### Coverage Reports

```bash
# Generate coverage report
make test-cov

# View HTML coverage report
open htmlcov/index.html
```

## Code Quality

### Formatting

```bash
# Format code with Black
make format

# Check formatting without changes
make lint
```

### Type Checking

```bash
# Run mypy type checking
mypy src/ --ignore-missing-imports

# Generate type coverage report
mypy src/ --ignore-missing-imports --no-incremental
```

### Linting

```bash
# Check with Ruff
ruff check src/ tests/

# Fix common issues
ruff check --fix src/ tests/
```

### Pre-commit Hooks

```bash
# Install pre-commit
pre-commit install

# Run all hooks
make pre-commit

# Run specific hook
pre-commit run black --all-files
```

## CI/CD Pipeline

### GitHub Actions Workflows

**Continuous Integration (.github/workflows/ci.yml):**
- Triggers on push to any branch and pull requests
- Runs on Python 3.11
- Services: PostgreSQL, Redis
- Jobs:
  - Test suite with coverage
  - Code quality checks (Black, Ruff, mypy)
  - Security scanning

**Continuous Deployment (.github/workflows/cd.yml):**
- Triggers on push to main branch
- Builds Docker image
- Pushes to Docker Hub
- Deploys to production

### Triggering Workflows

```bash
# Trigger CI on push
git push origin feature-branch

# Trigger CD on merge to main
git push origin main

# Trigger workflow by tag
git tag v1.0.0
git push origin v1.0.0
```

## Test Configuration

### pytest.ini

Controls pytest behavior:
- Test discovery patterns
- Markers for categorizing tests
- Output format
- Async mode

### pyproject.toml

Tool configurations:
- Black: code formatting
- Ruff: linting rules
- mypy: type checking
- Coverage: report settings
- isort: import sorting

### .pre-commit-config.yaml

Git hooks that run before commits:
- Trailing whitespace removal
- YAML validation
- Large file detection
- Black formatting
- Ruff linting
- mypy type checking

## Test Database

Tests use SQLite for isolation:

```bash
# SQLite database created at ./test.db
# Automatically created and destroyed per test

# Force reset test database
rm test.db
```

## Mock and Fixture Usage

### Database Fixtures

```python
@pytest.fixture
def test_db():
    """Create test database."""
    # Setup
    engine = create_engine(...)
    Base.metadata.create_all(bind=engine)
    
    # Test
    yield session
    
    # Teardown
    session.close()
    Base.metadata.drop_all(bind=engine)
```

### Redis Fixtures

```python
@pytest.fixture
def redis_client():
    """Create fake Redis client."""
    fake_redis = fakeredis.FakeStrictRedis()
    client = RedisClient.__new__(RedisClient)
    client.redis = fake_redis
    return client
```

### Authentication Fixtures

```python
@pytest.fixture
def auth_token():
    """Generate test JWT token."""
    return create_access_token(
        user_id="test-user",
        username="testuser"
    )
```

## Performance Testing

### Load Testing

```bash
# Run slow tests (load tests)
pytest tests/test_performance.py -v -s

# Test with profiling
pytest tests/ --profile
```

### Benchmarking

```python
def test_task_creation_performance():
    """Benchmark task creation."""
    start = time.time()
    for i in range(100):
        task_manager.create_task(...)
    elapsed = time.time() - start
    assert elapsed < 5.0  # Should complete in < 5s
```

## Debugging Tests

### Print Debug Info

```bash
# Show print statements
pytest tests/test_auth.py -v -s

# Show local variables on failure
pytest tests/ -v -l
```

### Drop into Debugger

```python
def test_something():
    import pdb; pdb.set_trace()  # Debugger breakpoint
    assert something == expected
```

### Use IPython

```python
from IPython import embed

def test_something():
    embed()  # Interactive IPython shell
    assert something == expected
```

## Test Markers

Mark tests for categorization:

```python
@pytest.mark.unit
def test_unit():
    pass

@pytest.mark.integration
def test_integration():
    pass

@pytest.mark.slow
def test_slow():
    pass

@pytest.mark.auth
def test_auth():
    pass

@pytest.mark.database
def test_database():
    pass
```

Run marked tests:

```bash
# Run only unit tests
pytest tests/ -m unit

# Run everything except slow tests
pytest tests/ -m "not slow"

# Run auth and database tests
pytest tests/ -m "auth or database"
```

## Coverage Reports

### Generate Report

```bash
# Terminal report
pytest --cov=src --cov-report=term-missing

# HTML report
pytest --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html

# XML report (for CI/CD)
pytest --cov=src --cov-report=xml
```

### Coverage Thresholds

Set minimum coverage in pyproject.toml:

```toml
[tool.coverage.report]
fail_under = 80  # Fail if coverage < 80%
```

## Continuous Integration Checks

All checks must pass before merging:

1. ✅ Unit tests pass
2. ✅ Integration tests pass
3. ✅ Code coverage > 80%
4. ✅ Black formatting passes
5. ✅ Ruff linting passes
6. ✅ mypy type checking passes
7. ✅ Security scan passes

## Best Practices

1. **Test coverage**: Aim for >80% code coverage
2. **Meaningful assertions**: Use descriptive assertion messages
3. **Isolated tests**: Each test should be independent
4. **Mock external services**: Use fakeredis, sqlalchemy mocks
5. **Test names**: Describe what is being tested
6. **DRY: Don't Repeat Yourself**: Use fixtures for common setup
7. **Fast tests**: Keep unit tests < 100ms
8. **Slow tests**: Mark slow tests with @pytest.mark.slow

## Troubleshooting

### Tests fail locally but pass in CI

Usually due to environment differences:
- Check DATABASE_URL
- Check REDIS_URL
- Check JWT_SECRET_KEY
- Verify Python version (3.11+)

### Redis connection errors

```bash
# Start Redis
redis-server

# Check connection
redis-cli ping
```

### Database lock errors

```bash
# Delete test database
rm test.db

# Rerun tests
pytest tests/
```

### Import errors

```bash
# Reinstall dependencies
pip install -r requirements.txt -r requirements_dev.txt

# Verify Python path
python -c "import src; print(src.__file__)"
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Black Code Formatter](https://github.com/psf/black)
- [Ruff Linter](https://github.com/charliermarsh/ruff)
- [mypy Type Checker](http://mypy-lang.org/)
- [GitHub Actions](https://docs.github.com/en/actions)
