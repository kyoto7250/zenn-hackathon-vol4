from fastapi import APIRouter
from app.api.v1.endpoints import session, scenario

api_router = APIRouter()
api_router.include_router(session.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(scenario.router, prefix="/scenarios", tags=["scenarios"])
from app.api.v1.endpoints import stream, k8s

api_router.include_router(stream.router, prefix="/stream", tags=["stream"])
api_router.include_router(k8s.router, prefix="/k8s", tags=["k8s"])
