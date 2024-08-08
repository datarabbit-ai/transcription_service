from enum import Enum

from pydantic import BaseModel


class MediaType(str, Enum):
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    OTHER = "OTHER"


class UploadResponse(BaseModel):
    reference_id: str
