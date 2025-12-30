import glob
import os
import shutil
import subprocess
import uuid
from typing import Dict, Optional, Tuple

import librosa
import soundfile as sf
import noisereduce as nr
from pydub import AudioSegment
from src.utils.settings import (
    TEMP_AUDIO_DIR,
    DEEPFILTERNET_BIN,
    DEEPFILTERNET_ENABLED,
    DEEPFILTERNET_MODEL,
    DEEPFILTERNET_USE_POSTFILTER,
)
from src.utils.errors import ProcessingError, ErrorCode
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Ensure temp directory exists
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

def _load_audio_segment(path: str) -> AudioSegment:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".wav":
        return AudioSegment.from_wav(path)
    return AudioSegment.from_file(path)


def preprocess_audio(path: str, use_deepfilter: Optional[bool] = None) -> Tuple[str, Dict[str, object]]:
    """
    Preprocess audio file: convert to mono, normalize, reduce noise,
    with optional DeepFilterNet enhancement (offline).
    
    Args:
        path: Path to input audio file
        
    Returns:
        Path to processed audio file
        
    Raises:
        ValueError: If audio file is corrupted or unsupported
        RuntimeError: If preprocessing fails
    """
    logger.info(f"Starting audio preprocessing for: {path}")
    base_id = uuid.uuid4()
    out = os.path.join(TEMP_AUDIO_DIR, f"{base_id}_clean.wav")
    mono_48k = os.path.join(TEMP_AUDIO_DIR, f"{base_id}_mono_48k.wav")
    temp_paths = [mono_48k]
    temp_dirs = []
    used_deepfilter = False
    
    try:
        # Convert to mono at 48 kHz (DeepFilterNet expects full-band audio)
        logger.debug("Converting audio to mono at 48kHz")
        audio = _load_audio_segment(path).set_channels(1).set_frame_rate(48000)
        audio.export(mono_48k, format="wav")

        enhanced_source = mono_48k
        enable_deepfilter = DEEPFILTERNET_ENABLED if use_deepfilter is None else use_deepfilter
        if enable_deepfilter:
            enhanced_path, df_dir = run_deepfilternet(mono_48k)
            if df_dir:
                temp_dirs.append(df_dir)
            if enhanced_path:
                enhanced_source = enhanced_path
                used_deepfilter = True
                logger.info("DeepFilterNet enhancement applied")
            else:
                logger.warning("DeepFilterNet enhancement skipped; falling back to standard preprocessing")

        # Resample to 16 kHz for transcription
        logger.debug("Resampling audio to 16kHz for transcription")
        audio = _load_audio_segment(enhanced_source).set_channels(1).set_frame_rate(16000)
        audio.export(out, format="wav")
        
        # Load and apply noise reduction
        if not used_deepfilter:
            logger.debug("Applying noise reduction")
        y, sr = librosa.load(out, sr=16000)
        if not used_deepfilter:
            y = nr.reduce_noise(y=y, sr=sr)
        y = librosa.util.normalize(y)
        
        # Save processed audio
        sf.write(out, y, sr)
        logger.info(f"Audio preprocessing completed: {out}")
        return out, {"enhanced": used_deepfilter, "enhancer": "deepfilternet" if used_deepfilter else None}
        
    except Exception as e:
        logger.error(f"Audio preprocessing failed: {str(e)}")
        # Clean up partial output if it exists
        if os.path.exists(out):
            os.remove(out)
        raise ProcessingError(
            message=f"Failed to preprocess audio: {str(e)}",
            error_code=ErrorCode.PREPROCESSING_FAILED,
        ) from e
    finally:
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
        for temp_dir in temp_dirs:
            shutil.rmtree(temp_dir, ignore_errors=True)


def run_deepfilternet(input_path: str) -> Tuple[Optional[str], Optional[str]]:
    """Run DeepFilterNet CLI if available; returns (output_path, output_dir)."""
    bin_path = resolve_deepfilternet_bin()
    if not bin_path:
        logger.warning("DeepFilterNet binary not found; skipping enhancement")
        return None, None

    output_dir = os.path.join(TEMP_AUDIO_DIR, f"df_{uuid.uuid4()}")
    os.makedirs(output_dir, exist_ok=True)

    cmd = [bin_path, input_path, "-o", output_dir]
    if DEEPFILTERNET_MODEL:
        if os.path.exists(DEEPFILTERNET_MODEL):
            cmd.extend(["-m", DEEPFILTERNET_MODEL])
        else:
            logger.warning("DeepFilterNet model not found at %s; using default model", DEEPFILTERNET_MODEL)
    if DEEPFILTERNET_USE_POSTFILTER:
        cmd.append("--pf")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.warning("DeepFilterNet failed: %s", result.stderr.strip())
        return None, output_dir

    expected = os.path.join(output_dir, os.path.basename(input_path))
    if os.path.exists(expected):
        return expected, output_dir

    matches = sorted(
        glob.glob(os.path.join(output_dir, "*.wav")),
        key=os.path.getmtime,
        reverse=True,
    )
    if matches:
        return matches[0], output_dir

    logger.warning("DeepFilterNet produced no output files")
    return None, output_dir


def resolve_deepfilternet_bin() -> Optional[str]:
    """Resolve DeepFilterNet binary path from settings or PATH."""
    if os.path.isabs(DEEPFILTERNET_BIN) or os.path.sep in DEEPFILTERNET_BIN:
        return DEEPFILTERNET_BIN if os.path.exists(DEEPFILTERNET_BIN) else None
    return shutil.which(DEEPFILTERNET_BIN)


def cleanup_temp_file(path: str) -> None:
    """Safely remove a temporary audio file."""
    try:
        if os.path.exists(path):
            os.remove(path)
            logger.debug(f"Cleaned up temp file: {path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temp file {path}: {str(e)}")
