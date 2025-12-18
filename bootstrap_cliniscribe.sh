#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Bootstrapping CliniScribe project structure..."

# Directories
mkdir -p docker
mkdir -p src/api/routers
mkdir -p src/api/services
mkdir -p src/utils
mkdir -p client/web-react/src/api
mkdir -p client/web-react/src/components
mkdir -p client/web-react/src/styles

################################
# ROOT FILES
################################

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

cat > requirements.txt << 'EOF'
fastapi
uvicorn[standard]
fastapi-utils
faster-whisper
librosa
soundfile
noisereduce
pydub
requests
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

# Minimal nginx.conf placeholder (you can customize later)
cat > docker/nginx.conf << 'EOF'
worker_processes 1;
events { worker_connections 1024; }
http {
  server {
    listen 80;
    location / {
      root /usr/share/nginx/html;
      try_files $uri /index.html;
    }
    location /api/ {
      proxy_pass http://api:8080/;
    }
  }
}
EOF

################################
# PYTHON PACKAGE INIT
################################

cat > src/__init__.py << 'EOF'
# CliniScribe package
EOF

################################
# SETTINGS
################################

cat > src/utils/settings.py << 'EOF'
import os

AUDIO_RETENTION_DAYS = int(os.environ.get("AUDIO_RETENTION_DAYS", 7))
AUDIO_STORAGE_DIR = os.environ.get("AUDIO_STORAGE_DIR", "audio.tmp")
EOF

################################
# SERVICES
################################

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

    if not os.path.exists(AUDIO_STORAGE_DIR):
        return

    for folder in os.listdir(AUDIO_STORAGE_DIR):
        try:
            date = datetime.strptime(folder, "%Y-%m-%d")
            if date < cutoff:
                shutil.rmtree(os.path.join(AUDIO_STORAGE_DIR, folder))
        except Exception:
            continue
EOF

################################
# ROUTERS
################################

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

# Simple healthcheck router (not in your paste, but useful)
cat > src/api/routers/healthcheck.py << 'EOF'
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}
EOF

################################
# MAIN FASTAPI APP
################################

cat > src/api/main.py << 'EOF'
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from src.api.routers.pipeline import router as pipeline_router
from src.api.routers.healthcheck import router as health_router
from src.api.services.cleanup import cleanup_old_audio

app = FastAPI(title="CliniScribe API")

app.include_router(pipeline_router, prefix="/api")
app.include_router(health_router, prefix="/api")

@app.on_event("startup")
@repeat_every(seconds=86400)
def retention():
    cleanup_old_audio()
EOF

################################
# FRONTEND: API
################################

cat > client/web-react/src/api/pipeline.js << 'EOF'
export async function runPipeline(file) {
  const fd = new FormData()
  fd.append("file", file)
  const r = await fetch("/api/pipeline", { method:"POST", body:fd })
  if (!r.ok) {
    throw new Error("Pipeline request failed")
  }
  return r.json()
}
EOF

################################
# FRONTEND: COMPONENTS
################################

cat > client/web-react/src/components/UploadCard.jsx << 'EOF'
import { useState } from "react"
import { runPipeline } from "../api/pipeline"

export default function UploadCard({ onResult }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setError(null)
    setLoading(true)
    try {
      const res = await runPipeline(file)
      onResult(res)
    } catch (err) {
      setError(err.message || "Upload failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="border rounded p-4">
      <input type="file" onChange={handleChange} />
      {loading && <p className="mt-2 text-sm text-gray-500">Processing...</p>}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  )
}
EOF

cat > client/web-react/src/components/ResultsPanel.jsx << 'EOF'
export default function ResultsPanel({ data }) {
  const { transcript, summary } = data || {}
  return (
    <div className="mt-6 space-y-4">
      <section>
        <h2 className="text-lg font-semibold mb-2">Summary</h2>
        <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded border">
          {summary}
        </pre>
      </section>
      <section>
        <h2 className="text-lg font-semibold mb-2">Transcript</h2>
        <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded border text-sm max-h-96 overflow-auto">
          {transcript?.text}
        </pre>
      </section>
    </div>
  )
}
EOF

cat > client/web-react/src/components/LoadingSpinner.jsx << 'EOF'
export default function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center p-4">
      <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full" />
    </div>
  )
}
EOF

################################
# FRONTEND: APP & ENTRY
################################

cat > client/web-react/src/App.jsx << 'EOF'
import { useState } from "react"
import UploadCard from "./components/UploadCard"
import ResultsPanel from "./components/ResultsPanel"

export default function App(){
  const [data,setData]=useState(null)
  return (
    <div className="max-w-4xl mx-auto p-8 space-y-6">
      <h1 className="text-2xl font-bold mb-4">CliniScribe</h1>
      <UploadCard onResult={setData}/>
      {data && <ResultsPanel data={data}/>}
    </div>
  )
}
EOF

cat > client/web-react/src/main.jsx << 'EOF'
import React from "react"
import ReactDOM from "react-dom/client"
import App from "./App"
import "./styles/index.css"

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
EOF

################################
# FRONTEND: CONFIG & STATIC
################################

cat > client/web-react/index.html << 'EOF'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>CliniScribe</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
EOF

cat > client/web-react/package.json << 'EOF'
{
  "name": "cliniscribe-web",
  "version": "0.0.1",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.13",
    "vite": "^5.4.0"
  }
}
EOF

cat > client/web-react/vite.config.js << 'EOF'
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8080",
        changeOrigin: true
      }
    }
  }
})
EOF

cat > client/web-react/postcss.config.js << 'EOF'
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
EOF

cat > client/web-react/tailwind.config.js << 'EOF'
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
EOF

cat > client/web-react/src/styles/index.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  @apply bg-gray-100 text-gray-900;
}
EOF

cat > client/web-react/Dockerfile << 'EOF'
FROM node:20 AS build
WORKDIR /app
COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* .npmrc* ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY ../docker/nginx.conf /etc/nginx/nginx.conf
EOF

echo "✅ CliniScribe structure and files created."
echo "Next steps:"
echo "  1) git add ."
echo "  2) git commit -m \"Initial CliniScribe snapshot\""
echo "  3) git push origin main"

