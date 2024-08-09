import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from redis import Redis
from rq.job import Job

from transcription_service import config
from transcription_service.models import (
    ListTranscriptionStatusesPaginatedResponse,
    MediaType,
    TranscriptionStatus,
    TranscriptionStatusEnum,
    UploadResponse,
)
from transcription_service.transcription import determine_media_type, transcribe_audio_task, transcribe_video_task

api_router = APIRouter()


@api_router.post("/upload", response_model=UploadResponse)
def upload(request: Request, file: UploadFile = File(...)):
    """
    Upload a file for transcription.
    """
    # Important: can't be async.
    timestamp = datetime.now().astimezone().replace(microsecond=0).isoformat()
    filename = Path(file.filename).name
    reference_id = f"{timestamp}_{filename}"

    media_type = determine_media_type(config.UPLOADS_DIR / filename)
    if media_type == MediaType.OTHER:
        raise HTTPException(
            status_code=415, detail="Unsupported media type. Only " "limited audio and video formats are supported."
        )
    # TODO: also possibly ad a check for the file size here / configurable max size.

    try:
        with open(config.UPLOADS_DIR / reference_id, "wb") as f:
            # We utilize shutil.copyfileobj from stdlib as it handles the chunking of larger files underneath.
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error uploading the file.")
    finally:
        file.file.close()

    if media_type == MediaType.VIDEO:
        job_type = transcribe_video_task
    elif media_type == MediaType.AUDIO:
        job_type = transcribe_audio_task
    # Else shouldn't ever happen as we handle the OTHER type earlier/before with different error code.

    # Create a job with a custom ID – otherwise, RQ will generate a random one that won't match the reference ID
    # TTLs are set to -1 to prevent the job from being removed from the queue after processing as we use them
    # for listing
    request.app.state.queue.enqueue(job_type, reference_id, job_id=reference_id, result_ttl=-1, failure_ttl=-1)

    return {"reference_id": reference_id}


def _get_job_status_and_error_message(reference_id: str, redis_conn: Redis) -> Tuple[TranscriptionStatusEnum, Optional[str]]:
    # Check the transcription job status
    job = Job.fetch(reference_id, connection=redis_conn)
    if job.is_queued:
        status = TranscriptionStatusEnum.QUEUED
        message = None
    elif job.is_started:
        status = TranscriptionStatusEnum.PROCESSING
        message = None
    elif job.is_finished:
        status = TranscriptionStatusEnum.COMPLETED
        message = None
    elif job.is_failed:
        status = TranscriptionStatusEnum.FAILED
        message = job.exc_info
    else:
        status = TranscriptionStatusEnum.UNKNOWN
        message = None

    return status, message


@api_router.get("/list", response_model=ListTranscriptionStatusesPaginatedResponse)
def list_transcriptions(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order by file creation time."),
):
    """
    Get a paginated list of all files to transcribe and their transcription status.
    """
    transcription_statuses = []

    # List all files for transcription in the upload directory
    reference_ids = sorted(
        (path.name for path in config.UPLOADS_DIR.iterdir()),
        key=lambda x: (config.UPLOADS_DIR / x).stat().st_ctime,
        reverse=sort_order == "desc",
    )
    total = len(reference_ids)

    # Calculate start and end indices for the current page
    start = (page - 1) * size
    end = start + size

    # Get only the transcriptions for the current page
    reference_ids = reference_ids[start:end]

    for reference_id in reference_ids:
        status, error_message = _get_job_status_and_error_message(reference_id, request.app.state.redis_conn)
        transcription_statuses.append(
            TranscriptionStatus(reference_id=reference_id, status=status, error_message=error_message)
        )

    return ListTranscriptionStatusesPaginatedResponse(items=transcription_statuses, total=total, page=page, size=size)


@api_router.get("/status/{reference_id}", response_model=TranscriptionStatus)
async def get_status(request: Request, reference_id: str):
    """
    Get the transcription status for a specific file.
    """
    if reference_id not in (path.name for path in config.UPLOADS_DIR.iterdir()):
        raise HTTPException(status_code=404, detail="Reference not found.")
    status, error_message = _get_job_status_and_error_message(reference_id, request.app.state.redis_conn)
    return TranscriptionStatus(reference_id=reference_id, status=status, error_message=error_message)
