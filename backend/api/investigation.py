from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException
from fastapi.concurrency import run_in_threadpool
from loguru import logger

from ai.agent import analyze_cluster
from core.config import settings
from kubernetes.executor import list_contexts
from models.schemas import ClusterInfo, Diagnosis, InvestigationRequest, InvestigationResponse
from services.investigation import run_evidence_collection

router = APIRouter()


@router.get("/clusters", response_model=list[ClusterInfo])
def clusters() -> list[ClusterInfo]:
    contexts, error = list_contexts()
    if error:
        raise HTTPException(status_code=503, detail={"message": "Unable to read local Kubernetes contexts.", "reason": error})
    return [ClusterInfo(**context) for context in contexts]


@router.post("/investigate", response_model=InvestigationResponse)
async def investigate(request: InvestigationRequest, authorization: str | None = Header(default=None)) -> InvestigationResponse:
    if settings.require_auth and not authorization:
        raise HTTPException(status_code=401, detail="Authentication is required to investigate a cluster.")
    investigation_id = str(uuid4())
    progress: list[str] = []
    try:
        evidence = await run_in_threadpool(run_evidence_collection, request.context, progress.append)
        progress.append("AI Reasoning")
        raw_diagnosis = await analyze_cluster(evidence)
        diagnosis = Diagnosis(
            root_cause=str(raw_diagnosis.get("root_cause", "Unknown Kubernetes issue")),
            explanation=str(raw_diagnosis.get("explanation", "No explanation was returned.")),
            fix=str(raw_diagnosis.get("fix", "Review the evidence and recent events.")),
            kubectl_command=str(raw_diagnosis.get("kubectl_command", "kubectl get pods -A")),
            prevention=str(raw_diagnosis.get("prevention", "Add monitoring and rollout checks.")),
            confidence=max(0, min(100, int(raw_diagnosis.get("confidence", 0)))),
            evidence=[str(item) for item in raw_diagnosis.get("evidence", [])],
        )
        progress.append("Root Cause Found")
        has_errors = any(section.get("errors") for section in evidence.values() if isinstance(section, dict))
        return InvestigationResponse(status="partial" if has_errors else "success", investigation_id=investigation_id, context=request.context, progress=progress, investigation=evidence, diagnosis=diagnosis, error=None)
    except Exception as exc:
        logger.exception("Investigation failed")
        raise HTTPException(status_code=500, detail="Investigation failed. Verify cluster access and try again.") from exc
