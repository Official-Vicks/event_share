from sqlalchemy import String, Column, DateTime, ForeignKey, Enum as sqlEnum
from db import Base
import enum
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    scheduled_at = Column(DateTime, nullable=False, index=True)
    location = Column(String, nullable=True)

    organizer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organizer = relationship("User", back_populates="organized_events")

    banner_url = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Participants
    participants = relationship("EventParticipant", back_populates="event")

    # Moments
    moments = relationship("Moment", back_populates="event")

class ParticipationStatus(str, enum.Enum):
    joined = "joined"
    maybe = "maybe"
    left = "left"


class EventParticipant(Base):
    __tablename__ = "event_participants"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), primary_key=True)

    status = Column(sqlEnum(ParticipationStatus), default=ParticipationStatus.joined)

    joined_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="event_participation")
    event = relationship("Event", back_populates="participants")