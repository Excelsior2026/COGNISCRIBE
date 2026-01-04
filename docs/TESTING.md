# Testing Guide for COGNISCRIBE

## Overview

COGNISCRIBE has comprehensive test coverage with 144 tests covering:
- Core services (93% coverage)
- API endpoints (92% coverage)
- Error handling (95% coverage)
- Utilities (90% coverage)
- Security & validation (90% coverage)

**Overall Coverage:** 82%

---

## 🚀 Quick Start

### Run All Tests

```bash
# Basic run
pytest

# With coverage
pytest --cov=src

# With detailed output
pytest -v

# Stop at first failure
pytest -x
```

### Run Specific Tests

```bash
# Single file
pytest tests/unit/test_transcriber.py

# Single class
pytest tests/unit/test_transcriber.py::TestTranscriber

# Single test
pytest tests/unit/test_transcriber.py::TestTranscriber::test_transcribe_basic

# By marker
pytest -m unit
pytest -m "not slow"
```

### Coverage Reports

```bash
# Terminal report
pytest --cov=src --cov-report=term-missing

# HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# XML for CI
pytest --cov=src --cov-report=xml
```

---

## 📋 Test Structure

```
tests/
├── unit/                      # Unit tests
│   ├── test_transcriber.py
│   ├── test_summarizer.py
│   ├── test_audio_preprocess.py
│   ├── test_task_manager.py
│   ├── test_healthcheck.py
│   ├── test_transcribe_chunk.py
│   ├── test_error_handling.py
│   ├── test_edge_cases.py
│   └── test_integration_resilience.py
├── test_api_pipeline.py       # API integration tests
├── test_api_pipeline_enhanced.py
├── test_phi_detector.py       # PHI detection tests
├── test_settings.py           # Configuration tests
├── test_validation.py         # Validation tests
└── conftest.py                # Shared fixtures
```

---

## 🧰 Test Categories

### Unit Tests (70 tests)
**Coverage:** Core business logic, services, utilities

```bash
pytest tests/unit/ -v
```

### API Tests (37 tests)
**Coverage:** Endpoints, request/response, integration

```bash
pytest tests/test_api*.py -v
```

### Edge Cases (37 tests)
**Coverage:** Boundaries, security, error handling

```bash
pytest tests/unit/test_edge_cases.py tests/unit/test_error_handling.py -v
```

---

## ⚙️ Configuration

### pytest.ini (in pyproject.toml)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = """
    --verbose
    --cov=src
    --cov-report=term-missing
    --cov-report=html
"""
markers = [
    "slow: slow tests",
    "integration: integration tests",
    "unit: unit tests",
]
```

### Coverage (in pyproject.toml)

```toml
[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
precision = 2
fail_under = 80  # Enforced!
```

---

## 📚 Writing Tests

### Test File Template

```python
"""Unit tests for [module name]."""

import pytest
from unittest.mock import Mock, patch
from src.module import function_to_test


class TestFeature:
    """Test feature functionality."""
    
    def test_basic_case(self):
        """Test basic functionality."""
        result = function_to_test("input")
        assert result == "expected"
    
    def test_edge_case(self):
        """Test edge case."""
        with pytest.raises(ValueError):
            function_to_test(None)
    
    @patch('src.module.external_service')
    def test_with_mock(self, mock_service):
        """Test with mocked dependency."""
        mock_service.return_value = "mocked"
        result = function_to_test("input")
        assert result == "mocked"
```

### Fixtures

Defined in `conftest.py`:

```python
@pytest.fixture
def sample_audio_file():
    """Provide sample audio file for testing."""
    # Setup
    file_path = create_test_file()
    yield file_path
    # Teardown
    cleanup(file_path)
```

Use in tests:

```python
def test_with_fixture(sample_audio_file):
    result = process_audio(sample_audio_file)
    assert result is not None
```

---

## 🎯 Coverage Goals

### Current Coverage

```
Module                              Coverage
-----------------------------------------------------
Core Services                       93% ✅
API Routers                         92% ✅
Error Handling                      95% ✅
Utilities                           90% ✅
Validation                          90% ✅
-----------------------------------------------------
Overall                             82% ✅
```

### Target Coverage

- **Minimum (Enforced):** 80%
- **Target:** 85%
- **Ideal:** 90%+

### Improving Coverage

```bash
# 1. Find uncovered lines
pytest --cov=src --cov-report=term-missing

# 2. Generate HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# 3. Add tests for missing lines

# 4. Verify improvement
pytest --cov=src
```

---

## 🐛 Debugging Tests

### Print Debugging

```python
def test_debug():
    result = function()
    print(f"Result: {result}")  # Will show with -s flag
    assert result == expected
```

Run with output:
```bash
pytest -s
```

### Using pdb

```python
def test_debug():
    import pdb; pdb.set_trace()  # Breakpoint
    result = function()
    assert result == expected
```

Run:
```bash
pytest --pdb  # Drop into debugger on failure
```

### Verbose Output

```bash
pytest -vv  # Extra verbose
pytest --tb=long  # Full tracebacks
pytest -l  # Show local variables
```

---

## ⚡ Performance

### Fast Tests

```bash
# Parallel execution (requires pytest-xdist)
pytest -n auto

# Only failed tests
pytest --lf

# Failed first, then rest
pytest --ff
```

### Skip Slow Tests

```python
@pytest.mark.slow
def test_slow_operation():
    # Expensive test
    pass
```

Run:
```bash
pytest -m "not slow"  # Skip slow tests
```

---

## 🛡️ Testing Best Practices

### 1. Test Names

```python
# Good
def test_transcribe_returns_text():
    pass

def test_transcribe_raises_error_on_invalid_file():
    pass

# Bad
def test_1():
    pass

def test_stuff():
    pass
```

### 2. One Assertion Per Test (Generally)

```python
# Good
def test_status_code():
    response = client.get("/api/health")
    assert response.status_code == 200

def test_response_structure():
    response = client.get("/api/health")
    assert "status" in response.json()

# Acceptable for related assertions
def test_response():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### 3. Use Fixtures

```python
# Good
@pytest.fixture
def client():
    return TestClient(app)

def test_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200

# Bad
def test_endpoint():
    client = TestClient(app)  # Repeated in every test
    response = client.get("/api/health")
    assert response.status_code == 200
```

### 4. Mock External Services

```python
@patch('src.api.services.summarizer.requests.post')
def test_with_ollama_mock(mock_post):
    mock_post.return_value.json.return_value = {"response": "summary"}
    result = generate_summary("text")
    assert result == "summary"
```

---

## 📊 Continuous Testing

### Watch Mode (requires pytest-watch)

```bash
pip install pytest-watch
ptw  # Runs tests on file changes
```

### Pre-commit Hook

Automatically runs tests before commit (optional):

```yaml
# Add to .pre-commit-config.yaml
- repo: local
  hooks:
    - id: pytest
      name: pytest
      entry: pytest
      language: system
      pass_filenames: false
      always_run: true
```

---

## 📦 Test Data

### Fixtures Location

```
tests/
├── fixtures/
│   ├── audio/
│   │   ├── sample.mp3
│   │   └── sample.wav
│   └── data/
│       └── test_data.json
└── conftest.py
```

### Using Test Files

```python
import pytest
from pathlib import Path

@pytest.fixture
def test_audio():
    return Path(__file__).parent / "fixtures" / "audio" / "sample.mp3"

def test_with_file(test_audio):
    assert test_audio.exists()
    result = process_audio(test_audio)
    assert result is not None
```

---

## ❓ FAQ

**Q: Tests are slow. How to speed up?**
A: Use `pytest -n auto` for parallel execution, or `pytest -m "not slow"` to skip slow tests.

**Q: How to test async functions?**
A: Use `pytest-asyncio` and mark tests with `@pytest.mark.asyncio`.

**Q: Mock not working?**
A: Ensure you're patching the right location: where it's used, not where it's defined.

**Q: Coverage not increasing?**
A: Check HTML report (`htmlcov/index.html`) to see exactly what's not covered.

**Q: Test passes locally, fails in CI?**
A: Check Python version, environment variables, and system dependencies.

---

## 📚 Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Happy Testing!** 🎉
