from sqlalchemy import String, Column, DateTime, ForeignKey
from db import Base
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID
from typing import Text
from sqlalchemy.orm import relationship

class Comment(Base):
    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    moment_id = Column(UUID(as_uuid=True), ForeignKey("moments.id"), nullable=False)

    content = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    moment = relationship("Moment", back_populates="comments")