from sqlalchemy import Column, String, ForeignKey, DateTime, Text, Table, Enum as sqlEnum
import enum
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base
import uuid
from enum import Enum as pyEnum
from sqlalchemy.dialects.postgresql import UUID

class MomentType(str, pyEnum):
    text = "text"
    image = "image"
    video = "video"

class Moment(Base):
    __tablename__ = "moments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    type = Column(sqlEnum(MomentType), nullable=False, default=MomentType.text)

    content = Column(Text, nullable=False)
    media_url = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    event = relationship("Event", back_populates="moments")
    user = relationship("User", back_populates="moments")

    likes = relationship("Like", back_populates="moment")
    comments = relationship("Comment", back_populates="moment")