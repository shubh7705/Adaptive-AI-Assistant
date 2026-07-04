from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer
import uuid
from datetime import datetime, timezone
from app.database.base import Base

def utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)

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
    supports_function_calling = Column(Boolean, default=False)
    supports_json_mode = Column(Boolean, default=False)
    
    context_window = Column(Integer, default=8192)
    max_output_tokens = Column(Integer, default=4096)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=utcnow_naive)
    updated_at = Column(DateTime, default=utcnow_naive, onupdate=utcnow_naive)
