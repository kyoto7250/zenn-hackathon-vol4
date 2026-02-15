from fastapi import APIRouter, HTTPException, Depends
from app.services.k8s_client import get_k8s_client
from kubernetes import client

router = APIRouter()


@router.delete("/pods/{namespace}/{name}")
async def delete_pod(name: str, namespace: str = "default"):
    # Delete pod from Kubernetes cluster
    v1 = get_k8s_client()
    try:
        # Grace period 0 for immediate deletion
        v1.delete_namespaced_pod(name, namespace, grace_period_seconds=0)
        return {"status": "deleted", "name": name, "namespace": namespace}
    except client.exceptions.ApiException as e:
        if e.status == 404:
            raise HTTPException(status_code=404, detail="Pod not found")
        raise HTTPException(status_code=500, detail=str(e))
