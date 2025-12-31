# COGNISCRIBE CI/CD Pipeline Documentation

## Overview

COGNISCRIBE uses GitHub Actions for Continuous Integration and Continuous Deployment.

### Workflows

1. **CI Pipeline** (.github/workflows/ci.yml)
   - Runs on every push and pull request
   - Tests, linting, type checking, security scanning
   - Must pass before merging

2. **CD Pipeline** (.github/workflows/cd.yml)
   - Runs on merge to main branch
   - Builds Docker image
   - Pushes to Docker registry
   - Deploys to production

## Continuous Integration

### Triggered By

- Push to any branch
- Pull request to main/develop
- Manual workflow dispatch

### Steps

#### 1. Test Suite
- Install dependencies
- Run pytest with coverage
- Generate coverage reports
- Upload to Codecov

#### 2. Code Quality
- Format check (Black)
- Linting (Ruff)
- Type checking (mypy)
- Import sorting (isort)

#### 3. Security Scanning
- Bandit security audit
- TruffleHog secret detection
- Dependency vulnerability check

### Required Checks

All of the following must pass before merge:

```yaml
# Status checks
- Tests (Unit + Integration + Coverage)
- Code Quality (Format + Lint + Types)
- Security (Bandit + TruffleHog)
- Build (Docker build succeeds)
```

### Configuration

**Environment Variables for CI:**
- `CODECOV_TOKEN` - Codecov integration
- `DOCKER_USERNAME` - Docker registry username
- `DOCKER_PASSWORD` - Docker registry password

## Continuous Deployment

### Triggered By

- Merge to main branch
- Manual workflow dispatch
- Tag creation (v*)

### Steps

#### 1. Build
- Build Docker image
- Test image creation
- Multi-stage optimization

#### 2. Push
- Push to Docker Hub
- Tag with commit SHA
- Tag with 'latest'
- Use buildkit cache

#### 3. Deploy
- Run deployment script
- Update Kubernetes manifests
- Health checks

### Deployment Strategies

**Rolling Deployment:**
```bash
# Gradual rollout to new version
docker-compose up -d --force-recreate api
```

**Blue-Green Deployment:**
```bash
# Run new version alongside old
# Switch traffic when ready
```

**Canary Deployment:**
```bash
# Deploy to small percentage of traffic
# Monitor metrics
# Gradually increase percentage
```

## Setting Up CI/CD

### 1. GitHub Secrets

Add required secrets to repository:

```bash
# Repository Settings > Secrets and variables > Actions

DOCKER_USERNAME: your-docker-username
DOCKER_PASSWORD: your-docker-password
CODECOV_TOKEN: your-codecov-token
```

### 2. Branch Protection Rules

Configure main branch protection:

```
Settings > Branches > Branch protection rules

- Require pull request reviews
- Dismiss stale pull request approvals
- Require status checks to pass:
  - Tests
  - Code Quality
  - Security
```

### 3. Trigger Workflows

```bash
# Trigger CI on push
git push origin feature-branch

# Trigger CD on merge to main
git checkout main
git merge feature-branch
git push origin main

# Trigger with tag
git tag v1.0.0
git push origin v1.0.0
```

## Monitoring Workflows

### View Workflow Status

```bash
# In GitHub web UI
- Go to Actions tab
- Click on workflow
- View real-time logs
- Download artifacts
```

### Command Line

```bash
# Using GitHub CLI
gh workflow list
gh workflow view ci.yml
gh workflow run ci.yml --ref main
gh run list --workflow=ci.yml
gh run view <run-id> --log
```

## Debugging Failed Workflows

### Common Issues

**Tests fail in CI but pass locally:**
```yaml
# Check environment variables
- DATABASE_URL
- REDIS_URL
- JWT_SECRET_KEY

# May need to use test database
DATABASE_URL: sqlite:///./test.db
```

**Docker build fails:**
```yaml
# Check Dockerfile syntax
# Verify all COPY paths exist
# Check for large files in .dockerignore
```

**Security scan blocks deployment:**
```yaml
# Review bandit report
# Address identified issues
# Or whitelist false positives
```

### Enable Debug Logging

```yaml
# In workflow file
- name: Enable debug logging
  run: echo "ACTIONS_STEP_DEBUG=true" >> $GITHUB_ENV
```

## Performance Optimization

### Caching

**Package Cache:**
```yaml
- uses: actions/setup-python@v4
  with:
    cache: 'pip'
```

**Docker Layer Cache:**
```yaml
cache-from: type=registry,ref=${{ registry }}/cogniscribe:buildcache
cache-to: type=registry,ref=${{ registry }}/cogniscribe:buildcache
```

### Parallel Jobs

Run tests in parallel:
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-suite: [unit, integration, database]
    steps:
      - run: pytest tests/test_${{ matrix.test-suite }}.py
```

### Matrix Testing

Test multiple Python versions:
```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
```

## Deployment Configuration

### Kubernetes Deployment

```yaml
# deploy.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cogniscribe-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cogniscribe
  template:
    spec:
      containers:
      - name: api
        image: docker.io/username/cogniscribe:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: cogniscribe-secrets
              key: database-url
```

### Docker Compose Deployment

```bash
# Deploy with docker-compose
docker-compose -f docker-compose-prod.yml up -d

# Verify services
docker-compose -f docker-compose-prod.yml ps

# View logs
docker-compose -f docker-compose-prod.yml logs -f api
```

## Rollback Procedures

### Rollback Docker Image

```bash
# Revert to previous image
docker pull username/cogniscribe:previous-sha
docker-compose up -d --force-recreate api
```

### Rollback Database

```bash
# If migrations caused issues
python scripts/rollback_db.py --version previous
```

## Monitoring & Alerts

### Health Checks

```yaml
# In deployment
livenessProbe:
  httpGet:
    path: /api/health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /api/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Alerting

Setup alerts for:
- Workflow failures
- Test coverage drops
- Performance degradation
- Deployment failures

## Best Practices

1. **Keep workflows simple** - One responsibility per job
2. **Use cache** - Significantly speeds up builds
3. **Fail fast** - Run quick checks first
4. **Matrix testing** - Test multiple configurations
5. **Artifact retention** - Set appropriate expiration
6. **Security** - Never commit secrets
7. **Documentation** - Document deployment procedures
8. **Gradual rollout** - Use deployment strategies

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Actions Best Practices](https://docs.github.com/en/actions/guides)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
