from sqlalchemy import Column, String, Float, Boolean, DateTime
import uuid
from datetime import datetime, timezone
from app.database.base import Base

class ModelRegistry(Base):
    __tablename__ = "models"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True, nullable=False)
    provider = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Capabilities and pricing
    cost_per_1k_tokens = Column(Float, default=0.0)
    supports_streaming = Column(Boolean, default=False)
    supports_vision = Column(Boolean, default=False)
    supports_tools = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
