import os, uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File
from src.api.services import audio_preprocess, transcriber, summarizer
from src.utils.settings import AUDIO_STORAGE_DIR

router = APIRouter()

@router.post("/pipeline")
async def pipeline(file: UploadFile = File(...), ratio: float = 0.15):
    date_dir = datetime.utcnow().strftime("%Y-%m-%d")
    base = os.path.join(AUDIO_STORAGE_DIR, date_dir)
    os.makedirs(base, exist_ok=True)

    raw = os.path.join(base, f"{uuid.uuid4()}_{file.filename}")
    with open(raw, "wb") as f:
        f.write(await file.read())

    clean = audio_preprocess.preprocess_audio(raw)
    transcript = transcriber.transcribe_audio(clean)
    summary = summarizer.generate_summary(transcript["text"], ratio)

    return {"success": True, "transcript": transcript, "summary": summary}
