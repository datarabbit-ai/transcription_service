from pydantic import BaseModel


class UploadResponse(BaseModel):
    reference_id: str
