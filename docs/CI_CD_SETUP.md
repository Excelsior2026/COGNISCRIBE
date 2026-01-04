# CI/CD Setup Guide for COGNISCRIBE

## Overview

COGNISCRIBE uses a comprehensive CI/CD pipeline with GitHub Actions to ensure code quality, test coverage, and deployment readiness.

## 🚀 Quick Start

### 1. Enable GitHub Actions

GitHub Actions should be enabled by default. Verify at:
```
https://github.com/Excelsior2026/COGNISCRIBE/settings/actions
```

### 2. Set Up Codecov (Optional but Recommended)

1. Go to [Codecov.io](https://codecov.io)
2. Sign in with GitHub
3. Add COGNISCRIBE repository
4. Copy the upload token
5. Add to repository secrets:
   ```
   Settings → Secrets and variables → Actions → New repository secret
   Name: CODECOV_TOKEN
   Value: <your-token>
   ```

### 3. Install Pre-commit Hooks Locally

```bash
# Install pre-commit
pip install pre-commit

# Install the git hooks
pre-commit install

# (Optional) Run against all files
pre-commit run --all-files
```

---

## 📊 Workflows

### 1. Test Workflow (`.github/workflows/test.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- All pull requests
- Manual dispatch

**What It Does:**
- Tests on Python 3.9, 3.10, 3.11
- Tests on Ubuntu and macOS
- Runs full test suite with coverage
- Lints code with flake8
- Checks formatting with black
- Security scan with bandit
- Uploads coverage to Codecov
- **Fails if coverage < 80%**

**Matrix Testing:**
```yaml
strategy:
  matrix:
    os: [ubuntu-latest]
    python-version: ['3.9', '3.10', '3.11']
    include:
      - os: macos-latest
        python-version: '3.11'
```

### 2. Lint Workflow (`.github/workflows/lint.yml`)

**Triggers:**
- Push to `main` or `develop`
- Pull requests

**Checks:**
- Code style (flake8)
- Import sorting (isort)
- Formatting (black)
- Type hints (mypy)
- Security issues (bandit)

**Outputs:**
- Detailed linting reports
- Security scan JSON report

### 3. Integration Tests (`.github/workflows/integration-tests.yml`)

**Triggers:**
- Push to `main` or `develop`
- Pull requests
- Daily at 2 AM UTC (scheduled)
- Manual dispatch

**What It Does:**
- Runs integration tests with services
- Future: Will include Ollama container
- Timeout protection (5 minutes)

---

## 🛡️ Quality Gates

### Automated Checks on Every PR:

1. ✅ **All tests pass** (144 tests)
2. ✅ **Code coverage ≥ 80%**
3. ✅ **No linting errors**
4. ✅ **Code is formatted** (black)
5. ✅ **Imports sorted** (isort)
6. ✅ **No security issues** (bandit)
7. ✅ **Pre-commit hooks pass**

### Coverage Threshold

**Enforced:** 80% minimum coverage

```bash
# Check locally
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

If coverage drops below 80%, the CI build **fails**.

---

## 📝 Pre-commit Hooks

### Installed Hooks

1. **File Checks:**
   - Trailing whitespace removal
   - End-of-file fixer
   - YAML/JSON/TOML validation
   - Large file detection (>1MB)
   - Merge conflict detection
   - Private key detection

2. **Python Code:**
   - Black formatting (line length: 120)
   - isort import sorting
   - flake8 linting
   - Bandit security scanning

### Running Pre-commit

```bash
# Run on staged files (automatic on commit)
git commit

# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files

# Skip hooks (not recommended)
git commit --no-verify
```

### Bypassing Hooks (Emergency Only)

```bash
# Skip pre-commit hooks
git commit --no-verify -m "Emergency fix"

# CI will still run and may fail!
```

---

## 🎆 Branch Protection Rules (Recommended)

### For `main` branch:

1. Go to: `Settings → Branches → Add rule`
2. Branch name pattern: `main`
3. Enable:
   - ☑️ Require a pull request before merging
   - ☑️ Require approvals (1)
   - ☑️ Require status checks to pass before merging
     - ☑️ Require branches to be up to date
     - Select: `test`, `lint`
   - ☑️ Require conversation resolution before merging
   - ☑️ Do not allow bypassing the above settings

### For `develop` branch:

Same as main, but:
- Approvals: 0 (for faster iteration)
- Status checks required: `test`

---

## 📊 Codecov Integration

### Setup

1. **Sign up:** [codecov.io](https://codecov.io)
2. **Connect repository**
3. **Add token to secrets:** `CODECOV_TOKEN`
4. **Badges automatically appear** on PRs

### Coverage Reports

**On Every PR:**
- Coverage diff (what changed)
- Line-by-line coverage
- Coverage trends

**View Reports:**
- Codecov dashboard: `https://codecov.io/gh/Excelsior2026/COGNISCRIBE`
- Artifacts in GitHub Actions
- Local HTML: `open htmlcov/index.html`

### Coverage Badges

Add to README.md:

```markdown
[![codecov](https://codecov.io/gh/Excelsior2026/COGNISCRIBE/branch/main/graph/badge.svg)](https://codecov.io/gh/Excelsior2026/COGNISCRIBE)
[![Tests](https://github.com/Excelsior2026/COGNISCRIBE/workflows/Tests/badge.svg)](https://github.com/Excelsior2026/COGNISCRIBE/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
```

---

## 🛠️ Local Development Workflow

### Before Committing:

```bash
# 1. Run tests locally
pytest

# 2. Check coverage
pytest --cov=src --cov-report=term-missing

# 3. Run linters
flake8 src tests
black --check src tests
isort --check src tests

# 4. Format code
black src tests
isort src tests

# 5. Run pre-commit
pre-commit run --all-files

# 6. Commit (hooks run automatically)
git commit -m "Your message"
```

### Quick Commands:

```bash
# Format everything
make format  # If Makefile exists
# OR
black src tests && isort src tests

# Run all checks
make lint test  # If Makefile exists
# OR
flake8 src tests && pytest

# Fix common issues
pre-commit run --all-files
```

---

## 🐛 Troubleshooting

### Issue: Tests Pass Locally, Fail in CI

**Causes:**
- Different Python version
- Missing system dependencies
- Environment variables not set
- Cached dependencies

**Solutions:**
```bash
# Test with specific Python version
pytest --python=python3.9

# Clear cache
pytest --cache-clear

# Test in clean environment
python -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt
pytest
```

### Issue: Pre-commit Hooks Fail

**Solution:**
```bash
# Update hooks
pre-commit autoupdate

# Clear cache
pre-commit clean

# Reinstall
pre-commit uninstall
pre-commit install

# Run with verbose output
pre-commit run --all-files --verbose
```

### Issue: Coverage Drops Below 80%

**Solution:**
```bash
# See what's not covered
pytest --cov=src --cov-report=term-missing

# Generate HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Add tests for missing coverage
# Run again to verify
```

### Issue: Linting Errors

**Auto-fix many issues:**
```bash
# Format code
black src tests

# Sort imports
isort src tests

# Check remaining issues
flake8 src tests
```

---

## 📚 Best Practices

### 1. Keep Coverage High
- **Target:** ≥ 80% (enforced)
- **Ideal:** ≥ 90%
- Write tests for new code
- Don't decrease coverage

### 2. Run Tests Before Push

```bash
# Quick check
pytest -x  # Stop at first failure

# Full check
pytest --cov=src --cov-report=term-missing
```

### 3. Use Feature Branches

```bash
# Create branch
git checkout -b feature/amazing-feature

# Make changes, commit
git add .
git commit -m "Add amazing feature"

# Push
git push origin feature/amazing-feature

# Create PR on GitHub
```

### 4. Keep PRs Small
- ✅ Focused changes
- ✅ Easy to review
- ✅ Faster to merge
- ❌ Avoid massive PRs

### 5. Write Good Commit Messages

```bash
# Good
git commit -m "fix: Handle timeout in Ollama service"
git commit -m "feat: Add chunk transcription endpoint"
git commit -m "test: Add edge cases for validation"

# Bad
git commit -m "fixes"
git commit -m "update"
git commit -m "stuff"
```

### 6. Review CI Output
- 👀 Check test results
- 👀 Review coverage report
- 👀 Fix linting issues
- 👀 Read security warnings

---

## ⚙️ Configuration Files

### `.github/workflows/test.yml`
Main test workflow with coverage

### `.github/workflows/lint.yml`
Code quality checks

### `.github/workflows/integration-tests.yml`
Integration and E2E tests

### `.pre-commit-config.yaml`
Pre-commit hooks configuration

### `pyproject.toml`
Tool configuration (black, isort, pytest, mypy, coverage)

### `.flake8`
Flake8 linter configuration

---

## 🚀 Deployment (Future)

### Continuous Deployment Pipeline

When ready for production:

1. **Staging Deployment:**
   - Auto-deploy `develop` → staging
   - Run integration tests
   - Manual approval

2. **Production Deployment:**
   - Tag release: `v1.0.0`
   - Auto-deploy `main` → production
   - Blue-green deployment
   - Rollback capability

### Docker Builds

```yaml
# Future: .github/workflows/docker.yml
- Build Docker image
- Push to registry
- Deploy to cloud
```

---

## 📊 Metrics & Monitoring

### Code Quality Metrics:
- **Test Coverage:** 82% (target: ≥80%)
- **Tests:** 144 passing
- **Code Quality:** A grade
- **Security:** No critical issues

### CI/CD Metrics:
- **Build Time:** ~3-5 minutes
- **Test Execution:** ~10 seconds
- **Success Rate:** Target 95%+

---

## ❓ FAQ

**Q: Do I need to run tests locally?**
A: Yes! CI is a safety net, not a replacement for local testing.

**Q: Can I skip pre-commit hooks?**
A: Yes with `--no-verify`, but CI will likely fail.

**Q: How do I add a new test?**
A: Add to appropriate file in `tests/`, follow existing patterns.

**Q: What if CI is red?**
A: Check the logs, fix issues, push again. PRs can't merge until green.

**Q: How do I update Python dependencies?**
A: Update `requirements.txt`, ensure tests pass, update CI if needed.

**Q: Can I merge my own PR?**
A: Depends on branch protection rules. Generally: no for `main`.

---

## 🎯 Next Steps

1. ✅ GitHub Actions enabled
2. ✅ Pre-commit hooks configured
3. ✅ Quality gates established
4. 🔲 Set up Codecov
5. 🔲 Enable branch protection
6. 🔲 Add badges to README
7. 🔲 Configure deployment pipeline

---

**Status:** CI/CD foundation complete! 🎉

All commits are now automatically tested, linted, and validated.
