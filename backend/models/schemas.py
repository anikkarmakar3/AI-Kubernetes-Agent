from pydantic import BaseModel, Field
from typing import Any


class HealthResponse(BaseModel):
    status: str
    service: str


class ClusterInfo(BaseModel):
    name: str
    current: bool = False


class InvestigationRequest(BaseModel):
    context: str | None = None


class Diagnosis(BaseModel):
    root_cause: str
    explanation: str
    fix: str
    kubectl_command: str
    prevention: str
    confidence: int
    evidence: list[str] = Field(default_factory=list)


class InvestigationResponse(BaseModel):
    status: str
    investigation_id: str
    context: str | None = None
    progress: list[str]
    investigation: dict[str, Any]
    diagnosis: Diagnosis
    error: str | None = None
