from __future__ import annotations

from collections.abc import Callable
from typing import Any

from kubernetes.executor import KubectlExecutor
from kubernetes.inspector import collect_logs, inspect_deployments, inspect_events, inspect_network, inspect_pods


def run_evidence_collection(context: str | None = None, on_progress: Callable[[str], None] | None = None) -> dict[str, Any]:
    executor = KubectlExecutor(context)
    progress = on_progress or (lambda _step: None)
    progress("Checking Pods")
    pods = inspect_pods(executor)
    progress("Reading Logs")
    logs = collect_logs(executor, pods)
    progress("Analyzing Events")
    events = inspect_events(executor)
    progress("Inspecting Deployments")
    deployments = inspect_deployments(executor)
    progress("Checking Networking")
    network = inspect_network(executor)
    return {"pods": pods, "logs": logs, "events": events, "deployments": deployments, "network": network}
