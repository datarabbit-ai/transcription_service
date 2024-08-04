from contextlib import asynccontextmanager

import whisper
from fastapi import FastAPI
from redis import Redis
from rq import Queue

from transcription_service import config
from transcription_service.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Run at startup
    Initialise the global objects and add them to app.state
    """
    config.UPLOADS_DIR.mkdir(exist_ok=True)
    config.TRANSCRIPTIONS_DIR.mkdir(exist_ok=True)

    app.state.transcription_model = whisper.load_model(config.WHISPER_MODEL_NAME)
    app.state.redis_conn = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)
    app.state.queue = Queue(connection=app.state.redis_conn)
    yield
    """ 
    Run on shutdowns – close the connections, clear variables and release the resources.
    """


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
