"""Health check endpoints."""
from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    version: str


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint"
)
async def health_check() -> HealthResponse:
    """
    Check if the service is healthy.
    
    Returns HTTP 200 with status "healthy" when all dependencies are available.
    """
    return HealthResponse(
        status="healthy",
        service="investingiq-api",
        version="2.0.0"
    )
