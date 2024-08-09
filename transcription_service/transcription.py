import tempfile
from functools import lru_cache
from pathlib import Path

import ffmpeg
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


def _transcribe_audio(path: Path) -> str:
    model = load_whisper_model(config.WHISPER_MODEL_NAME, config.WHISPER_MODEL_DEVICE)
    result = model.transcribe(str(path))
    return result["text"]


def transcribe_audio_task(reference_id: str) -> None:
    """
    Transcribe an audio file with the given reference ID. The transcription result will be saved to a file in the
    configured transcriptions directory.

    Args:
        reference_id (str): The reference ID of the audio file.
    """
    audio_path = config.UPLOADS_DIR / f"{reference_id}"
    results = _transcribe_audio(audio_path)

    # Save transcription
    with open(config.TRANSCRIPTIONS_DIR / f"{reference_id}.txt", "w", encoding="utf-8") as f:
        f.write(results)


def _extract_audio_from_video(video_path: Path, audio_path: Path) -> None:
    stream = ffmpeg.input(str(video_path))
    stream = ffmpeg.output(stream, filename=str(audio_path), acodec="pcm_s16le", ac=1, ar="16k")
    ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
    # It raises an exception if the command fails / returns non-zero internally.


def transcribe_video_task(reference_id: str) -> None:
    """
    Transcribe a video file with the given reference ID. The transcription result will be saved to a file in the
    configured transcriptions directory.

    Args:
        reference_id (str): The reference ID of the video file.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        video_path = config.UPLOADS_DIR / f"{reference_id}"
        temp_audio_path = Path(temp_dir) / "audio.wav"
        _extract_audio_from_video(video_path, temp_audio_path)
        results = _transcribe_audio(temp_audio_path)

        # Save transcription
        with open(config.TRANSCRIPTIONS_DIR / f"{reference_id}.txt", "w", encoding="utf-8") as f:
            f.write(results)
