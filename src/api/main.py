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
