"""
Health check route.
"""
from fastapi import APIRouter
from backend.app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def get_health() -> HealthResponse:
    """
    Basic health check endpoint to verify service availability.
    """
    return HealthResponse(status="ok")
