#!/bin/bash

# CogniScribe Deployment Test Script
# Tests that all services are running and healthy

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "CogniScribe Deployment Verification"
echo "========================================"
echo ""

# Check Docker is running
echo -n "Checking Docker... "
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}FAILED${NC}"
    echo "Error: Docker is not running or you don't have permission."
    echo "Try: sudo systemctl start docker"
    exit 1
fi
echo -e "${GREEN}OK${NC}"

# Check Docker Compose
echo -n "Checking Docker Compose... "
if ! docker compose version > /dev/null 2>&1; then
    echo -e "${RED}FAILED${NC}"
    echo "Error: Docker Compose not found."
    echo "Install: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}OK${NC}"

echo ""
echo "Starting services..."
docker compose up -d --build

echo ""
echo "Waiting for services to start (this may take 3-5 minutes on first run)..."
sleep 30

# Check Ollama container
echo ""
echo -n "Checking Ollama container... "
if docker compose ps ollama | grep -q "Up"; then
    echo -e "${GREEN}RUNNING${NC}"
else
    echo -e "${RED}STOPPED${NC}"
    echo "Logs:"
    docker compose logs ollama | tail -20
    exit 1
fi

# Check API container
echo -n "Checking API container... "
if docker compose ps api | grep -q "Up"; then
    echo -e "${GREEN}RUNNING${NC}"
else
    echo -e "${RED}STOPPED${NC}"
    echo "Logs:"
    docker compose logs api | tail -20
    exit 1
fi

# Wait for services to be fully ready
echo ""
echo "Waiting for services to be ready..."
sleep 30

# Test Ollama endpoint
echo ""
echo -n "Testing Ollama API... "
if curl -s -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
    echo "  Models installed:"
    curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | sed 's/^/    - /'
else
    echo -e "${YELLOW}WARNING${NC}"
    echo "  Ollama is starting but not ready yet. Model may still be downloading."
    echo "  Check progress: docker logs -f cogniscribe-ollama"
fi

# Test API health endpoint
echo ""
echo -n "Testing API health endpoint... "
retries=0
max_retries=10
while [ $retries -lt $max_retries ]; do
    if curl -s -f http://localhost:8080/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        response=$(curl -s http://localhost:8080/api/health)
        echo "  Response: $response"
        break
    else
        retries=$((retries + 1))
        if [ $retries -eq $max_retries ]; then
            echo -e "${RED}FAILED${NC}"
            echo "  API is not responding after $max_retries attempts"
            echo ""
            echo "API Logs (last 30 lines):"
            docker compose logs api | tail -30
            exit 1
        fi
        echo -n "."
        sleep 3
    fi
done

# Test API routes
echo ""
echo -n "Testing API routes... "
if curl -s http://localhost:8080/docs > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
    echo "  Swagger docs: http://localhost:8080/docs"
else
    echo -e "${YELLOW}WARNING${NC}"
    echo "  Docs endpoint not accessible"
fi

# Summary
echo ""
echo "========================================"
echo -e "${GREEN}Deployment Test PASSED!${NC}"
echo "========================================"
echo ""
echo "Services:"
echo "  - API:    http://localhost:8080"
echo "  - Docs:   http://localhost:8080/docs"
echo "  - Ollama: http://localhost:11434"
echo ""
echo "Next steps:"
echo "  1. Upload test audio file to http://localhost:8080/docs"
echo "  2. Check logs: docker compose logs -f"
echo "  3. Stop services: docker compose down"
echo ""
echo "For full deployment guide, see: DEPLOYMENT.md"
echo ""
