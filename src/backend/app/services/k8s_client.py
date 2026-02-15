from kubernetes import client
from app.core.config import settings


def get_k8s_client() -> client.CoreV1Api:
    """
    Returns a configured Kubernetes CoreV1Api client.
    """
    configuration = client.Configuration()
    configuration.host = settings.KUBERNETES_HOST
    # For standard k8s clients, you may need SSL/token options depending on cluster setup.

    api_client = client.ApiClient(configuration)
    return client.CoreV1Api(api_client)


def get_k8s_apps_client() -> client.AppsV1Api:
    """
    Returns a configured Kubernetes AppsV1Api client.
    """
    configuration = client.Configuration()
    configuration.host = settings.KUBERNETES_HOST
    api_client = client.ApiClient(configuration)
    return client.AppsV1Api(api_client)
