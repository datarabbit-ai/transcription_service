import os
from pathlib import Path

WHISPER_MODEL_NAME = os.environ["WHISPER_MODEL_NAME"]
WHISPER_MODEL_DEVICE = os.environ["WHISPER_MODEL_DEVICE"]
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = int(os.environ["REDIS_PORT"])
REDIS_DB = int(os.environ["REDIS_DB"])
UPLOADS_DIR = Path(os.environ["UPLOADS_DIR"])
TRANSCRIPTIONS_DIR = Path(os.environ["TRANSCRIPTIONS_DIR"])
