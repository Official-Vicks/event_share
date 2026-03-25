from sqlalchemy import String, Column, DateTime, ForeignKey
from db import Base
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID
from typing import Text
from sqlalchemy.orm import relationship

class Follow(Base):
    __tablename__ = "follows"

    follower_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    following_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    following = relationship("User", foreign_keys=[following_id], back_populates="followers")