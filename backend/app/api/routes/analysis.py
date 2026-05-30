"""Analysis API endpoints - starts Azure Durable Functions orchestration."""
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    AnalysisRequest, AnalysisTaskStatus, AnalysisTaskResponse,
)
from app.services.orchestration_client import get_orchestration_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analysis/request", response_model=AnalysisTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_analysis(request: AnalysisRequest) -> AnalysisTaskResponse:
    """Create analysis task and start the Durable Functions orchestration."""
    ticker = request.ticker.upper().strip()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker symbol is required")
    
    task_id = str(uuid4())
    llm_enabled = request.llm_config is not None
    
    try:
        client = get_orchestration_client()
        llm_config = None
        if request.llm_config:
            llm_config = {
                "provider": request.llm_config.provider.value,
                "api_key": request.llm_config.api_key,
                "model": request.llm_config.model,
            }
        client.start_analysis(ticker, task_id, llm_config)
    except Exception as e:
        logger.error(f"Failed to start orchestration: {e}")
        raise HTTPException(status_code=503, detail=f"Orchestration unavailable: {e}")
    
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
