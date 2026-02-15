from app.schemas import ScenarioCreate
import uuid
import json
import requests
import yaml
import re
from app.core.config import settings
from app.services.k8s_client import get_k8s_client
from kubernetes import client, utils
import os
from typing import Dict, Any

# API Endpoint
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


def review_yaml(api_key: str, yaml_content: str, user_request: str) -> Dict[str, Any]:
    """
    YAMLの妥当性をレビュー
    Returns: {"approved": bool, "instruction": str}
    """
    prompt_review = f"""
    Role: Kubernetes YAML Reviewer.

    Task:
    Review the following Kubernetes YAML manifest for correctness and compatibility with Kubernetes.
    User Request: "{user_request}"

    YAML to Review:
    {yaml_content}

    Validation Criteria:
    1. Valid YAML syntax
    2. Required fields present (apiVersion, kind, metadata.name)
    3. Resource types compatible with Kubernetes
    4. Logical consistency (e.g., Service selectors match Pod labels)

    Output Format (JSON):
    {{
        "approved": true/false,
        "instruction": "If not approved, provide specific instructions for fixing (in Japanese)"
    }}

    """

    try:
        response = requests.post(
            f"{GEMINI_URL}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt_review}]}],
                "generationConfig": {"response_mime_type": "application/json"},
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        result_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(result_text)
    except Exception as e:
        print(f"Review failed: {e}")
        return {"approved": True, "instruction": ""}


def regenerate_yaml(
    api_key: str, user_request: str, previous_yaml: str, instruction: str
) -> Dict[str, str]:
    """
    やり直し指示に基づいてYAMLとdescriptionを再生成
    Returns: {"yaml": str, "description": str}
    """
    prompt_regenerate = f"""
    Role: Kubernetes YAML Generator.

    Task:
    Regenerate the Kubernetes YAML based on the following feedback.

    Original User Request: "{user_request}"

    Previous YAML:
    {previous_yaml}

    Feedback/Instruction:
    {instruction}

    Important:
    Also regenerate the detailed explanation in Japanese that includes:
    - Summary of what the user requested
    - List of ALL generated YAML resources with their specific names and purposes
    - Detailed explanation of how these resources interact and communicate (including ports)
    - Step-by-step Reconcile Flow describing controller actions
    - CRITICAL: Use plain text only. NO Markdown formatting (no **, -, #, etc.)
    - Use newlines and indentation for readability

    Output Format (JSON):
    {{
        "yaml": "Corrected multi-document YAML string (separated by ---)",
        "description": "日本語での詳細な解説（プレーンテキストのみ、Markdown不可、改行使用可）..."
    }}
    """

    try:
        response = requests.post(
            f"{GEMINI_URL}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt_regenerate}]}],
                "generationConfig": {"response_mime_type": "application/json"},
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        result_text = data["candidates"][0]["content"]["parts"][0]["text"]
        result_data = json.loads(result_text)
        return {
            "yaml": result_data.get("yaml", ""),
            "description": result_data.get("description", ""),
        }
    except Exception as e:
        print(f"Regeneration failed: {e}")
        return {"yaml": "", "description": ""}


def _normalize_mermaid(mermaid_text: str) -> str:
    cleaned = (mermaid_text or "").strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    if not cleaned:
        return "flowchart TD\n  A[No diagram generated]"
    lines = cleaned.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("flowchart "):
            lines[i] = re.sub(r"\b(LR|RL|BT)\b", "TB", line, count=1)
            break
    cleaned = "\n".join(lines).strip()
    return cleaned


def review_diagram(
    api_key: str, yaml_content: str, mermaid: str, events: list
) -> Dict[str, Any]:
    """
    Diagramの妥当性をレビュー
    Returns: {"approved": bool, "instruction": str}
    """
    prompt_review = f"""
    Role: Mermaid Diagram Reviewer for Kubernetes.

    Task:
    Review the generated Mermaid diagram for correctness and consistency.

    Input YAML:
    {yaml_content}

    Generated Mermaid:
    {mermaid}

    Events: {json.dumps(events, ensure_ascii=False)}

    Validation Criteria:
    1. Mermaid syntax must be valid and renderable.
    1.0 CRITICAL: Perform strict grammar validation:
       - No parse error such as "Syntax error in text"
       - Brackets/quotes/subgraph blocks must be balanced
       - Edge-ID animation syntax (e.g., r1@--> and r1@{{ animation: fast }}) must be valid
       - classDef/class/style declarations must be syntactically valid
    1.1 Diagram direction must be TB or TD (avoid LR/RL) for square-friendly readability.
    2. Mandatory control plane nodes must be present:
       - User
       - API Server
       - Controller Manager
       - Scheduler
       - etcd
    3. Each worker node must have a kubelet node.
    4. Flows must represent logical Kubernetes control flow.
    5. The diagram MUST clearly use frame/group boundaries (subgraph) for:
       - One Kubernetes Cluster (single cluster only)
       - Control Plane
       - Node units
       - kubelet units inside node group(s)
    5.1 CRITICAL: Deployment, Service, and ReplicaSet nodes must be inside the Control Plane frame.
    5. CRITICAL: Deployment/ReplicaSet/Pod relationships must be properly connected:
       - Deployment nodes must be connected to ReplicaSet nodes
       - ReplicaSet nodes must be connected to Pod nodes
       - Controller Manager must be connected to Deployments and ReplicaSets
       - No Deployment, ReplicaSet, or Pod should be isolated/orphaned
    6. CRITICAL: Kubernetes resource ownership and control flow must be accurate:
       - User creates resources via API Server
       - API Server stores/reads cluster state via etcd
       - Controller Manager watches and reconciles Deployments/ReplicaSets
       - Scheduler assigns Pods to nodes
       - Each kubelet watches API Server
       - Kubelet manages Pods on each node
    7. CRITICAL: Edge labels MUST include port information (e.g., "HTTP:8080", "TCP:5432", "gRPC:50051")
    8. Port information should be specific and accurate based on the YAML resources
    8.1 CRITICAL: Animated arrows must be included using edge IDs.
       Example:
       - r1@---->|Request| api
       - r1@{{ animation: fast }}
    8.2 CRITICAL: Readable color styling must be included using classDef/class or style directives.
    9. Events must be valid Kubernetes events with Japanese messages.
    10. Diagram must accurately reflect the resources in the YAML.
    11. Do NOT include multiple clusters. Assume exactly one cluster.

    Output Format (JSON):
    {{
        "approved": true/false,
        "instruction": "If not approved, provide specific instructions for fixing (in Japanese)"
    }}

    Decision Rule:
    If Mermaid grammar/syntax is broken, "approved" must be false.
    """

    try:
        response = requests.post(
            f"{GEMINI_URL}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt_review}]}],
                "generationConfig": {"response_mime_type": "application/json"},
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        result_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(result_text)
    except Exception as e:
        print(f"Diagram review failed: {e}")
        return {"approved": True, "instruction": ""}


def regenerate_diagram(
    api_key: str,
    yaml_content: str,
    previous_mermaid: str,
    previous_events: list,
    instruction: str,
) -> Dict[str, Any]:
    """
    やり直し指示に基づいてDiagramを再生成
    Returns: {"mermaid": str, "events": list}
    """
    prompt_regenerate = f"""
    Role: Mermaid Diagram generator for Kubernetes.

    Task:
    Regenerate the network topology diagram based on the following feedback.

    Input YAML:
    {yaml_content}

    Previous Mermaid:
    {previous_mermaid}

    Events: {json.dumps(previous_events, ensure_ascii=False)}

    Feedback/Instruction:
    {instruction}

    Rules:
    1. Use Mermaid flowchart syntax and generate one full diagram string.
       - Use `flowchart TB` or `flowchart TD` (avoid LR/RL).
    2. Structure (CRITICAL):
       - Assume exactly ONE Kubernetes cluster. Do NOT create multiple clusters.
       - Use subgraph frame for Cluster.
       - Use subgraph frame for Control Plane inside Cluster.
       - Use subgraph frame(s) for each Node.
       - Place each kubelet clearly inside its corresponding Node frame.
       - Include all required resources in correct groups.
       - Control Plane must include: API Server, Controller Manager, Scheduler, etcd.
       - Deployment, Service, and ReplicaSet must be drawn inside the Control Plane frame.
    3. Connections (CRITICAL - All resources must be connected):
       - User Flow:
         * User -> API Server (Create/Update requests)
       - Control Plane Flow:
         * API Server -> Controller Manager (Watch resources)
         * Controller Manager -> API Server (Create/Update ReplicaSets, reconcile state)
         * API Server -> Scheduler (Watch unscheduled Pods)
         * Scheduler -> API Server (Bind Pods to nodes)
         * API Server <-> etcd (Read/Write cluster state)
       - Resource Ownership (Parent-Child relationships):
         * Deployment -> ReplicaSet (Owns, label: "Manages")
         * ReplicaSet -> Pod (Owns, label: "Manages")
       - Node & Pod Management:
         * kubelet -> API Server (Watch resources)
         * Scheduler -> kubelet (Assign Pod, for each node)
         * kubelet -> Pod (Manage, for each Pod on that node)
       - Application Flow:
         * Service -> Pod (Route traffic, with port info)
         * Pod -> Pod or External (Application connections, with port info)
       - CRITICAL: Edge labels MUST include port information and protocol when applicable.
       - Examples: "HTTP:8080", "TCP:5432", "gRPC:50051", "HTTPS:443", "API:6443"
       - For Service connections, specify the Service port and target port.
       - For Pod-to-Pod connections, specify the container port.
    4. Events:
       - Generate a list of likely Kubernetes events (Normal/Warning).
       - Event messages MUST be in Japanese.
    5. Visual requirements (CRITICAL):
       - Add animated arrows with edge IDs.
         Example:
           r1@---->|Request| api
           r2@---->|Response| user
           r1@{{ animation: fast }}
           r2@{{ animation: slow }}
       - Add readable colors using classDef/class or style directives.
       - Keep the composition square-friendly and avoid very wide layouts.

    Output Format (JSON):
    {{
        "mermaid": "Mermaid flowchart text",
        "events": [ {{"kind": "Pod", "name": "...", "message": "日本語メッセージ..."}} ]
    }}
    """

    try:
        response = requests.post(
            f"{GEMINI_URL}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt_regenerate}]}],
                "generationConfig": {"response_mime_type": "application/json"},
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        result_text = data["candidates"][0]["content"]["parts"][0]["text"]
        result_data = json.loads(result_text)
        return {
            "mermaid": _normalize_mermaid(result_data.get("mermaid", "")),
            "events": result_data.get("events", []),
        }
    except Exception as e:
        print(f"Diagram regeneration failed: {e}")
        return {
            "mermaid": "flowchart TD\n  A[Diagram regeneration failed]",
            "events": [],
        }


def generate_mock_scenario(user_content: str) -> ScenarioCreate:
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")

    # --- Step 1: Generate YAML and Description ---
    prompt_yaml = f"""
    Role: Kubernetes Expert & Simulation Scripter.

    Task:
    1. Analyze the user request: "{user_content}"
    2. Generate valid Kubernetes YAML manifests to implement this scenario.
       - The YAML MUST be compatible with Kubernetes.
       - Include necessary resources: Deployment, Service, Pod, etc.
       - Use deterministic names.
    3. Create a detailed explanation in Japanese that includes:
       - Summary of what the user requested
       - List of ALL generated YAML resources with their specific names and purposes
       - Detailed explanation of how these resources interact and communicate (including ports)
       - Step-by-step Reconcile Flow describing controller actions
       - CRITICAL: Use plain text only. NO Markdown formatting (no **, -, #, etc.)
       - Use newlines and indentation for readability

    Output Format:
    Return a JSON object:
    {{
        "description": "日本語での詳細な解説（プレーンテキストのみ、Markdown不可、改行使用可）...",
        "yaml": "Multi-document YAML string (separated by ---)"
    }}
    """

    try:
        # Call AI for Step 1
        response_1 = requests.post(
            f"{GEMINI_URL}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt_yaml}]}],
                "generationConfig": {"response_mime_type": "application/json"},
            },
            timeout=60,
        )
        response_1.raise_for_status()
        data_1 = response_1.json()
        generated_json_1 = data_1["candidates"][0]["content"]["parts"][0]["text"]
        step1_data = json.loads(generated_json_1)

        # Handle case where AI returns array instead of object
        if isinstance(step1_data, list):
            step1_data = step1_data[0] if step1_data else {}

        description = step1_data.get("description", "No description provided.")
        yaml_content = step1_data.get("yaml", "")

        if not yaml_content:
            return ScenarioCreate(
                name=f"Error: {user_content[:20]}...",
                description="AI failed to generate YAML.",
                topology_json={"mermaid": "flowchart TD\n  A[Failed to generate YAML]"},
                events_json={"events": []},
                yaml_content="",
            )

        # --- Review Loop: Validate YAML (max 2 retries) ---
        max_retries = 2
        for attempt in range(max_retries):
            review_result = review_yaml(api_key, yaml_content, user_content)

            if review_result["approved"]:
                break

            if attempt < max_retries - 1:
                retry_instruction = review_result.get("instruction", "")
                regenerated = regenerate_yaml(
                    api_key, user_content, yaml_content, retry_instruction
                )
                yaml_content = regenerated.get("yaml", "")
                new_description = regenerated.get("description", "")
                if new_description:
                    description = new_description
                if not yaml_content:
                    return ScenarioCreate(
                        name=f"Error: {user_content[:20]}...",
                        description="AI failed to regenerate YAML.",
                        topology_json={
                            "mermaid": "flowchart TD\n  A[Failed to regenerate YAML]"
                        },
                        events_json={"events": []},
                        yaml_content="",
                    )

        # --- Step 2: Generate Topology from YAML ---
        prompt_topology = f"""
        Role: Mermaid Diagram generator for Kubernetes.

        Task:
        Given the following Kubernetes YAML, generate a Kubernetes topology as Mermaid flowchart.

        Input YAML:
        {yaml_content}

        Rules:
        1. Use Mermaid flowchart syntax.
           - Use `flowchart TB` or `flowchart TD` (avoid LR/RL).
        2. Kubernetes units and framing (CRITICAL):
           - Assume exactly ONE Kubernetes cluster. Do NOT consider multiple clusters.
           - Use subgraph to draw a clear frame for the cluster.
           - Use subgraph to draw a clear frame for control plane inside the cluster.
           - Use subgraph to draw clear frames for each node.
           - Place kubelet inside each node frame so the relationship is visually obvious.
           - Deployment, Service, and ReplicaSet must be inside the control plane frame.
        3. Resources:
           - Create entities for every resource in YAML.
           - Expand Deployments: Deployment -> ReplicaSet -> Pods (assume 1 replica if not specified, unless scaled).
           - Mandatory control plane entities: User, API Server, Controller Manager, Scheduler, etcd.
        4. Connections (CRITICAL - All resources must be connected):
           - User Flow:
             * User -> API Server (Create/Update requests)
           - Control Plane Flow:
             * API Server -> Controller Manager (Watch resources)
             * Controller Manager -> API Server (Create/Update ReplicaSets, reconcile state)
             * API Server -> Scheduler (Watch unscheduled Pods)
             * Scheduler -> API Server (Bind Pods to nodes)
             * API Server <-> etcd (Read/Write cluster state)
           - Resource Ownership (Parent-Child relationships):
             * Deployment -> ReplicaSet (Owns, label: "Manages")
             * ReplicaSet -> Pod (Owns, label: "Manages")
           - Node & Pod Management:
             * kubelet -> API Server (Watch resources)
             * Scheduler -> kubelet (Assign Pod, for each node)
             * kubelet -> Pod (Manage, for each Pod on that node)
           - Application Flow:
             * Service -> Pod (Route traffic, with port info)
             * Pod -> Pod or External (Application connections, with port info)
           - CRITICAL: Edge labels MUST include port information and protocol when applicable.
           - Examples: "HTTP:8080", "TCP:5432", "gRPC:50051", "HTTPS:443", "API:6443"
           - For Service connections, specify the Service port and target port.
           - For Pod-to-Pod connections, specify the container port.
        5. Events:
           - Generate a list of likely Kubernetes events (Normal/Warning) that would occur.
           - Event messages MUST be in Japanese.
        6. Visual requirements (CRITICAL):
           - Add animated arrows with edge IDs.
             Example:
               r1@---->|Request| api
               r2@---->|Response| user
               r1@{{ animation: fast }}
               r2@{{ animation: slow }}
           - Use readable colors with classDef/class or style directives.
           - Keep the composition square-friendly and avoid very wide layouts.

        Output Format (JSON):
        {{
            "mermaid": "Mermaid flowchart text",
            "events": [ {{"kind": "Pod", "name": "...", "message": "日本語メッセージ..."}} ]
        }}
        """

        # Call AI for Step 2
        response_2 = requests.post(
            f"{GEMINI_URL}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt_topology}]}],
                "generationConfig": {"response_mime_type": "application/json"},
            },
            timeout=60,
        )
        response_2.raise_for_status()
        data_2 = response_2.json()
        generated_json_2 = data_2["candidates"][0]["content"]["parts"][0]["text"]
        step2_data = json.loads(generated_json_2)

        mermaid = _normalize_mermaid(step2_data.get("mermaid", ""))
        events = step2_data.get("events", [])

        # --- Review Loop: Validate Diagram (max 2 retries) ---
        for attempt in range(max_retries):
            review_result = review_diagram(api_key, yaml_content, mermaid, events)

            if review_result["approved"]:
                break

            if attempt < max_retries - 1:
                retry_instruction = review_result.get("instruction", "")
                regenerated = regenerate_diagram(
                    api_key, yaml_content, mermaid, events, retry_instruction
                )
                mermaid = _normalize_mermaid(regenerated.get("mermaid", ""))
                events = regenerated.get("events", [])

        # Post-processing: Apply YAML to Cluster
        created_resources = []
        if yaml_content:
            k8s_client = get_k8s_client()
            api_client = k8s_client.api_client
            yaml_objects = list(yaml.safe_load_all(yaml_content))
            for obj in yaml_objects:
                if not obj or not isinstance(obj, dict):
                    continue
                try:
                    utils.create_from_dict(api_client, obj)
                    kind = obj.get("kind", "Unknown")
                    name = obj.get("metadata", {}).get("name", "Unknown")
                    created_resources.append(f"{kind}/{name}")
                except Exception as e:
                    print(f"Failed to apply {obj.get('kind')}: {e}")

        return ScenarioCreate(
            name=f"Scenario: {user_content[:20]}...",
            description=description,
            topology_json={"mermaid": mermaid},
            events_json={"events": events},
            yaml_content=yaml_content,
        )

    except Exception as e:
        print(f"Error in generation: {e}")
        import traceback

        traceback.print_exc()
        return ScenarioCreate(
            name=f"Error: {user_content[:20]}...",
            description=f"Failed to generate scenario: {str(e)}",
            topology_json={"mermaid": "flowchart TD\n  A[Failed to generate scenario]"},
            events_json={"events": []},
            yaml_content="",
        )
