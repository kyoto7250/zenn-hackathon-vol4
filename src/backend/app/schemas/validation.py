import json
import os
from typing import Dict, Any
from jsonschema import validate, ValidationError
from fastapi import HTTPException

# Load schemas
SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "json_schemas")


def load_schema(filename: str) -> Dict[str, Any]:
    with open(os.path.join(SCHEMA_DIR, filename), "r") as f:
        return json.load(f)


TOPOLOGY_SCHEMA = load_schema("topology.schema.json")
EVENTS_SCHEMA = load_schema("events.schema.json")


def validate_topology(data: Dict[str, Any]):
    try:
        validate(instance=data, schema=TOPOLOGY_SCHEMA)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Invalid topology: {e.message}")


def validate_events(data: Dict[str, Any]):
    try:
        validate(instance=data, schema=EVENTS_SCHEMA)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Invalid events: {e.message}")
