from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.config import settings
from app.models import Scenario
from app.schemas import ScenarioResponse, DiagramRetryRequest
from app.services.gen_scenario import regenerate_diagram

router = APIRouter()


@router.get("/{id}", response_model=ScenarioResponse)
async def get_scenario(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Scenario).filter(Scenario.id == id))
    scenario = result.scalars().first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.get("/", response_model=list[ScenarioResponse])
async def list_scenarios(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Scenario).offset(skip).limit(limit))
    scenarios = result.scalars().all()
    return scenarios


from app.schemas import EventCreate


@router.post("/{id}/events", response_model=ScenarioResponse)
async def add_scenario_event(
    id: str, event: EventCreate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Scenario).filter(Scenario.id == id))
    scenario = result.scalars().first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Append event to events_json
    # Note: mutating the JSON field directly might not trigger sqlalchemy update if not flagged
    current_events = scenario.events_json.get("events", [])
    current_events.append(event.model_dump())

    # Create a new dictionary to ensure sqlalchemy detects the change
    scenario.events_json = {**scenario.events_json, "events": current_events}

    await db.commit()
    await db.refresh(scenario)
    return scenario


@router.post("/{id}/diagram/retry", response_model=ScenarioResponse)
async def retry_scenario_diagram(
    id: str, payload: DiagramRetryRequest, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Scenario).filter(Scenario.id == id))
    scenario = result.scalars().first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set")

    current_mermaid = payload.mermaid or scenario.topology_json.get("mermaid", "")
    current_events = scenario.events_json.get("events", [])
    user_instruction = payload.instruction.strip()
    if not user_instruction:
        raise HTTPException(status_code=422, detail="instruction is required")

    render_error = payload.render_error or "Mermaid render failed on frontend."
    combined_instruction = (
        f"{user_instruction}\n\n"
        f"Frontend render error:\n{render_error}\n\n"
        "Please fix Mermaid syntax and regenerate while preserving scenario intent."
    )

    regenerated = regenerate_diagram(
        settings.GEMINI_API_KEY,
        scenario.yaml_content or "",
        current_mermaid,
        current_events,
        combined_instruction,
    )

    scenario.topology_json = {
        **scenario.topology_json,
        "mermaid": regenerated.get("mermaid", current_mermaid),
    }
    scenario.events_json = {
        **scenario.events_json,
        "events": regenerated.get("events", current_events),
    }

    await db.commit()
    await db.refresh(scenario)
    return scenario
