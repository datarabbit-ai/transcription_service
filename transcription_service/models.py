from enum import Enum
from typing import List, Optional

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


class ListTranscriptionStatusesPaginatedResponse(BaseModel):
    items: List[TranscriptionStatus]
    total: int
    page: int
    size: int


class HealthCheckResponse(BaseModel):
    redis_is_healthy: bool
    web_app_is_healthy: bool
    at_least_one_worker_is_healthy: bool
