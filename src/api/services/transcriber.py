import os
from faster_whisper import WhisperModel

MODEL = os.environ.get("WHISPER_MODEL", "large-v3")
DEVICE = "cuda" if os.environ.get("USE_GPU", "true") == "true" else "cpu"
TYPE = "float16" if DEVICE == "cuda" else "int8"

model = WhisperModel(MODEL, device=DEVICE, compute_type=TYPE)

def transcribe_audio(path: str):
    segments, info = model.transcribe(path, vad_filter=True, word_timestamps=True)
    text, segs = [], []

    for s in segments:
        text.append(s.text.strip())
        segs.append({
            "start": s.start,
            "end": s.end,
            "text": s.text.strip(),
            "confidence": s.avg_logprob
        })

    return {
        "text": " ".join(text),
        "segments": segs,
        "language": info.language,
        "duration": info.duration
    }
