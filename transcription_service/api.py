import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import ffmpeg
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from rq.job import Job

from transcription_service import config
from transcription_service.models import UploadResponse

api_router = APIRouter()


@api_router.post("/upload", response_model=UploadResponse)
def upload(file: UploadFile = File(...)):
    # Important: can't be async.
    timestamp = datetime.now().astimezone().replace(microsecond=0).isoformat()
    filename = Path(file.filename).name
    reference_id = f"{timestamp}_{filename}"

    # TODO: validate file format/type? (extension at least)
    try:
        with open(config.UPLOADS_DIR / filename, "wb") as f:
            # We utilize shutil.copyfileobj from stdlib as it handles the chunking of larger files underneath.
            shutil.copyfileobj(file.file, f)
            # TODO: redis enqueue
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error uploading the file")
    finally:
        file.file.close()

    return {"reference_id": reference_id}
