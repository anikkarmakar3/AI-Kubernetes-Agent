from __future__ import annotations

from typing import Any

from ai.client import request_diagnosis
from ai.prompt_builder import SYSTEM_PROMPT, build_prompt


def heuristic_diagnosis(investigation: dict[str, Any]) -> dict[str, Any]:
    text = str(investigation).lower()
    pods = investigation.get("pods", {}).get("problematic_pods", [])
    first = pods[0] if pods else {}
    name = first.get("name", "the affected deployment")
    namespace = first.get("namespace", "default")
    status = first.get("status", "")
    if "database_url" in text or "missing env" in text or "environment variable" in text:
        return {"root_cause": "A required environment variable is missing", "explanation": "The container fails during startup because its application configuration is incomplete.", "fix": "Add the missing value through a Secret or ConfigMap and restart the workload.", "kubectl_command": f"kubectl -n {namespace} edit deployment {name}", "prevention": "Validate required environment variables during deployment and use a Secret for credentials.", "confidence": 94, "evidence": ["Startup logs mention a missing environment variable", f"Pod state is {status or 'unhealthy'}"]}
    if "imagepullbackoff" in text or "errimagepull" in text or "failedpull" in text:
        return {"root_cause": "The container image cannot be pulled", "explanation": "Kubernetes cannot find or authenticate to the configured image registry and tag.", "fix": "Correct the image repository/tag and verify registry credentials.", "kubectl_command": f"kubectl -n {namespace} set image deployment/{name} APP=REPOSITORY:TAG", "prevention": "Pin valid image tags and validate images in CI before rollout.", "confidence": 96, "evidence": ["Pod or event state indicates an image pull failure"]}
    if "oomkilled" in text:
        return {"root_cause": "The container exceeded its memory limit", "explanation": "The kernel terminated the container after it used more memory than Kubernetes allowed.", "fix": "Increase the container memory limit after measuring usage, then review the application memory behavior.", "kubectl_command": f"kubectl -n {namespace} edit deployment {name}", "prevention": "Set realistic requests and limits and alert on memory saturation.", "confidence": 96, "evidence": ["Container termination reason is OOMKilled"]}
    if "no ready endpoints" in text or ("selector" in text and "mismatch" in text):
        return {"root_cause": "A Service has no matching ready endpoints", "explanation": "The Service selector does not route traffic to healthy pod labels.", "fix": "Align the Service selector with the pod template labels and verify the endpoints.", "kubectl_command": "kubectl get svc,endpoints -A", "prevention": "Test Service selectors and endpoint readiness during deployment checks.", "confidence": 90, "evidence": ["Service inspection found no ready endpoints"]}
    errors = investigation.get("pods", {}).get("errors", []) + investigation.get("events", {}).get("errors", [])
    if errors:
        return {"root_cause": "Kubernetes evidence could not be collected", "explanation": "The backend could not reach the selected cluster or execute kubectl.", "fix": "Verify kubeconfig path, cluster access, kubectl installation, and permissions.", "kubectl_command": "kubectl cluster-info", "prevention": "Add a preflight cluster connectivity check before investigations.", "confidence": 99, "evidence": errors[:3]}
    if not pods:
        return {"root_cause": "No critical Kubernetes issues detected", "explanation": "The collected pod, event, deployment, and networking evidence contains no detected critical issue.", "fix": "No immediate fix is required.", "kubectl_command": "kubectl get pods -A", "prevention": "Continue monitoring events, rollout health, and resource usage.", "confidence": 82, "evidence": ["No problematic pods were detected"]}
    return {"root_cause": status or "A Kubernetes workload is unhealthy", "explanation": f"The workload {name} is not healthy and requires inspection of its recent events and logs.", "fix": "Review the pod logs and warning events, then update the workload configuration.", "kubectl_command": f"kubectl -n {namespace} describe pod {name}", "prevention": "Add rollout health checks and alerts for repeated restarts.", "confidence": 70, "evidence": [f"Pod state is {status or 'unhealthy'}"]}


async def analyze_cluster(investigation: dict[str, Any]) -> dict[str, Any]:
    response = await request_diagnosis(SYSTEM_PROMPT, build_prompt(investigation))
    return response or heuristic_diagnosis(investigation)


def suggest_fix(investigation: dict[str, Any]) -> dict[str, Any]:
    return heuristic_diagnosis(investigation)
