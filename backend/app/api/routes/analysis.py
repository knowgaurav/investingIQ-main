"""Analysis API endpoints - uses Redis + Service Bus (no database required)."""
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    AnalysisRequest, AnalysisTaskStatus, AnalysisTaskResponse,
)
from app.services.service_bus import get_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analysis/request", response_model=AnalysisTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_analysis(request: AnalysisRequest) -> AnalysisTaskResponse:
    """Create analysis task and send to Azure Service Bus for processing."""
    ticker = request.ticker.upper().strip()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker symbol is required")
    
    task_id = str(uuid4())
    llm_enabled = request.llm_config is not None
    
    try:
        orchestrator = get_orchestrator()
        llm_config = None
        if request.llm_config:
            llm_config = {
                "provider": request.llm_config.provider.value,
                "api_key": request.llm_config.api_key,
                "model": request.llm_config.model,
            }
        orchestrator.start_analysis(ticker, task_id, llm_config)
    except Exception as e:
        logger.error(f"Failed to queue analysis: {e}")
        raise HTTPException(status_code=503, detail=f"Service Bus unavailable: {e}")
    
    analysis_type = "ML + LLM" if llm_enabled else "ML only"
    return AnalysisTaskResponse(
        task_id=task_id, 
        status="processing", 
        message=f"Analysis queued for {ticker} ({analysis_type})"
    )


@router.get("/analysis/status/{task_id}", response_model=AnalysisTaskStatus)
async def get_analysis_status(task_id: UUID) -> AnalysisTaskStatus:
    """Get task status - now tracked via SSE, this is just a fallback."""
    return AnalysisTaskStatus(
        task_id=str(task_id),
        ticker="",
        status="processing",
        progress=0,
        current_step="Use SSE endpoint for real-time updates",
        error_message=None
    )
