"""Analysis API endpoints for stock analysis tasks."""
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.models.schemas import (
    AnalysisRequest,
    AnalysisTaskStatus,
    AnalysisTaskResponse,
    AnalysisReportResponse,
    PriceDataPoint,
    SentimentResult,
    ErrorResponse,
)
from app.models.database import get_db, AnalysisTask, AnalysisReport
from app.tasks.aggregate_tasks import orchestrate_analysis

router = APIRouter()


@router.post(
    "/analysis/request",
    response_model=AnalysisTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request stock analysis",
    description="Create a new analysis task for a stock ticker. Returns immediately with a task_id for tracking progress.",
    responses={
        202: {"description": "Analysis task created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid ticker symbol"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def request_analysis(
    request: AnalysisRequest,
    db: Session = Depends(get_db),
) -> AnalysisTaskResponse:
    """
    Create a new stock analysis task.
    
    This endpoint initiates an asynchronous analysis workflow for the specified
    stock ticker. The analysis includes:
    - Fetching stock price data
    - Gathering recent news articles
    - Sentiment analysis on news
    - AI-generated insights and summary
    
    Args:
        request: AnalysisRequest containing the ticker symbol
        db: Database session
        
    Returns:
        AnalysisTaskResponse with task_id for tracking progress
    """
    ticker = request.ticker.upper().strip()
    
    if not ticker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticker symbol is required",
        )
    
    try:
        # Start the Celery task
        celery_result = orchestrate_analysis.delay(ticker)
        
        # Create task record in database
        task = AnalysisTask(
            celery_task_id=celery_result.id,
            ticker=ticker,
            status="pending",
            progress=0,
            current_step="Initializing analysis",
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        return AnalysisTaskResponse(
            task_id=task.id,
            status="pending",
            message=f"Analysis task created for {ticker}",
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create analysis task: {str(e)}",
        )


@router.get(
    "/analysis/status/{task_id}",
    response_model=AnalysisTaskStatus,
    status_code=status.HTTP_200_OK,
    summary="Get analysis task status",
    description="Get the current status and progress of an analysis task.",
    responses={
        200: {"description": "Task status retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
)
async def get_analysis_status(
    task_id: UUID,
    db: Session = Depends(get_db),
) -> AnalysisTaskStatus:
    """
    Get the status of an analysis task.
    
    Args:
        task_id: UUID of the analysis task
        db: Database session
        
    Returns:
        AnalysisTaskStatus with current progress information
    """
    task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis task {task_id} not found",
        )
    
    return AnalysisTaskStatus(
        task_id=task.id,
        ticker=task.ticker,
        status=task.status,
        progress=task.progress or 0,
        current_step=task.current_step,
        error_message=task.error_message,
    )


@router.get(
    "/analysis/report/{ticker}",
    response_model=AnalysisReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get analysis report",
    description="Get the most recent completed analysis report for a stock ticker.",
    responses={
        200: {"description": "Analysis report retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Report not found"},
    },
)
async def get_analysis_report(
    ticker: str,
    db: Session = Depends(get_db),
) -> AnalysisReportResponse:
    """
    Get the most recent analysis report for a ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        db: Database session
        
    Returns:
        AnalysisReportResponse with complete analysis data
    """
    ticker_upper = ticker.upper().strip()
    
    # Get the most recent report for this ticker
    report = (
        db.query(AnalysisReport)
        .filter(AnalysisReport.ticker == ticker_upper)
        .order_by(AnalysisReport.analyzed_at.desc())
        .first()
    )
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis report found for ticker {ticker_upper}",
        )
    
    # Convert price_data JSON to PriceDataPoint list
    price_data = []
    if report.price_data:
        for point in report.price_data:
            price_data.append(
                PriceDataPoint(
                    date=datetime.fromisoformat(point["date"]) if isinstance(point["date"], str) else point["date"],
                    open=point["open"],
                    high=point["high"],
                    low=point["low"],
                    close=point["close"],
                    volume=point["volume"],
                )
            )
    
    # Convert sentiment_details JSON to SentimentResult list
    sentiment_details = None
    if report.sentiment_details:
        sentiment_details = [
            SentimentResult(
                headline=detail["headline"],
                sentiment=detail["sentiment"],
                confidence=detail.get("confidence", 0.0),
                reasoning=detail.get("reasoning", ""),
            )
            for detail in report.sentiment_details
        ]
    
    return AnalysisReportResponse(
        id=report.id,
        ticker=report.ticker,
        company_name=report.company_name,
        analyzed_at=report.analyzed_at,
        price_data=price_data,
        news_summary=report.news_summary,
        sentiment_score=report.sentiment_score,
        sentiment_breakdown=report.sentiment_breakdown,
        sentiment_details=sentiment_details,
        ai_insights=report.ai_insights,
    )


@router.get(
    "/analysis/report/{ticker}/history",
    status_code=status.HTTP_200_OK,
    summary="Get analysis report history",
    description="Get all analysis reports for a stock ticker.",
)
async def get_analysis_history(
    ticker: str,
    limit: int = 10,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get historical analysis reports for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        limit: Maximum number of reports to return
        db: Database session
        
    Returns:
        Dict with list of report summaries
    """
    ticker_upper = ticker.upper().strip()
    
    reports = (
        db.query(AnalysisReport)
        .filter(AnalysisReport.ticker == ticker_upper)
        .order_by(AnalysisReport.analyzed_at.desc())
        .limit(limit)
        .all()
    )
    
    return {
        "ticker": ticker_upper,
        "count": len(reports),
        "reports": [
            {
                "id": str(report.id),
                "analyzed_at": report.analyzed_at.isoformat(),
                "sentiment_score": report.sentiment_score,
                "company_name": report.company_name,
            }
            for report in reports
        ],
    }
