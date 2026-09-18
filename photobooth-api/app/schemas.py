from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class EventCreate(BaseModel):
    client_name: str
    event_type: str
    event_date: date


class EventCreateResponse(BaseModel):
    event_id: UUID


class EventDetailResponse(BaseModel):
    event_id: UUID
    client_name: str
    event_type: str
    event_date: date
    created_at: datetime
    photo_count: int


class UploadResponse(BaseModel):
    photo_id: UUID
    polaroid_key: str
