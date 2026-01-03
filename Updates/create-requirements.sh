#!/bin/bash
# Phase 4 - Create Missing Requirements Files
# Run this to create requirements.txt and requirements_dev.txt

set -e

REPO_DIR="/users/billp/documents/github/cogniscribe"
cd "$REPO_DIR"

echo "📝 Creating missing requirements files..."
echo ""

# ============================================================================
# Create requirements.txt (production dependencies)
# ============================================================================
echo "Creating requirements.txt..."

cat > requirements.txt << 'EOF'
# FastAPI & Web Framework
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6

# Authentication & Security
python-jose==3.3.0
passlib==1.7.4
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# Caching & Tasks
redis==5.0.1

# Audio Processing
librosa==0.10.0
soundfile==0.12.1
scipy==1.11.4

# ML/AI
numpy==1.24.3
torch==2.0.1
transformers==4.35.2

# HTTP & Requests
httpx==0.25.2
requests==2.31.0

# Logging & Monitoring
python-json-logger==2.0.7

# Utilities
python-dateutil==2.8.2
pytz==2023.3
UUID==1.30
EOF

echo "✅ Created requirements.txt"
echo ""

# ============================================================================
# Create requirements_dev.txt (development dependencies)
# ============================================================================
echo "Creating requirements_dev.txt..."

cat > requirements_dev.txt << 'EOF'
# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
pytest-xdist==3.5.0
fakeredis==2.19.0

# Code Quality
black==23.12.0
ruff==0.1.8
mypy==1.7.1
pylint==3.0.3

# Documentation
sphinx==7.2.6
sphinx-rtd-theme==2.0.0

# Debugging
ipython==8.18.1
ipdb==0.13.13

# Type Stubs
types-redis==4.6.0.11
sqlalchemy-stubs==0.4

# Pre-commit hooks
pre-commit==3.5.0

# Security
bandit==1.7.5
EOF

echo "✅ Created requirements_dev.txt"
echo ""

# ============================================================================
# Verify files were created
# ============================================================================
echo "✅ Verifying files..."
ls -lh requirements.txt requirements_dev.txt
echo ""

echo "✅ Requirements files created successfully!"
echo ""
echo "Now you can run:"
echo "  pip install -r requirements.txt"
echo "  pip install -r requirements_dev.txt"
