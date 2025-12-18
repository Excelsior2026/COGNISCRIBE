import requests
from typing import Optional
from src.utils.settings import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def generate_summary(text: str, ratio: float = 0.15, subject: Optional[str] = None) -> str:
    """
    Generate structured clinical study notes using Ollama.
    
    Args:
        text: Transcript text to summarize
        ratio: Target summary length ratio (0.0-1.0)
        subject: Optional subject/topic for tailored summaries (e.g., 'anatomy', 'pharmacology')
        
    Returns:
        Formatted summary text
        
    Raises:
        RuntimeError: If Ollama service is unavailable or summarization fails
    """
    logger.info(f"Starting summarization (ratio={ratio}, subject={subject})")
    
    # Validate ratio
    if not 0.0 <= ratio <= 1.0:
        logger.warning(f"Invalid ratio {ratio}, using default 0.15")
        ratio = 0.15
    
    # Calculate target tokens (Ollama uses num_predict)
    num_predict = int(len(text.split()) * ratio * 1.8)
    
    # Build subject-specific prompt
    subject_context = f" Focus on {subject} content." if subject else ""
    
    prompt = f"""You are CliniScribe, an AI assistant helping medical and nursing students learn from lecture recordings.

Generate well-structured study notes in the following format:

### Learning Objectives
[Key learning goals from this content]

### Core Concepts
[Main theoretical concepts and principles]

### Clinical Terms
[Important medical terminology and definitions]

### Procedures
[Any clinical procedures, techniques, or protocols discussed]

### Summary
[Concise overview connecting all concepts]{subject_context}

Transcript:
{text}
"""
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": num_predict
        }
    }
    
    try:
        logger.debug(f"Sending request to Ollama at {OLLAMA_URL}")
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=OLLAMA_TIMEOUT
        )
        response.raise_for_status()
        
        result = response.json()
        summary = result.get("response", "")
        
        if not summary:
            raise ValueError("Empty response from Ollama")
        
        logger.info(f"Summarization completed: {len(summary)} characters")
        return summary
        
    except requests.exceptions.Timeout:
        logger.error(f"Ollama request timed out after {OLLAMA_TIMEOUT}s")
        raise RuntimeError(
            f"Summarization timed out. The transcript may be too long. "
            f"Try increasing OLLAMA_TIMEOUT or reducing the audio length."
        )
    except requests.exceptions.ConnectionError:
        logger.error(f"Could not connect to Ollama at {OLLAMA_URL}")
        raise RuntimeError(
            f"Cannot connect to Ollama service at {OLLAMA_URL}. "
            f"Ensure Ollama is running and accessible."
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama request failed: {str(e)}")
        raise RuntimeError(f"Summarization failed: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error during summarization: {str(e)}")
        raise RuntimeError(f"Failed to generate summary: {str(e)}") from e
