import time
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

import click
import requests
import yt_dlp


def is_youtube_url(url: str) -> bool:
    """Check if a given URL is a YouTube URL."""
    parsed = urlparse(url)
    return parsed.netloc in ["www.youtube.com", "youtube.com", "youtu.be"]


def get_youtube_video_id(url: str) -> Optional[str]:
    """
    Extract the video ID from a YouTube URL.

    Args:
        url (str): The YouTube URL.

    Returns:
        Optional[str]: The video ID if found, None otherwise.
    """
    parsed_url = urlparse(url)
    if parsed_url.netloc == "youtu.be":
        return parsed_url.path[1:]
    if parsed_url.netloc in ("www.youtube.com", "youtube.com"):
        if parsed_url.path == "/watch":
            p = parse_qs(parsed_url.query)
            return p.get("v", [None])[0]
    return None


def download_youtube_video(url: str, output_dir: Path) -> Path:
    """
    Download a YouTube video and convert it to an mp3 file.

    Args:
        url: The URL of the YouTube video.
        output_dir: The directory where the downloaded file will be saved.

    Returns:
        Path: The path to the downloaded mp3 file.
    """
    video_id = get_youtube_video_id(url)
    if not video_id:
        raise ValueError("Could not extract video ID from the URL")

    output_path = output_dir / f"{video_id}.%(ext)s"
    ydl_opts = {
        "outtmpl": str(output_path),
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            }
        ],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_dir / f"{video_id}.mp3"


def upload_file(api_url: str, file_path: Path, data: Optional[dict] = None) -> str:
    """
    Upload a file to the transcription service API.

    Args:
        api_url: The base URL of the API.
        file_path: The path to the file to upload.
        data: Optional metadata to send with the request.

    Returns:
        str: The reference ID from the API.
    """
    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{api_url}/upload", files=files, data=data)

        response.raise_for_status()
        return response.json()["reference_id"]
    except requests.exceptions.RequestException as e:
        raise Exception(f"Upload failed: {e}")


def check_status(api_url: str, reference_id: str) -> Optional[str]:
    """
    Check the status of a transcription request.

    Args:
        api_url: The base URL of the API.
        reference_id: The reference ID of the transcription request.

    Returns:
        Optional[str]: The status of the transcription.
    """
    try:
        response = requests.get(f"{api_url}/status/{reference_id}")
        if response.status_code == 200:
            status = response.json()["status"]
            return status
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to check status: {e}")


def download_transcription(api_url: str, reference_id: str, output_path: Path) -> None:
    """
    Download the transcription result from the API.

    Args:
        api_url: The base URL of the API.
        reference_id: The reference ID of the transcription request.
        output_path: The path where the transcription will be saved.

    Raises:
        Exception: If the download fails.
    """
    try:
        response = requests.get(f"{api_url}/download/{reference_id}")
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

        print(f"Transcription downloaded to {output_path}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Download failed: {e}")


@click.command()
@click.argument("api_url", type=str)
@click.argument("input_source", type=str)
@click.argument("output_path", type=click.Path(dir_okay=False, path_type=Path))
@click.option(
    "--include-word-timestamps",
    is_flag=True,
    help="Return the transcription in rich format, " "including word-level timestamps in the transcription.",
)
def main(api_url: str, input_source: str, output_path: Path, include_word_timestamps: bool) -> None:
    """
    Transcribe a video file or YouTube video using the transcription service API.

    Args:
        api_url: Base URL of the transcription service API.
        input_source: Path to the input video file or YouTube URL.
        output_path: Path to save the transcription result.
        include_word_timestamps: Whether to include word-level timestamps in the transcription.
    """
    youtube_dir = Path.cwd() / "youtube_downloads"
    youtube_dir.mkdir(exist_ok=True)

    if is_youtube_url(input_source):
        print(f"Downloading YouTube video: {input_source}")
        input_file = download_youtube_video(input_source, youtube_dir)
        print(f"Video downloaded and converted to audio: {input_file}")
    else:
        input_file = Path(input_source)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

    print(f"Uploading file: {input_file}")
    data = {"include_word_timestamps": include_word_timestamps}
    reference_id = upload_file(api_url, input_file, data)
    print(f"File uploaded. Reference ID: {reference_id}")

    while True:
        status = check_status(api_url, reference_id)
        print(f"Current status: {status}")

        if status == "COMPLETED":
            break
        elif status in ["FAILED", "UNKNOWN"]:
            raise Exception(f"Transcription failed with status: {status}")

        time.sleep(10)  # Wait for 10 seconds before checking again

    download_transcription(api_url, reference_id, output_path)
    print("Transcription process completed.")


if __name__ == "__main__":
    main()
