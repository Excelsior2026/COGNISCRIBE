#!/usr/bin/env bash
set -euo pipefail

echo "🔁 Filling CliniScribe files with canonical code..."

################################
# PYTHON BACKEND
################################

cat > src/utils/settings.py << 'EOF'
import os

AUDIO_RETENTION_DAYS = int(os.environ.get("AUDIO_RETENTION_DAYS", 7))
AUDIO_STORAGE_DIR = os.environ.get("AUDIO_STORAGE_DIR", "audio.tmp")
EOF

cat > src/api/services/audio_preprocess.py << 'EOF'
import os, uuid, librosa, soundfile as sf, noisereduce as nr
from pydub import AudioSegment

TEMP_DIR = "temp_processed"
os.makedirs(TEMP_DIR, exist_ok=True)

def preprocess_audio(path: str) -> str:
    out = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_clean.wav")
    audio = AudioSegment.from_file(path).set_channels(1).set_frame_rate(16000)
    audio.export(out, format="wav")

    y, sr = librosa.load(out, sr=16000)
    y = nr.reduce_noise(y=y, sr=sr)
    y = librosa.util.normalize(y)

    sf.write(out, y, sr)
    return out
EOF

cat > src/api/services/transcriber.py << 'EOF'
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
EOF

cat > src/api/services/summarizer.py << 'EOF'
import os, requests

OLLAMA_URL = f"http://{os.getenv('OLLAMA_HOST','localhost')}:{os.getenv('OLLAMA_PORT','11434')}/api/generate"
MODEL = "llama3.1:8b"

def generate_summary(text: str, ratio=0.15):
    max_tokens = int(len(text.split()) * ratio * 1.8)

    prompt = f"""
You are CliniScribe. Generate structured clinical study notes.

### Learning Objectives
### Core Concepts
### Clinical Terms
### Procedures
### Final Summary

Transcript:
{text}
"""

    r = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature":0.2,"max_tokens":max_tokens}
    })

    return r.json()["response"]
EOF

cat > src/api/services/cleanup.py << 'EOF'
import os, shutil
from datetime import datetime, timedelta
from src.utils.settings import AUDIO_STORAGE_DIR, AUDIO_RETENTION_DAYS

def cleanup_old_audio():
    cutoff = datetime.utcnow() - timedelta(days=AUDIO_RETENTION_DAYS)

    for folder in os.listdir(AUDIO_STORAGE_DIR):
        try:
            date = datetime.strptime(folder, "%Y-%m-%d")
            if date < cutoff:
                shutil.rmtree(os.path.join(AUDIO_STORAGE_DIR, folder))
        except:
            continue
EOF

cat > src/api/routers/pipeline.py << 'EOF'
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
EOF

cat > src/api/main.py << 'EOF'
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from src.api.routers.pipeline import router
from src.api.services.cleanup import cleanup_old_audio

app = FastAPI(title="CliniScribe API")

app.include_router(router, prefix="/api")

@app.on_event("startup")
@repeat_every(seconds=86400)
def retention():
    cleanup_old_audio()
EOF

################################
# DOCKER
################################

cat > docker/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn","src.api.main:app","--host","0.0.0.0","--port","8080"]
EOF

cat > docker-compose.yml << 'EOF'
version: "3.9"
services:
  api:
    build: .
    ports: ["8080:8080"]
    environment:
      OLLAMA_HOST: host.docker.internal
      OLLAMA_PORT: 11434
    extra_hosts:
      - "host.docker.internal:host-gateway"

  frontend:
    build: ./client/web-react
    ports: ["5173:80"]
EOF

################################
# FRONTEND
################################

cat > client/web-react/src/api/pipeline.js << 'EOF'
export async function runPipeline(file) {
  const fd = new FormData()
  fd.append("file", file)
  const r = await fetch("/api/pipeline", { method:"POST", body:fd })
  return r.json()
}
EOF

cat > client/web-react/src/App.jsx << 'EOF'
import {useState} from "react"
import UploadCard from "./components/UploadCard"
import ResultsPanel from "./components/ResultsPanel"

export default function App(){
  const [data,setData]=useState(null)
  return (
    <div className="max-w-4xl mx-auto p-8">
      <UploadCard onResult={setData}/>
      {data && <ResultsPanel data={data}/>}
    </div>
  )
}
EOF

cat > client/web-react/src/components/UploadCard.jsx << 'EOF'
import {runPipeline} from "../api/pipeline"

export default function UploadCard({onResult}){
  return (
    <input type="file" onChange={async e=>{
      const res = await runPipeline(e.target.files[0])
      onResult(res)
    }}/>
  )
}
EOF

echo "✅ All conversation snippets written into their files."
echo "Next:"
echo "  git status"
echo "  git add ."
echo "  git commit -m \"CliniScribe canonical snapshot from conversation\""
echo "  git push origin main"
