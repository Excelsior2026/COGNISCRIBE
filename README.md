# CogniScribe 🎓🎤

[![Tests](https://github.com/Excelsior2026/COGNISCRIBE/workflows/Tests/badge.svg)](https://github.com/Excelsior2026/COGNISCRIBE/actions/workflows/test.yml)
[![Lint](https://github.com/Excelsior2026/COGNISCRIBE/workflows/Lint/badge.svg)](https://github.com/Excelsior2026/COGNISCRIBE/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/Excelsior2026/COGNISCRIBE/branch/main/graph/badge.svg)](https://codecov.io/gh/Excelsior2026/COGNISCRIBE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Educational-green.svg)](LICENSE)

**AI-powered audio transcription and study note generation for medical and nursing students**

CogniScribe helps you transform lecture recordings into structured study notes with transcription, key concepts, clinical terms, and summaries—all powered by state-of-the-art AI models.

## ✨ Features

- **🎙️ Audio Transcription**: High-quality transcription using OpenAI's Whisper model
- **🧹 Noise Reduction**: Automatic audio preprocessing to clean up lecture hall recordings
- **📝 Structured Notes**: AI-generated study notes with:
  - Learning Objectives
  - Core Concepts
  - Clinical Terms & Definitions
  - Procedures & Protocols
  - Concise Summary
- **🎯 Subject-Aware**: Customize summaries for specific subjects (anatomy, pharmacology, etc.)
- **⚡ Fast Processing**: Optimized pipeline with configurable model sizes
- **🔌 REST API**: Easy integration with your own applications
- **🧪 Thoroughly Tested**: 82% code coverage with 144 comprehensive tests
- **🚀 CI/CD Pipeline**: Automated testing, linting, and quality checks

## ⚠️ Educational Use Notice

CogniScribe is for educational use only. Do not upload live clinical data or PHI. Not for diagnosis, treatment, or clinical decision-making.

## 🚀 Quick Start

### Prerequisites

- **Python 3.11.x** (recommended for prebuilt audio/Whisper dependencies)
- **Ollama** (for summarization) - [Install Ollama](https://ollama.ai/download)
- **FFmpeg** (for audio processing)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Excelsior2026/COGNISCRIBE.git
cd COGNISCRIBE
```

2. **Create a virtualenv and install Python dependencies**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. **Install and start Ollama**
```bash
# Install Ollama from https://ollama.ai/download
# Then pull the model
ollama pull llama3.1:8b
```

4. **Run the API server**
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

5. **Visit the API docs**: Open http://localhost:8080/docs

## 📖 Usage

### Via Web Interface (API Docs)

1. Navigate to http://localhost:8080/docs
2. Click on `POST /api/pipeline`
3. Click "Try it out"
4. Upload your audio file
5. Adjust the `ratio` (summary length, 0.05-1.0)
6. Optionally specify a `subject` (e.g., "anatomy", "pharmacology")
7. Click "Execute" and wait for results

### Via Command Line (curl)

```bash
curl -X POST "http://localhost:8080/api/pipeline?ratio=0.2&subject=anatomy" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@my_lecture.mp3" \
  -o result.json
```

### Via Python

```python
import requests

with open("lecture.mp3", "rb") as f:
    response = requests.post(
        "http://localhost:8080/api/pipeline",
        params={"ratio": 0.15, "subject": "pharmacology"},
        files={"file": f}
    )

result = response.json()
print(result["summary"])
```

## 🧪 Testing

COGNISCRIBE has comprehensive test coverage with 144 tests covering all critical functionality.

### Quick Commands

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_transcriber.py -v

# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Test Coverage

- **Core Services**: 93% coverage (transcription, summarization, preprocessing)
- **API Endpoints**: 92% coverage (health, pipeline, chunk transcription)
- **Error Handling**: 95% coverage (exception hierarchy, error recovery)
- **Security & Validation**: 90% coverage (input sanitization, boundary testing)
- **Overall Project**: 82% coverage

For detailed testing documentation, see [docs/TESTING.md](docs/TESTING.md).

## 🔄 CI/CD Pipeline

Every commit and pull request is automatically:
- ✅ Tested on Python 3.9, 3.10, 3.11
- ✅ Tested on Ubuntu and macOS
- ✅ Linted with flake8
- ✅ Checked for code formatting (black)
- ✅ Scanned for security issues (bandit)
- ✅ Coverage reported to Codecov
- ✅ Required to maintain 80%+ coverage

For CI/CD setup and configuration, see [docs/CI_CD_SETUP.md](docs/CI_CD_SETUP.md).

## ⚙️ Configuration

Configure CogniScribe via environment variables:

### Model Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_MODEL` | `base` | Whisper model size: `tiny`, `base`, `small`, `medium`, `large-v3` |
| `USE_GPU` | `false` | Use GPU acceleration if available |
| `OLLAMA_MODEL` | `llama3.1:8b` | Ollama model for summarization |
| `OLLAMA_HOST` | `localhost` | Ollama server hostname |
| `OLLAMA_PORT` | `11434` | Ollama server port |

### File Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_FILE_SIZE_MB` | `500` | Maximum upload file size |
| `AUDIO_RETENTION_DAYS` | `7` | Days to keep processed audio files |
| `AUDIO_STORAGE_DIR` | `audio_storage` | Directory for uploaded files |
| `TEMP_AUDIO_DIR` | `temp_processed` | Directory for temporary files |

### Performance Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_TIMEOUT` | `300` | Timeout for summarization (seconds) |
| `LOG_LEVEL` | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### Example Configuration

Create a `.env` file or export variables:

```bash
# For faster processing on laptops
export WHISPER_MODEL=small
export OLLAMA_MODEL=llama3.1:8b
export MAX_FILE_SIZE_MB=200

# For maximum quality (requires powerful GPU)
export WHISPER_MODEL=large-v3
export USE_GPU=true
export OLLAMA_MODEL=llama3.1:70b
```

## 🏗️ Docker Deployment

```bash
# Start both API and frontend (Docker Desktop required)
docker compose up -d --build
```

- API available at http://localhost:8080
- Frontend at http://localhost:5173
- Ollama must be running on the host (`ollama serve`) with the model pulled (`ollama pull llama3.1:8b`)
- The Docker image bundles FFmpeg, libsndfile, and libmagic so audio processing works out of the box

## 📊 Supported Audio Formats

- `.wav` - Waveform Audio
- `.mp3` - MPEG Audio
- `.m4a` - MPEG-4 Audio
- `.flac` - Free Lossless Audio Codec
- `.ogg` - Ogg Vorbis
- `.aac` - Advanced Audio Coding
- `.wma` - Windows Media Audio

## 🎓 Tips for Students

### Choosing the Right Model Size

| Model | Speed | Accuracy | RAM Required | Best For |
|-------|-------|----------|--------------|----------|
| `tiny` | ⚡⚡⚡⚡⚡ | ⭐⭐ | ~1 GB | Quick notes, clear audio |
| `base` | ⚡⚡⚡⚡ | ⭐⭐⭐ | ~1.5 GB | **Default - balanced** |
| `small` | ⚡⚡⚡ | ⭐⭐⭐⭐ | ~2 GB | Good quality, reasonable speed |
| `medium` | ⚡⚡ | ⭐⭐⭐⭐⭐ | ~5 GB | High quality transcription |
| `large-v3` | ⚡ | ⭐⭐⭐⭐⭐ | ~10 GB | Maximum accuracy |

### Summary Length (ratio parameter)

- `0.05-0.10`: Very brief bullet points
- `0.15` (default): Balanced summary with key details
- `0.20-0.30`: Detailed notes with examples
- `0.50-1.0`: Comprehensive coverage (near-transcript length)

### Subject Customization

Specify a subject for better-tailored notes:
- `"anatomy"` - Focus on structures and systems
- `"pharmacology"` - Emphasize drugs, mechanisms, side effects
- `"pathophysiology"` - Highlight disease processes
- `"clinical skills"` - Focus on procedures and techniques
- `"nursing fundamentals"` - Patient care and nursing theory

## 🔧 Troubleshooting

### "Could not load Whisper model"
- Try a smaller model: `export WHISPER_MODEL=base`
- Ensure sufficient RAM/VRAM available
- Check internet connection (models download on first use)

### "Cannot connect to Ollama service"
- Verify Ollama is running: `ollama list`
- Check Ollama port: `curl http://localhost:11434/api/tags`
- Ensure model is pulled: `ollama pull llama3.1:8b`

### "File too large"
- Increase limit: `export MAX_FILE_SIZE_MB=1000`
- Or split long recordings into smaller segments

### Slow Processing
- Use a smaller Whisper model (`tiny`, `base`, or `small`)
- Enable GPU if available: `export USE_GPU=true`
- Use a smaller Ollama model: `ollama pull llama3.1:8b`

## 🏛️ Architecture

```
┌─────────────┐
│   Client    │
│ (Upload MP3)│
└──────┬──────┘
       │
       ▼
┌──────────────────────────────┐
│   FastAPI Server            │
│  ┌──────────────────────┐   │
│  │ 1. Validate & Store  │   │
│  └──────────┬───────────┘   │
│             ▼               │
│  ┌──────────────────────┐   │
│  │ 2. Audio Preprocess  │   │
│  │   - Noise Reduction  │   │
│  │   - Normalization    │   │
│  └──────────┬───────────┘   │
│             ▼               │
│  ┌──────────────────────┐   │
│  │ 3. Whisper Transcribe│   │
│  │   - Speech-to-Text   │   │
│  │   - Timestamps       │   │
│  └──────────┬───────────┘   │
│             ▼               │
│  ┌──────────────────────┐   │
│  │ 4. Ollama Summarize  │   │
│  │   - Structured Notes │   │
│  └──────────┬───────────┘   │
└─────────────┼───────────────┘
              ▼
       ┌─────────────┐
       │   Result    │
       │  (JSON)     │
       └─────────────┘
```

## 📚 Documentation

- **[Testing Guide](docs/TESTING.md)** - Comprehensive testing documentation
- **[CI/CD Setup](docs/CI_CD_SETUP.md)** - Continuous integration and deployment guide
- **[API Documentation](http://localhost:8080/docs)** - Interactive API documentation (when server is running)

## 🤝 Contributing

Contributions are welcome! Please ensure:
- ✅ All tests pass (`pytest`)
- ✅ Code coverage remains ≥ 80%
- ✅ Code is formatted with black
- ✅ Imports are sorted with isort
- ✅ No linting errors (flake8)

See [docs/CI_CD_SETUP.md](docs/CI_CD_SETUP.md) for development workflow.

Areas for improvement:
- Speaker diarization (identify multiple speakers)
- Export to Markdown/PDF/Notion
- Batch processing multiple files
- Integration with note-taking apps
- Mobile app support

## 📄 License

This project is designed for educational use by medical and nursing students.

## 🙏 Acknowledgments

- **OpenAI Whisper** - State-of-the-art speech recognition
- **Ollama** - Local LLM inference
- **Meta Llama** - Open-source language models
- Built with **FastAPI** for modern Python APIs

---

**Made with ❤️ for medical and nursing students**

*Have questions? Found a bug? Open an issue on GitHub!*
