from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


# Session Schemas
class SessionCreate(BaseModel):
    title: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Message Schemas
class MessageCreate(BaseModel):
    content: str
    role: str = "user"  # user or assistant


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    message: MessageResponse
    scenario_id: Optional[str] = None


# Scenario Schemas
class ScenarioBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    topology_json: Dict[str, Any]
    events_json: Dict[str, Any]
    yaml_content: Optional[str] = None
    schema_version: str = "1.0"


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioResponse(ScenarioBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventCreate(BaseModel):
    t: int
    kind: str
    pod: Optional[str] = None
    node: Optional[str] = None
    resource: Optional[Dict[str, Any]] = None
    component: Optional[str] = None
    message: Optional[str] = None


class DiagramRetryRequest(BaseModel):
    mermaid: Optional[str] = None
    instruction: str
    render_error: Optional[str] = None
