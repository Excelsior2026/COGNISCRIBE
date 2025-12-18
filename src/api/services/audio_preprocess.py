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
