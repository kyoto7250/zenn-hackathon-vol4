import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from kubernetes import client, watch
from app.services.k8s_client import get_k8s_client
import json
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)


def infer_component(event_reason: str, event_obj: dict) -> str:
    """
    Infer the component (Source) based on event reason and involved object.
    """
    if event_reason == "Scheduled":
        return "Scheduler"
    if event_reason in ["SuccessfulCreate", "Created", "ScalingReplicaSet"]:
        return "API Server"
    if event_reason in [
        "Pulled",
        "Pulling",
        "Created",
        "Started",
        "Killing",
        "BackOff",
    ]:
        # Created can be both, but for Pods usually Kubelet
        if event_obj.get("kind") == "Pod":
            return "Kubelet"
        return "Controller"
    if event_reason == "TriggeredScaleUp":
        return "Autoscaler"

    return "Kubernetes"


@router.websocket("/events")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    v1 = get_k8s_client()
    resource_version = None

    try:
        while True:
            # Poll for events
            # We run this in a thread to avoid blocking the async loop

            func = v1.list_event_for_all_namespaces
            kwargs = {"timeout_seconds": 5}
            if resource_version:
                kwargs["resource_version"] = resource_version

            # Run blocking call in thread
            ret = await asyncio.to_thread(func, **kwargs)

            if ret.metadata.resource_version:
                resource_version = ret.metadata.resource_version

            for event in ret.items:
                # Transform k8s event to our SimulationEvent format

                # Use last_timestamp or event_time
                ts = event.last_timestamp or event.event_time or event.first_timestamp
                if ts:
                    ts_str = ts.isoformat()
                else:
                    ts_str = datetime.now().isoformat()

                involved_obj = {
                    "kind": event.involved_object.kind,
                    "name": event.involved_object.name,
                    "namespace": event.involved_object.namespace,
                    "uid": event.involved_object.uid,
                }

                source_component = infer_component(event.reason, involved_obj)

                # Create a concise message
                message = event.message
                if not message:
                    message = (
                        f"{event.reason} {involved_obj['kind']}/{involved_obj['name']}"
                    )

                payload = {
                    "type": "BIO_EVENT",
                    "event": {
                        "kind": event.reason,  # e.g. Scheduled, Created, Started
                        "component": source_component,  # e.g. Scheduler, Kubelet
                        "message": message,
                        "timestamp": ts_str,
                        "object": involved_obj,
                    },
                }

                await websocket.send_json(payload)

            # Sleep a bit to avoid busy loop if timeout doesn't work as expected
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass
