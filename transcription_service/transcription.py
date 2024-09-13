import json
import tempfile
from pathlib import Path

import ffmpeg
import torch
import whisper
from pyannote.audio import Pipeline

from transcription_service import config
from transcription_service.models import MediaType
from transcription_service.utils import diarize_text


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


def init_whisper_model(model_name: str, device: str) -> whisper.Whisper:
    """
    Init helper class responsible for setting up global whisper model instance – necessary because of how the
    redis queue workers are implemented.
    """
    global TRANSCRIPTION_MODEL
    TRANSCRIPTION_MODEL = whisper.load_model(model_name).to(device)


def init_diarization_model(device: str) -> Pipeline:
    """
    Init helper class responsible for setting up global whisper model instance – necessary because of how the
    redis queue workers are implemented.
    """
    global DIARIZATION_MODEL
    torch_device = torch.device(device)
    DIARIZATION_MODEL = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=config.HF_TOKEN).to(torch_device)


def _format_to_word_timestamps_json_string(transcription_segments: dict) -> str:
    word_timings = []
    for segment in transcription_segments:
        for word_info in segment["words"]:
            word_timings.append(
                {"word": word_info["word"], "start": f"{word_info['start']:.2f}", "end": f"{word_info['end']:.2f}"}
            )
    word_timings_str = json.dumps(word_timings, indent=4)
    return word_timings_str


def _format_to_diarized_transcription_json_string(transcription_segments: dict, include_word_timestamps: bool) -> str:
    transcript = []
    for seg, spk, sent in transcription_segments:
        if include_word_timestamps:
            line = {"start": seg.start, "end": seg.end, "person": spk, "transcript": sent}
        else:
            line = {"person": spk, "transcript": sent}
        transcript.append(line)
    transcript_string = json.dumps(transcript, indent=4)
    return transcript_string


def _transcribe_audio(path: Path, include_word_timestamps: bool, diarize_speakers: bool) -> str:
    global TRANSCRIPTION_MODEL
    result = TRANSCRIPTION_MODEL.transcribe(str(path), word_timestamps=include_word_timestamps)
    if diarize_speakers:
        diarization_result = DIARIZATION_MODEL(str(path))
        merge_results = diarize_text(result, diarization_result)
        diarization_string = _format_to_diarized_transcription_json_string(merge_results, include_word_timestamps)
        return diarization_string
    if include_word_timestamps:
        word_timings_str = _format_to_word_timestamps_json_string(result["segments"])
        return word_timings_str
    else:
        return result["text"]


def transcribe_audio_task(reference_id: str, include_word_timestamps: bool = False, diarize_speakers: bool = False) -> None:
    """
    Transcribe an audio file with the given reference ID. The transcription result will be saved to a file in the
    configured transcriptions directory.

    Args:
        reference_id (str): The reference ID of the audio file.
        include_word_timestamps (bool): Whether to include word timestamps in the transcription (rich/extended
        format) Defaults to False to ensure backwards compatibility.
    """
    audio_path = config.UPLOADS_DIR / f"{reference_id}"
    results = _transcribe_audio(audio_path, include_word_timestamps, diarize_speakers)

    # Save transcription
    with open(config.TRANSCRIPTIONS_DIR / f"{reference_id}.txt", "w", encoding="utf-8") as f:
        f.write(results)


def _extract_audio_from_video(video_path: Path, audio_path: Path) -> None:
    stream = ffmpeg.input(str(video_path))
    stream = ffmpeg.output(stream, filename=str(audio_path), acodec="pcm_s16le", ac=1, ar="16k")
    ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
    # It raises an exception if the command fails / returns non-zero internally.


def transcribe_video_task(reference_id: str, include_word_timestamps: bool = False, diarize_speakers: bool = False) -> None:
    """
    Transcribe a video file with the given reference ID. The transcription result will be saved to a file in the
    configured transcriptions directory.

    Args:
        reference_id (str): The reference ID of the video file.
        include_word_timestamps (bool): Whether to include word timestamps in the transcription (rich/extended
        format) Defaults to False to ensure backwards compatibility.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        video_path = config.UPLOADS_DIR / f"{reference_id}"
        temp_audio_path = Path(temp_dir) / "audio.wav"
        _extract_audio_from_video(video_path, temp_audio_path)
        results = _transcribe_audio(temp_audio_path, include_word_timestamps, diarize_speakers)

        # Save transcription
        with open(config.TRANSCRIPTIONS_DIR / f"{reference_id}.txt", "w", encoding="utf-8") as f:
            f.write(results)
