from sqlalchemy import String, Column, DateTime, ForeignKey
from db import Base
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class Like(Base):
    __tablename__ = "likes"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)

    moment_id = Column(UUID(as_uuid=True), ForeignKey("moments.id"), primary_key=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    moment = relationship("Moment", back_populates="likes")