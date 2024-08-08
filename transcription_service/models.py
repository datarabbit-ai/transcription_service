from enum import Enum
from typing import Optional

from pydantic import BaseModel


class MediaType(str, Enum):
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    OTHER = "OTHER"


class UploadResponse(BaseModel):
    reference_id: str


class TranscriptionStatusEnum(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class TranscriptionStatus(BaseModel):
    reference_id: str
    status: TranscriptionStatusEnum
    error_message: Optional[str]
