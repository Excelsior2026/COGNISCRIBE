"""Pytest configuration and shared fixtures for CogniScribe tests."""
import os
import tempfile
import pytest
from pathlib import Path
from typing import Generator
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# Set test environment variables before importing app
os.environ["COGNISCRIBE_AUTH_ENABLED"] = "false"
os.environ["PHI_DETECTION_ENABLED"] = "true"
os.environ["WHISPER_MODEL"] = "tiny"
os.environ["OLLAMA_HOST"] = "localhost"
os.environ["OLLAMA_TIMEOUT"] = "60"
os.environ["LOG_LEVEL"] = "DEBUG"

from src.api.main import app
from src.utils import settings


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Get path to test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def mock_audio_storage(temp_dir: Path, monkeypatch) -> Path:
    """Mock audio storage directory."""
    storage_dir = temp_dir / "audio_storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "AUDIO_STORAGE_DIR", str(storage_dir))
    return storage_dir


@pytest.fixture(scope="function")
def mock_temp_audio(temp_dir: Path, monkeypatch) -> Path:
    """Mock temporary audio processing directory."""
    temp_audio_dir = temp_dir / "temp_audio"
    temp_audio_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "TEMP_AUDIO_DIR", str(temp_audio_dir))
    return temp_audio_dir


@pytest.fixture(scope="function")
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture(scope="function")
def sample_audio_file(test_data_dir: Path) -> Path:
    """Path to sample audio file (10 seconds).
    
    Note: Create actual test audio files in tests/fixtures/
    For now, this returns a placeholder path.
    """
    audio_file = test_data_dir / "sample_lecture_10s.mp3"
    
    # If file doesn't exist, create a minimal MP3 for testing
    if not audio_file.exists():
        test_data_dir.mkdir(parents=True, exist_ok=True)
        # Create minimal valid MP3 header (silence)
        # This is a minimal MP3 frame - not real audio but valid format
        mp3_header = bytes([
            0xFF, 0xFB, 0x90, 0x00,  # MP3 sync word + header
            0x00, 0x00, 0x00, 0x00,
        ] * 100)  # Repeat to make ~800 bytes
        audio_file.write_bytes(mp3_header)
    
    return audio_file


@pytest.fixture(scope="function")
def sample_transcript() -> dict:
    """Sample transcript from Whisper."""
    return {
        "text": (
            "Today we will discuss the cardiovascular system. "
            "The heart has four chambers: two atria and two ventricles. "
            "The right atrium receives deoxygenated blood from the body. "
            "The blood then flows to the right ventricle and is pumped to the lungs. "
            "In the lungs, blood picks up oxygen through gas exchange. "
            "Oxygenated blood returns to the left atrium, flows to the left ventricle, "
            "and is pumped throughout the body via the aorta."
        ),
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 3.5,
                "text": "Today we will discuss the cardiovascular system."
            },
            {
                "id": 1,
                "start": 3.5,
                "end": 7.0,
                "text": "The heart has four chambers: two atria and two ventricles."
            }
        ],
        "language": "en",
        "duration": 45.0
    }


@pytest.fixture(scope="function")
def sample_transcript_with_phi() -> str:
    """Sample transcript containing PHI for testing rejection."""
    return (
        "Patient John Smith, DOB 05/15/1985, was admitted today. "
        "Medical record number MRN12345678. "
        "His SSN is 123-45-6789 and phone number is 555-123-4567. "
        "Diagnosed with hypertension, prescribed lisinopril 10mg."
    )


@pytest.fixture(scope="function")
def sample_summary() -> str:
    """Sample summary from Ollama."""
    return """
## Learning Objectives
- Understand the structure of the heart
- Explain blood flow through cardiac chambers
- Describe pulmonary and systemic circulation

## Core Concepts

### Cardiac Anatomy
The heart is a four-chambered muscular organ consisting of two atria (upper chambers) 
and two ventricles (lower chambers).

### Blood Flow Pathway
Deoxygenated blood → Right atrium → Right ventricle → Lungs → Left atrium → 
Left ventricle → Body

## Clinical Terms

**Atrium** - Upper chamber of the heart that receives blood

**Ventricle** - Lower chamber of the heart that pumps blood

**Aorta** - Largest artery in the body, carries oxygenated blood from left ventricle

**Pulmonary circulation** - Blood flow between heart and lungs

## Summary
The cardiovascular system consists of the heart and blood vessels. The heart's four 
chambers work in coordination to pump blood through pulmonary circulation (to the lungs) 
and systemic circulation (to the body). Understanding this pathway is fundamental to 
comprehending cardiovascular physiology.
"""


@pytest.fixture(scope="function")
def mock_whisper_transcribe(sample_transcript: dict):
    """Mock Whisper transcription."""
    with patch("src.api.services.transcriber.transcribe_audio") as mock:
        mock.return_value = sample_transcript
        yield mock


@pytest.fixture(scope="function")
def mock_ollama_summarize(sample_summary: str):
    """Mock Ollama summarization."""
    with patch("src.api.services.summarizer.generate_summary") as mock:
        mock.return_value = sample_summary
        yield mock


@pytest.fixture(scope="function")
def mock_audio_preprocess():
    """Mock audio preprocessing."""
    with patch("src.api.services.audio_preprocess.preprocess_audio") as mock:
        mock.return_value = (
            "/tmp/processed_audio.wav",
            {"enhanced": False, "enhancer": None}
        )
        yield mock


@pytest.fixture(scope="function")
def mock_full_pipeline(
    mock_audio_preprocess,
    mock_whisper_transcribe,
    mock_ollama_summarize
):
    """Mock entire processing pipeline."""
    return {
        "preprocess": mock_audio_preprocess,
        "transcribe": mock_whisper_transcribe,
        "summarize": mock_ollama_summarize
    }


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment after each test."""
    yield
    # Cleanup code here if needed


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual functions"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests with mocked services"
    )
    config.addinivalue_line(
        "markers", "api: API endpoint tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests (skip with -m 'not slow')"
    )
    config.addinivalue_line(
        "markers", "requires_ollama: Tests requiring actual Ollama service"
    )
    config.addinivalue_line(
        "markers", "requires_whisper: Tests requiring actual Whisper model"
    )
