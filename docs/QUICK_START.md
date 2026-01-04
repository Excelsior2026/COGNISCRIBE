# CogniScribe Quick Start Guide

## 🚀 For First-Time Users

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 8GB free disk space
- 4GB RAM (8GB recommended)

### 1. Get the Code

```bash
git clone https://github.com/Excelsior2026/COGNISCRIBE.git
cd COGNISCRIBE
```

### 2. One-Command Deploy

```bash
# Start everything
docker compose up -d --build

# Watch the logs (optional)
docker compose logs -f
```

**⏱️ First startup takes 3-5 minutes** to download the Ollama model (~4.7GB).

### 3. Verify It Works

```bash
# Test health endpoint
curl http://localhost:8080/api/health
# Expected: {"status":"healthy","timestamp":"..."}

# View API documentation
open http://localhost:8080/docs
```

### 4. Test Transcription

**Option A: Via Swagger UI**
1. Go to http://localhost:8080/docs
2. Click on `POST /api/pipeline`
3. Click "Try it out"
4. Upload an audio file
5. Set `ratio` to `0.15`
6. Click "Execute"

**Option B: Via cURL**
```bash
curl -X POST http://localhost:8080/api/pipeline \
  -F "file=@sample.mp3" \
  -F "ratio=0.15" \
  -F "subject=Biology Lecture"
```

### 5. Check Results

Response includes:
- Full transcription with timestamps
- Structured summary (Key Points, Details, Actions)
- Metadata (duration, language, etc.)
- PHI scan results (if enabled)

---

## 👨‍💻 For Developers

### Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/Excelsior2026/COGNISCRIBE.git
cd COGNISCRIBE

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
vim .env  # Edit as needed

# 5. Start Ollama locally
# Option A: Docker
docker run -d -p 11434:11434 --name ollama ollama/ollama:latest
docker exec ollama ollama pull llama3.1:8b

# Option B: Native (if installed)
ollama serve &
ollama pull llama3.1:8b

# 6. Run API server
uvicorn src.api.main:app --reload --port 8080
```

### Project Structure

```
COGNISCRIBE/
├── src/
│   ├── api/                  # FastAPI application
│   │   ├── main.py          # API entry point
│   │   ├── routers/         # API endpoints
│   │   │   ├── pipeline.py  # Main transcription pipeline
│   │   │   ├── healthcheck.py
│   │   │   └── auth.py
│   │   └── services/        # Business logic
│   │       ├── audio_preprocess.py
│   │       ├── transcriber.py
│   │       ├── summarizer.py
│   │       └── task_manager.py
│   └── utils/               # Utilities
│       ├── settings.py      # Pydantic settings
│       ├── phi_detector.py  # PHI detection
│       ├── validation.py    # Input validation
│       ├── errors.py        # Error handling
│       └── logger.py        # Logging setup
├── tests/                   # Test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docker/
│   └── Dockerfile          # Container build
├── scripts/
│   └── test-deployment.sh  # Deployment verification
├── docs/
│   └── QUICK_START.md      # This file
├── docker-compose.yml      # Service orchestration
├── requirements.txt        # Python dependencies
├── .env.example           # Configuration template
├── DEPLOYMENT.md          # Deployment guide
└── README.md              # Project overview
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_phi_detector.py

# Run tests matching pattern
pytest -k "phi"

# View coverage report
open htmlcov/index.html
```

### Code Quality

```bash
# Run linter
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/

# Type checking (if mypy configured)
mypy src/
```

### Making Changes

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes
vim src/api/routers/pipeline.py

# 3. Run tests
pytest

# 4. Commit with conventional commit message
git commit -m "feat: add new endpoint for speaker detection"

# 5. Push and create PR
git push origin feature/my-feature
```

### Debugging

```bash
# View logs
docker compose logs -f api
docker compose logs -f ollama

# Get container shell
docker exec -it cogniscribe-api bash

# Test Ollama directly
curl http://localhost:11434/api/generate \
  -d '{
    "model": "llama3.1:8b",
    "prompt": "Say hello",
    "stream": false
  }'

# Check disk usage
docker system df

# View settings
python -c "from src.utils.settings import get_settings; print(get_settings())"
```

---

## 📚 Common Tasks

### Change Whisper Model

```bash
# Edit docker-compose.yml
services:
  api:
    environment:
      WHISPER_MODEL: small  # Change from base to small

# Restart
docker compose restart api
```

### Change Ollama Model

```bash
# Pull new model
docker exec -it cogniscribe-ollama ollama pull mistral:7b

# Update docker-compose.yml
services:
  api:
    environment:
      OLLAMA_MODEL: mistral:7b

# Restart
docker compose restart api
```

### Enable GPU Acceleration

**Whisper (API)**:
```yaml
services:
  api:
    environment:
      USE_GPU: "true"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

**Ollama**:
```yaml
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### Increase File Size Limit

```bash
# Edit docker-compose.yml
services:
  api:
    environment:
      MAX_FILE_SIZE_MB: 2000  # Increase from 1000 to 2000 MB

# Restart
docker compose restart api
```

### View PHI Detection Settings

```python
from src.utils.settings import get_settings

settings = get_settings()
print(f"PHI Detection: {settings.phi_detection_enabled}")
```

---

## 🐛 Troubleshooting

### Problem: API not responding

```bash
# Check if containers are running
docker compose ps

# Check API logs
docker compose logs api | tail -50

# Restart services
docker compose restart
```

### Problem: Ollama model not downloaded

```bash
# Check Ollama logs
docker logs cogniscribe-ollama

# Manually pull model
docker exec -it cogniscribe-ollama ollama pull llama3.1:8b

# List installed models
docker exec -it cogniscribe-ollama ollama list
```

### Problem: Out of disk space

```bash
# Check disk usage
df -h
docker system df

# Clean up Docker
docker system prune -a --volumes
```

### Problem: Port already in use

```bash
# Find what's using port 8080
lsof -i :8080

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8081:8080"  # Use 8081 instead
```

---

## 📖 Additional Resources

- **Full Deployment Guide**: [DEPLOYMENT.md](../DEPLOYMENT.md)
- **Configuration Reference**: [.env.example](../.env.example)
- **API Documentation**: http://localhost:8080/docs
- **GitHub Issues**: https://github.com/Excelsior2026/COGNISCRIBE/issues
- **Roadmap**: https://github.com/Excelsior2026/COGNISCRIBE/issues/11

---

## 🆘 Need Help?

1. Check the [Troubleshooting section](../DEPLOYMENT.md#troubleshooting) in DEPLOYMENT.md
2. Search [existing issues](https://github.com/Excelsior2026/COGNISCRIBE/issues)
3. Create a [new issue](https://github.com/Excelsior2026/COGNISCRIBE/issues/new) with:
   - Output of `docker compose logs`
   - Output of `docker compose ps`
   - Your OS and Docker version
   - Steps to reproduce

---

**Happy transcribing!** 🎙️
