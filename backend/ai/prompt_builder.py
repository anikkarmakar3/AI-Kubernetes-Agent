import json
from typing import Any

SYSTEM_PROMPT = """You are a senior Kubernetes SRE. Correlate the supplied evidence and identify one primary root cause. Do not invent resources or commands. Return only valid JSON with keys: root_cause, explanation, fix, kubectl_command, prevention, confidence, evidence. confidence must be an integer from 0 to 100. If the cluster evidence contains an access error, explain that clearly instead of claiming the cluster is healthy."""


def build_prompt(investigation: dict[str, Any]) -> str:
    return "Analyze this Kubernetes investigation evidence. Keep the answer concise and beginner friendly:\n" + json.dumps(investigation, indent=2, default=str)[:40000]
