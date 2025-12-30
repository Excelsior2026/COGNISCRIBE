import re
import requests
from typing import Optional, Dict
from src.utils.settings import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
from src.utils.errors import ProcessingError, ServiceUnavailableError, ErrorCode
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

_EMPTY_SUMMARY = {
    "objectives": "",
    "concepts": "",
    "terms": "",
    "procedures": "",
    "summary": "",
}


def _normalize_heading(heading: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", "", heading.lower().replace("&", "and"))).strip()


def _map_heading_to_key(heading: str) -> Optional[str]:
    normalized = _normalize_heading(heading)
    if "learning objective" in normalized:
        return "objectives"
    if "core concept" in normalized:
        return "concepts"
    if "clinical term" in normalized or normalized == "terms":
        return "terms"
    if "procedure" in normalized or "protocol" in normalized:
        return "procedures"
    if normalized.endswith("summary") or normalized == "summary":
        return "summary"
    return None


def parse_summary_sections(text: str) -> Dict[str, str]:
    """Parse LLM summary text into structured sections."""
    sections = dict(_EMPTY_SUMMARY)
    if not text:
        return sections

    matches = list(re.finditer(r"^\s*#{2,4}\s*(.+?)\s*$", text, re.MULTILINE))
    if not matches:
        sections["summary"] = text.strip()
        return sections

    for idx, match in enumerate(matches):
        key = _map_heading_to_key(match.group(1))
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if key and content:
            sections[key] = content

    if not any(sections.values()):
        sections["summary"] = text.strip()

    return sections


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
        ServiceUnavailableError: If Ollama is unavailable
        ProcessingError: If summarization fails
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
    
    prompt = f"""You are CogniScribe, an AI assistant helping medical and nursing students learn from lecture recordings.

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
    except requests.exceptions.Timeout as exc:
        logger.error(f"Ollama request timed out after {OLLAMA_TIMEOUT}s")
        raise ServiceUnavailableError(
            message=(
                "Summarization timed out. The transcript may be too long. "
                "Try increasing OLLAMA_TIMEOUT or reducing the audio length."
            ),
            error_code=ErrorCode.OLLAMA_TIMEOUT,
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        logger.error(f"Could not connect to Ollama at {OLLAMA_URL}")
        raise ServiceUnavailableError(
            message=(
                f"Cannot connect to Ollama service at {OLLAMA_URL}. "
                "Ensure Ollama is running and accessible."
            ),
            error_code=ErrorCode.OLLAMA_UNAVAILABLE,
        ) from exc
    except requests.exceptions.RequestException as exc:
        status_code = getattr(exc.response, "status_code", None)
        details = {"status_code": status_code} if status_code else None
        logger.error(f"Ollama request failed: {str(exc)}")
        raise ServiceUnavailableError(
            message="Summarization service returned an error.",
            error_code=ErrorCode.OLLAMA_UNAVAILABLE,
            details=details,
        ) from exc

    try:
        result = response.json()
    except ValueError as exc:
        logger.error(f"Invalid JSON response from Ollama: {str(exc)}")
        raise ProcessingError(
            message="Summarization service returned invalid JSON.",
            error_code=ErrorCode.SUMMARIZATION_FAILED,
        ) from exc

    summary = result.get("response", "")
    if not summary.strip():
        raise ProcessingError(
            message="Summarization service returned empty response.",
            error_code=ErrorCode.SUMMARIZATION_FAILED,
        )

    logger.info(f"Summarization completed: {len(summary)} characters")
    return summary
