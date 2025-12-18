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
