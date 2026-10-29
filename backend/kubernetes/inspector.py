from __future__ import annotations

from typing import Any

from core.config import settings
from kubernetes.executor import KubectlExecutor

PROBLEM_STATES = {"CrashLoopBackOff", "ImagePullBackOff", "ErrImagePull", "Pending", "Error", "OOMKilled", "ContainerCreating"}
EVENT_REASONS = {"FailedScheduling", "BackOff", "FailedMount", "FailedPull", "ErrImagePull", "Unhealthy"}


def _container_statuses(pod: dict[str, Any]) -> list[dict[str, Any]]:
    statuses = []
    for container in pod.get("status", {}).get("containerStatuses", []) + pod.get("status", {}).get("initContainerStatuses", []):
        state = container.get("state", {})
        waiting = state.get("waiting", {})
        terminated = state.get("terminated", {})
        reason = waiting.get("reason") or terminated.get("reason")
        if reason:
            statuses.append({"container": container.get("name"), "reason": reason, "message": waiting.get("message") or terminated.get("message")})
    return statuses


def inspect_pods(executor: KubectlExecutor) -> dict[str, Any]:
    data, error = executor.json(["get", "pods", "-A"])
    if error:
        return {"healthy": False, "problematic_pods": [], "errors": [error]}
    pods = data.get("items", []) if isinstance(data, dict) else []
    problematic = []
    for pod in pods:
        statuses = _container_statuses(pod)
        phase = pod.get("status", {}).get("phase", "Unknown")
        reasons = [item["reason"] for item in statuses]
        detected = next((reason for reason in reasons if reason in PROBLEM_STATES), None)
        if not detected and phase in PROBLEM_STATES:
            detected = phase
        not_ready = any(item.get("ready") is False for item in pod.get("status", {}).get("containerStatuses", []))
        if detected or (phase == "Running" and not_ready):
            problematic.append({"name": pod.get("metadata", {}).get("name"), "namespace": pod.get("metadata", {}).get("namespace"), "status": detected or "NotReady", "restart_count": sum(item.get("restartCount", 0) for item in pod.get("status", {}).get("containerStatuses", [])), "containers": statuses})
    return {"healthy": not problematic, "total_pods": len(pods), "problematic_pods": problematic, "errors": []}


def collect_logs(executor: KubectlExecutor, pods: dict[str, Any]) -> dict[str, Any]:
    logs = []
    for pod in pods.get("problematic_pods", []):
        result = executor.run(["logs", "-n", pod["namespace"], pod["name"], "--all-containers=true", f"--tail={settings.log_tail_lines}"])
        logs.append({"name": pod["name"], "namespace": pod["namespace"], "logs": result.stdout[-12000:] if result.ok else "", "error": result.error or ""})
    return {"items": logs, "errors": []}


def inspect_events(executor: KubectlExecutor) -> dict[str, Any]:
    data, error = executor.json(["get", "events", "-A", "--sort-by=.lastTimestamp"])
    if error:
        return {"findings": [], "errors": [error]}
    findings = []
    for event in (data or {}).get("items", []) if isinstance(data, dict) else []:
        reason = event.get("reason", "")
        if reason in EVENT_REASONS:
            findings.append({"reason": reason, "message": event.get("message", "")[-1000:], "namespace": event.get("metadata", {}).get("namespace"), "object": event.get("involvedObject", {}).get("name"), "type": event.get("type", "Warning")})
    return {"findings": findings[-100:], "errors": []}


def inspect_deployments(executor: KubectlExecutor) -> dict[str, Any]:
    data, error = executor.json(["get", "deployments", "-A"])
    if error:
        return {"healthy": False, "deployments": [], "errors": [error]}
    deployments = []
    for deployment in (data or {}).get("items", []) if isinstance(data, dict) else []:
        spec = deployment.get("spec", {})
        status = deployment.get("status", {})
        desired = spec.get("replicas", 0)
        available = status.get("availableReplicas", 0)
        unavailable = status.get("unavailableReplicas", 0)
        conditions = status.get("conditions", [])
        failed = [condition.get("message", condition.get("reason", "")) for condition in conditions if condition.get("type") == "Progressing" and condition.get("reason") == "ProgressDeadlineExceeded"]
        if available < desired or unavailable > 0 or failed:
            deployments.append({"name": deployment.get("metadata", {}).get("name"), "namespace": deployment.get("metadata", {}).get("namespace"), "desired": desired, "available": available, "unavailable": unavailable, "conditions": failed or conditions})
    return {"healthy": not deployments, "deployments": deployments, "errors": []}


def inspect_network(executor: KubectlExecutor) -> dict[str, Any]:
    services, service_error = executor.json(["get", "services", "-A"])
    endpoints, endpoint_error = executor.json(["get", "endpoints", "-A"])
    endpoint_map = {(item.get("metadata", {}).get("namespace"), item.get("metadata", {}).get("name")): item for item in (endpoints or {}).get("items", [])} if isinstance(endpoints, dict) else {}
    findings = []
    for service in (services or {}).get("items", []) if isinstance(services, dict) else []:
        metadata = service.get("metadata", {})
        key = (metadata.get("namespace"), metadata.get("name"))
        subsets = endpoint_map.get(key, {}).get("subsets", [])
        if not subsets or not any(subset.get("addresses") for subset in subsets):
            findings.append({"service": metadata.get("name"), "namespace": metadata.get("namespace"), "issue": "Service has no ready endpoints", "selector": service.get("spec", {}).get("selector", {})})
    errors = [error for error in [service_error, endpoint_error] if error]
    return {"healthy": not findings and not errors, "findings": findings, "errors": errors}
