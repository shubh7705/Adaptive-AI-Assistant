from sqlalchemy import Column, String, Float, Boolean, Integer, ForeignKey, DateTime
import uuid
from datetime import datetime, timezone
from app.database.base import Base

def utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)

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
    
    created_at = Column(DateTime, default=utcnow_naive)

class ModelBenchmarks(Base):
    __tablename__ = "model_benchmarks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String, ForeignKey("models.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    coding_score = Column(Float, default=5.0)
    reasoning_score = Column(Float, default=5.0)
    math_score = Column(Float, default=5.0)
    vision_score = Column(Float, default=0.0)
    creative_score = Column(Float, default=5.0)
    tool_score = Column(Float, default=0.0)
    
    arena_score = Column(Float, default=1000.0)
    mmlu_score = Column(Float, default=50.0)
    humaneval_score = Column(Float, default=30.0)
    
    recorded_at = Column(DateTime, default=utcnow_naive)

class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String, ForeignKey("models.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    average_latency_ms = Column(Float, default=0.0)
    requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    error_rate = Column(Float, default=0.0)
    success_rate = Column(Float, default=1.0)
    average_tokens_per_sec = Column(Float, default=0.0)
    current_active_requests = Column(Integer, default=0)
    
    last_updated = Column(DateTime, default=utcnow_naive, onupdate=utcnow_naive)
