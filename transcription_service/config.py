import os
from pathlib import Path

REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = int(os.environ["REDIS_PORT"])
REDIS_DB = int(os.environ["REDIS_DB"])
UPLOADS_DIR = Path(os.environ["UPLOADS_DIR"])
TRANSCRIPTIONS_DIR = Path(os.environ["TRANSCRIPTIONS_DIR"])

# Default values for the whisper model are set as the codebase is shared by both API and worker, and the former
# is independent/does not rely on them, so it shouldn't crash if they are not set.
WHISPER_MODEL_NAME = os.environ.get("WHISPER_MODEL_NAME", "base")
WHISPER_MODEL_DEVICE = os.environ.get("WHISPER_MODEL_DEVICE", "cpu")
