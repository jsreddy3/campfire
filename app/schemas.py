from typing import List, Optional, Union, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class AudioSegmentBase(BaseModel):
    filename: str
    duration: float   # seconds
    order: int
    s3_key: str

class AudioSegmentCreate(AudioSegmentBase):
    segment_id: Union[UUID, str]

class AudioSegmentRead(AudioSegmentBase):
    segment_id: Union[UUID, str] = Field(alias="id")
    transcript: Optional[str] = None

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(timespec="seconds") + "Z",
            UUID: lambda v: str(v)
        }

class DreamBase(BaseModel):
    title: str

class DreamCreate(DreamBase):
    id: UUID | None = None          # accept optional id from client
    title: str

class DreamUpdate(DreamBase):
    pass

class DreamRead(DreamBase):
    id: Union[UUID, str]
    created: datetime
    transcript: Optional[str] = None
    state: str
    segments: List[AudioSegmentRead] = []
    video_s3_key: Optional[str] = None
    video_metadata: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(timespec="seconds") + "Z",
            UUID: lambda v: str(v)
        }

class TranscriptRead(BaseModel):
    transcript: str