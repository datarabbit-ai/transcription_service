from functools import lru_cache
from pathlib import Path

import whisper

from transcription_service import config
from transcription_service.models import MediaType


# TODO: investigate how RQ is working, as it seems the model is re-created each time.
@lru_cache(maxsize=1)
def load_whisper_model(model_name: str, device: str) -> whisper.Whisper:
    return whisper.load_model(model_name).to(device)


def determine_media_type(path: Path) -> MediaType:
    """
    Determine the media type of the file at the given path.

    Args:
        path (Path): Path to the file.

    Returns:
        MediaType: The media type of the file.
    """
    ext = path.suffix.lower()
    if ext in (".mp4", ".mov", ".avi", ".mkv"):
        return MediaType.VIDEO
    elif ext in (".mp3", ".wav", ".flac"):
        return MediaType.AUDIO
    else:
        return MediaType.OTHER


def transcribe_audio(reference_id: str) -> None:
    """
    Transcribe an audio file with the given reference ID. The transcription result will be saved to a file in the
    configured transcriptions directory.

    Args:
        reference_id (str): The reference ID of the audio file.
    """
    model = load_whisper_model(config.WHISPER_MODEL_NAME, config.WHISPER_MODEL_DEVICE)

    result = model.transcribe(str(config.UPLOADS_DIR / f"{reference_id}"))

    # Save transcription
    with open(config.TRANSCRIPTIONS_DIR / f"{reference_id}.txt", "w", encoding="utf-8") as f:
        f.write(result["text"])


def transcribe_video(reference_id: str):
    """
    Transcribe a video file with the given reference ID. The transcription result will be saved to a file in the
    configured transcriptions directory.

    Args:
        reference_id (str): The reference ID of the video file.
    """
    # Placeholder for the actual transcription
    pass
