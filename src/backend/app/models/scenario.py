from sqlalchemy import Column, String, Text, DateTime, JSON
from app.core.database import Base
import uuid
from datetime import datetime


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    topology_json = Column(JSON, nullable=False)
    events_json = Column(JSON, nullable=False)
    yaml_content = Column(Text, nullable=True)
    schema_version = Column(String(10), nullable=False, default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
