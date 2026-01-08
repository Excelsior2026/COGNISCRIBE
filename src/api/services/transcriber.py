from typing import Optional, Dict, Any
from faster_whisper import WhisperModel
from src.utils.settings import WHISPER_MODEL, DEVICE, COMPUTE_TYPE
from src.utils.errors import ProcessingError, ErrorCode
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Lazy load model on first use
_model: Optional[WhisperModel] = None


def get_model() -> WhisperModel:
    """Lazy load and return the Whisper model."""
    global _model
    if _model is None:
        logger.info(f"Loading Whisper model: {WHISPER_MODEL} on {DEVICE} ({COMPUTE_TYPE})")
        try:
            _model = WhisperModel(
                WHISPER_MODEL,
                device=DEVICE,
                compute_type=COMPUTE_TYPE
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            raise ProcessingError(
                message=(
                    f"Could not load Whisper model '{WHISPER_MODEL}'. "
                    "Ensure the model is downloaded or use a smaller model (tiny, base, small)."
                ),
                error_code=ErrorCode.WHISPER_MODEL_LOAD_FAILED,
            ) from e
    return _model


def transcribe_audio(path: str) -> Dict[str, Any]:
    """
    Transcribe audio file using Whisper.
    
    Args:
        path: Path to audio file
        
    Returns:
        Dictionary containing:
        - text: Full transcription
        - segments: List of segments with timestamps and confidence
        - language: Detected language
        - duration: Audio duration in seconds
        
    Raises:
        RuntimeError: If transcription fails
    """
    logger.info(f"Starting transcription for: {path}")
    
    try:
        model = get_model()
        segments, info = model.transcribe(
            path,
            vad_filter=True,
            word_timestamps=True
        )
        
        text_parts = []
        segment_list = []
        
        logger.debug(f"Processing segments (language: {info.language}, duration: {info.duration:.2f}s)")
        
        for segment in segments:
            text_parts.append(segment.text.strip())
            segment_list.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment.text.strip(),
                "confidence": round(segment.avg_logprob, 3)
            })
        
        result = {
            "text": " ".join(text_parts),
            "segments": segment_list,
            "language": info.language,
            "duration": round(info.duration, 2)
        }
        
        logger.info(f"Transcription completed: {len(segment_list)} segments, {len(result['text'])} characters")
        return result
        
    except FileNotFoundError as e:
        logger.error(f"Audio file not found: {str(e)}")
        raise ProcessingError(
            message=f"Audio file not found: {str(e)}",
            error_code=ErrorCode.TRANSCRIPTION_FAILED,
        ) from e
    except RuntimeError as e:
        logger.error(f"Whisper runtime error: {str(e)}")
        raise ProcessingError(
            message=f"Transcription runtime error: {str(e)}",
            error_code=ErrorCode.TRANSCRIPTION_FAILED,
        ) from e
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}", exc_info=True)
        raise ProcessingError(
            message=f"Failed to transcribe audio: {str(e)}",
            error_code=ErrorCode.TRANSCRIPTION_FAILED,
        ) from e
