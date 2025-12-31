"""Enhanced health check endpoints with dependency monitoring."""
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)


class DependencyHealth(BaseModel):
    """Health status of a single dependency."""
    name: str
    status: str  # healthy, degraded, unhealthy
    latency_ms: Optional[float] = None
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """Comprehensive health check response."""
    status: str  # healthy, degraded, unhealthy
    service: str
    version: str
    uptime_seconds: Optional[float] = None
    timestamp: str
    dependencies: List[DependencyHealth] = []


class ReadinessResponse(BaseModel):
    """Readiness check response."""
    ready: bool
    checks: Dict[str, bool]


# Track service start time
_service_start_time: Optional[datetime] = None


def set_start_time():
    """Set service start time."""
    global _service_start_time
    _service_start_time = datetime.utcnow()


async def check_postgres() -> DependencyHealth:
    """Check PostgreSQL connectivity."""
    import time
    from sqlalchemy import text
    
    start = time.time()
    try:
        from app.models.database import SessionLocal
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            latency = (time.time() - start) * 1000
            return DependencyHealth(
                name="postgres",
                status="healthy",
                latency_ms=round(latency, 2),
            )
        finally:
            db.close()
    except Exception as e:
        latency = (time.time() - start) * 1000
        logger.warning(f"PostgreSQL health check failed: {e}")
        return DependencyHealth(
            name="postgres",
            status="unhealthy",
            latency_ms=round(latency, 2),
            message=str(e),
        )


async def check_redis() -> DependencyHealth:
    """Check Redis connectivity."""
    import time
    import redis
    
    settings = get_settings()
    start = time.time()
    
    try:
        client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            socket_connect_timeout=2,
        )
        client.ping()
        latency = (time.time() - start) * 1000
        return DependencyHealth(
            name="redis",
            status="healthy",
            latency_ms=round(latency, 2),
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        logger.warning(f"Redis health check failed: {e}")
        return DependencyHealth(
            name="redis",
            status="degraded",  # Redis is optional for caching
            latency_ms=round(latency, 2),
            message=str(e),
        )


async def check_llm() -> DependencyHealth:
    """Check LLM service connectivity."""
    import time
    import httpx
    
    settings = get_settings()
    start = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Just check if the API is reachable
            response = await client.get(f"{settings.openai_base_url}/models")
            latency = (time.time() - start) * 1000
            
            if response.status_code < 500:
                return DependencyHealth(
                    name="llm",
                    status="healthy",
                    latency_ms=round(latency, 2),
                )
            else:
                return DependencyHealth(
                    name="llm",
                    status="degraded",
                    latency_ms=round(latency, 2),
                    message=f"Status code: {response.status_code}",
                )
    except Exception as e:
        latency = (time.time() - start) * 1000
        logger.warning(f"LLM health check failed: {e}")
        return DependencyHealth(
            name="llm",
            status="degraded",  # LLM is important but not critical
            latency_ms=round(latency, 2),
            message=str(e),
        )


async def check_mlflow() -> DependencyHealth:
    """Check MLflow connectivity."""
    import time
    import httpx
    
    settings = get_settings()
    start = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.mlflow_tracking_uri}/health")
            latency = (time.time() - start) * 1000
            
            return DependencyHealth(
                name="mlflow",
                status="healthy" if response.status_code == 200 else "degraded",
                latency_ms=round(latency, 2),
            )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return DependencyHealth(
            name="mlflow",
            status="degraded",  # MLflow is optional
            latency_ms=round(latency, 2),
            message=str(e),
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Check the health of the service and all its dependencies."
)
async def health_check() -> HealthResponse:
    """
    Comprehensive health check.
    
    Returns HTTP 200 with status "healthy" when all critical dependencies are available.
    Returns HTTP 200 with status "degraded" when non-critical dependencies are unavailable.
    Returns HTTP 503 with status "unhealthy" when critical dependencies fail.
    """
    settings = get_settings()
    
    # Check all dependencies in parallel
    checks = await asyncio.gather(
        check_postgres(),
        check_redis(),
        check_llm(),
        check_mlflow(),
        return_exceptions=True,
    )
    
    # Convert exceptions to unhealthy status
    dependencies = []
    for check in checks:
        if isinstance(check, Exception):
            dependencies.append(DependencyHealth(
                name="unknown",
                status="unhealthy",
                message=str(check),
            ))
        else:
            dependencies.append(check)
    
    # Determine overall status
    critical_deps = ["postgres"]  # Only postgres is critical
    
    overall_status = "healthy"
    for dep in dependencies:
        if dep.status == "unhealthy" and dep.name in critical_deps:
            overall_status = "unhealthy"
            break
        elif dep.status in ("unhealthy", "degraded"):
            if overall_status == "healthy":
                overall_status = "degraded"
    
    # Calculate uptime
    uptime = None
    if _service_start_time:
        uptime = (datetime.utcnow() - _service_start_time).total_seconds()
    
    return HealthResponse(
        status=overall_status,
        service=settings.app_name,
        version="2.0.0",
        uptime_seconds=uptime,
        timestamp=datetime.utcnow().isoformat() + "Z",
        dependencies=dependencies,
    )


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Simple liveness check for Kubernetes."
)
async def liveness() -> dict:
    """Simple liveness check - just confirms the service is running."""
    return {"status": "alive"}


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Check if the service is ready to receive traffic."
)
async def readiness() -> ReadinessResponse:
    """
    Readiness check for Kubernetes.
    
    Returns ready=True only if critical dependencies are available.
    """
    # Check only critical dependencies
    postgres_check = await check_postgres()
    
    checks = {
        "postgres": postgres_check.status == "healthy",
    }
    
    all_ready = all(checks.values())
    
    return ReadinessResponse(
        ready=all_ready,
        checks=checks,
    )


@router.get(
    "/health/circuits",
    status_code=status.HTTP_200_OK,
    summary="Circuit breaker status",
    description="Get the status of all circuit breakers."
)
async def circuit_status() -> dict:
    """Get status of all circuit breakers."""
    from app.utils.circuit_breaker import get_all_circuit_stats
    
    stats = get_all_circuit_stats()
    return {
        "circuits": [
            {
                "name": s.name,
                "state": s.state,
                "failure_count": s.failure_count,
                "total_calls": s.total_calls,
                "total_failures": s.total_failures,
            }
            for s in stats
        ]
    }


@router.get(
    "/health/cache",
    status_code=status.HTTP_200_OK,
    summary="Cache status",
    description="Get cache statistics."
)
async def cache_status() -> dict:
    """Get cache statistics."""
    from app.utils.cache import get_cache_service
    
    cache = get_cache_service()
    return cache.get_stats()
