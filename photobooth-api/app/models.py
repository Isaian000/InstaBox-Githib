import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_name = Column(String(200), nullable=False)
    event_type = Column(String(100), nullable=False)
    event_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    photos = relationship("Photo", back_populates="event", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    original_key = Column(String(500), nullable=True)  # se limpia (NULL) al hacer /finish
    polaroid_key = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="photos")
