from pathlib import Path

from transcription_service.models import MediaType


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


def transcribe_audio(reference_id: str):
    """
    Transcribe an audio file.

    Args:
        reference_id (str): The reference ID of the audio file.
    """
    # Placeholder for the actual transcription


def transcribe_video(reference_id: str):
    """
    Transcribe a video file.

    Args:
        reference_id (str): The reference ID of the video file.
    """
    # Placeholder for the actual transcription
    pass
