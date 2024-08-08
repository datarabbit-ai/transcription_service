import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from transcription_service import config
from transcription_service.models import MediaType, UploadResponse
from transcription_service.transcription import determine_media_type, transcribe_audio, transcribe_video

api_router = APIRouter()


@api_router.post("/upload", response_model=UploadResponse)
def upload(request: Request, file: UploadFile = File(...)):
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
        job_type = transcribe_video
    elif media_type == MediaType.AUDIO:
        job_type = transcribe_audio
    # Else shouldn't ever happen as we handle the OTHER type earlier/before with different error code.

    request.app.state.queue.enqueue(job_type, reference_id)

    return {"reference_id": reference_id}
