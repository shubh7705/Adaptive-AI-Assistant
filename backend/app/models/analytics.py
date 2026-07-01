from sqlalchemy import Column, String, Float, Boolean, Integer, ForeignKey, DateTime
import uuid
from datetime import datetime, timezone
from app.database.base import Base

class RoutingLog(Base):
    __tablename__ = "routing_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True)
    model_id = Column(String, ForeignKey("models.id", ondelete="SET NULL"), nullable=True)
    
    intent_detected = Column(String, nullable=True)
    complexity_score = Column(String, nullable=True) # e.g. "low", "medium", "high"
    
    latency_ms = Column(Float, default=0.0)
    total_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    
    cache_hit = Column(Boolean, default=False)
    is_fallback = Column(Boolean, default=False)
    
    # Store the evaluation score if applicable
    evaluation_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Benchmark(Base):
    __tablename__ = "benchmarks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    
    avg_latency_ms = Column(Float, default=0.0)
    success_rate = Column(Float, default=1.0)
    avg_quality_score = Column(Float, default=0.0)
    
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
