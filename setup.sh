#!/bin/bash
# CogniScribe Setup Script
# Helps users set up the application quickly

set -e

echo "🚀 CogniScribe Setup Script"
echo "============================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env file${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env and set your configuration values${NC}"
    else
        echo -e "${RED}❌ .env.example not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Generate secure keys if needed
echo ""
echo "🔐 Generating secure keys..."

# Generate JWT secret if not set or is default
if ! grep -q "JWT_SECRET_KEY=" .env || grep -q "your-secret-key-change-in-production" .env; then
    jwt_secret=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$jwt_secret|" .env
    else
        # Linux
        sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$jwt_secret|" .env
    fi
    echo -e "${GREEN}✅ Generated JWT_SECRET_KEY${NC}"
else
    echo "   JWT_SECRET_KEY already set"
fi

# Generate API key if not set
if ! grep -q "CLINISCRIBE_API_KEYS=" .env || grep -q "your-api-key" .env; then
    api_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|CLINISCRIBE_API_KEYS=.*|CLINISCRIBE_API_KEYS=$api_key|" .env
    else
        sed -i "s|CLINISCRIBE_API_KEYS=.*|CLINISCRIBE_API_KEYS=$api_key|" .env
    fi
    echo -e "${GREEN}✅ Generated CLINISCRIBE_API_KEYS${NC}"
    echo -e "${YELLOW}   Your API key: $api_key${NC}"
    echo -e "${YELLOW}   Save this key - you'll need it to make API requests${NC}"
else
    echo "   CLINISCRIBE_API_KEYS already set"
fi

# Check for required dependencies
echo ""
echo "📦 Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo ""
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Created virtual environment${NC}"
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install dependencies
echo ""
echo "📥 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt not found${NC}"
fi

# Check for PostgreSQL
echo ""
echo "🗄️  Checking database..."
if command -v psql &> /dev/null; then
    echo "   PostgreSQL client found"
else
    echo -e "${YELLOW}⚠️  PostgreSQL client not found. Install PostgreSQL to use the database.${NC}"
fi

# Check for Redis
echo ""
echo "💾 Checking Redis..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✅ Redis is running${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis is installed but not running. Start it with: redis-server${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Redis not found. Install Redis for production rate limiting.${NC}"
fi

# Check for Ollama
echo ""
echo "🤖 Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✅ Ollama is installed${NC}"
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${GREEN}✅ Ollama service is running${NC}"
    else
        echo -e "${YELLOW}⚠️  Ollama is installed but not running. Start it with: ollama serve${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Ollama not found. Install Ollama for summarization features.${NC}"
    echo "   Visit: https://ollama.ai"
fi

# Initialize database
echo ""
echo "🗄️  Database setup..."
read -p "Initialize database tables? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 -c "from src.database.config import init_db; init_db()"
    echo -e "${GREEN}✅ Database initialized${NC}"
fi

echo ""
echo "============================"
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Review and update .env file with your configuration"
echo "2. Ensure PostgreSQL is running and accessible"
echo "3. Start the application with: python -m src.api.main"
echo "   Or use: uvicorn src.api.main:app --reload"
echo ""
echo "For more information, see README.md"
