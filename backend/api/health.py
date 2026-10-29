from fastapi import APIRouter

from models.schemas import HealthResponse

router = APIRouter()


@router.get("/")
def service_info() -> dict[str, str]:
    return {
        "service": "ai-kubernetes-agent",
        "status": "running",
        "health": "/health",
        "api_docs": "/docs",
    }


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="healthy", service="ai-kubernetes-agent")
