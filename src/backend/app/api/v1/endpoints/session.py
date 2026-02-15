from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models import Session, Message, Scenario
from app.schemas import (
    SessionCreate,
    SessionResponse,
    MessageCreate,
    ChatResponse,
    MessageResponse,
)
from app.services.gen_scenario import generate_mock_scenario
import uuid

router = APIRouter()


@router.post("/", response_model=SessionResponse)
async def create_session(session_in: SessionCreate, db: AsyncSession = Depends(get_db)):
    db_session = Session(title=session_in.title)
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session


@router.post("/{session_id}/messages", response_model=ChatResponse)
async def create_message(
    session_id: str, message_in: MessageCreate, db: AsyncSession = Depends(get_db)
):
    # Verify session exists
    result = await db.execute(select(Session).filter(Session.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 1. Save user message
    user_message = Message(
        session_id=session_id, role="user", content=message_in.content
    )
    db.add(user_message)

    # 2. Generate Scenario (Mock)
    # In real impl, this would be async or background task
    scenario_data = generate_mock_scenario(message_in.content)

    # 3. Save Scenario
    scenario = Scenario(
        name=scenario_data.name,
        description=scenario_data.description,
        topology_json=scenario_data.topology_json,
        events_json=scenario_data.events_json,
        yaml_content=scenario_data.yaml_content,
        schema_version=scenario_data.schema_version,
    )
    db.add(scenario)
    await db.flush()  # to get ID

    # 4. Save Assistant Message
    assistant_content = (
        f"I've generated a scenario for you based on '{message_in.content}'."
    )
    assistant_message = Message(
        session_id=session_id, role="assistant", content=assistant_content
    )
    db.add(assistant_message)

    await db.commit()
    await db.refresh(assistant_message)

    return ChatResponse(
        message=MessageResponse.model_validate(assistant_message),
        scenario_id=scenario.id,
    )
