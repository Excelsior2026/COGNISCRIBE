import os
import uuid
import librosa
import soundfile as sf
import noisereduce as nr
from pydub import AudioSegment
from src.utils.settings import TEMP_AUDIO_DIR
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Ensure temp directory exists
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)


def preprocess_audio(path: str) -> str:
    """
    Preprocess audio file: convert to mono, normalize, reduce noise.
    
    Args:
        path: Path to input audio file
        
    Returns:
        Path to processed audio file
        
    Raises:
        ValueError: If audio file is corrupted or unsupported
        RuntimeError: If preprocessing fails
    """
    logger.info(f"Starting audio preprocessing for: {path}")
    out = os.path.join(TEMP_AUDIO_DIR, f"{uuid.uuid4()}_clean.wav")
    
    try:
        # Convert to mono and resample
        logger.debug("Converting audio to mono and resampling to 16kHz")
        audio = AudioSegment.from_file(path).set_channels(1).set_frame_rate(16000)
        audio.export(out, format="wav")
        
        # Load and apply noise reduction
        logger.debug("Applying noise reduction")
        y, sr = librosa.load(out, sr=16000)
        y = nr.reduce_noise(y=y, sr=sr)
        y = librosa.util.normalize(y)
        
        # Save processed audio
        sf.write(out, y, sr)
        logger.info(f"Audio preprocessing completed: {out}")
        return out
        
    except Exception as e:
        logger.error(f"Audio preprocessing failed: {str(e)}")
        # Clean up partial output if it exists
        if os.path.exists(out):
            os.remove(out)
        raise RuntimeError(f"Failed to preprocess audio: {str(e)}") from e


def cleanup_temp_file(path: str) -> None:
    """Safely remove a temporary audio file."""
    try:
        if os.path.exists(path):
            os.remove(path)
            logger.debug(f"Cleaned up temp file: {path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temp file {path}: {str(e)}")
