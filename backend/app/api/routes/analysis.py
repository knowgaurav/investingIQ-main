"""Analysis API endpoints - thin router that offloads to Azure Service Bus."""
import logging
from uuid import UUID, uuid4
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.models.schemas import (
    AnalysisRequest, AnalysisTaskStatus, AnalysisTaskResponse,
    AnalysisReportResponse, PriceDataPoint, SentimentResult,
)
from app.models.database import get_db, AnalysisTask, AnalysisReport
from app.services.service_bus import get_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analysis/request", response_model=AnalysisTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_analysis(
    request: AnalysisRequest,
    db: Session = Depends(get_db)
) -> AnalysisTaskResponse:
    """Create analysis task and send to Azure Service Bus for processing."""
    ticker = request.ticker.upper().strip()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker symbol is required")
    
    task_id = str(uuid4())
    task = AnalysisTask(id=task_id, ticker=ticker, status="processing", progress=0, current_step="Queued for processing")
    db.add(task)
    db.commit()
    
    try:
        # Send to Service Bus - Azure Functions will process
        orchestrator = get_orchestrator()
        orchestrator.start_analysis(ticker, task_id)
    except Exception as e:
        logger.error(f"Failed to queue analysis: {e}")
        task.status = "failed"
        task.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=503, detail=f"Service Bus unavailable: {e}")
    
    return AnalysisTaskResponse(task_id=task_id, status="processing", message=f"Analysis queued for {ticker}")


@router.get("/analysis/status/{task_id}", response_model=AnalysisTaskStatus)
async def get_analysis_status(task_id: UUID, db: Session = Depends(get_db)) -> AnalysisTaskStatus:
    task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return AnalysisTaskStatus(task_id=task.id, ticker=task.ticker, status=task.status, progress=task.progress or 0, current_step=task.current_step, error_message=task.error_message)


@router.get("/analysis/report/{ticker}", response_model=AnalysisReportResponse)
async def get_analysis_report(ticker: str, db: Session = Depends(get_db)) -> AnalysisReportResponse:
    ticker = ticker.upper().strip()
    report = db.query(AnalysisReport).filter(AnalysisReport.ticker == ticker).order_by(AnalysisReport.analyzed_at.desc()).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"No report found for {ticker}")
    
    price_data = [PriceDataPoint(date=datetime.fromisoformat(p["date"]) if isinstance(p["date"], str) else p["date"], open=p["open"], high=p["high"], low=p["low"], close=p["close"], volume=p["volume"]) for p in (report.price_data or [])]
    sentiment_details = [SentimentResult(headline=d["headline"], sentiment=d["sentiment"], confidence=d.get("confidence", 0), reasoning=d.get("reasoning", "")) for d in (report.sentiment_details or [])] if report.sentiment_details else None
    
    return AnalysisReportResponse(id=report.id, ticker=report.ticker, company_name=report.company_name, analyzed_at=report.analyzed_at, price_data=price_data, news_summary=report.news_summary, sentiment_score=report.sentiment_score, sentiment_breakdown=report.sentiment_breakdown, sentiment_details=sentiment_details, ai_insights=report.ai_insights)
