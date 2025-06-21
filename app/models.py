import enum, uuid
from datetime import datetime
from sqlalchemy import Column, Enum, DateTime, String, Text, Float, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base

class DreamState(str, enum.Enum):
    draft = "draft"
    completed = "completed"
    video_generated = "video_generated"

class Dream(Base):
    __tablename__ = "dreams"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created   = Column(DateTime, default=datetime.utcnow, nullable=False)
    title     = Column(String(255), nullable=False)
    transcript= Column(Text)
    state     = Column(Enum(DreamState), default=DreamState.draft, nullable=False)

    segments  = relationship(
        "AudioSegment",
        back_populates="dream",
        cascade="all, delete-orphan",
        order_by="AudioSegment.order",
    )
    

class AudioSegment(Base):
    __tablename__ = "segments"

    id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dream_id = Column(UUID(as_uuid=True), ForeignKey("dreams.id", ondelete="CASCADE"))
    filename = Column(String(255), nullable=True)
    duration = Column(Float, nullable=False)  # seconds
    order    = Column(Integer, nullable=False)
    s3_key   = Column(String(512), nullable=False)
    transcript = Column(Text, nullable=True)

    dream    = relationship("Dream", back_populates="segments")