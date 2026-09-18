import uuid

from sqlalchemy import Column, DateTime, String

from app.database.base import Base
from app.utils.time import utcnow_naive


class User(Base):
    """Persistent application user used for registration and JWT login."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow_naive, nullable=False)
