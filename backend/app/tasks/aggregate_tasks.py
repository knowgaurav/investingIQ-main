"""Aggregation tasks - runs on aggregate_queue workers."""
from celery import chord, group
from app.tasks.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, queue="aggregate_queue")
def orchestrate_analysis(self, ticker: str) -> dict:
    """
    Main orchestrator that kicks off parallel analysis workflow.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        dict with task group ID for tracking
    """
    from app.tasks.data_tasks import fetch_stock_data_task, fetch_news_task
    
    # Phase 1: Fetch data in parallel
    data_workflow = group(
        fetch_stock_data_task.s(ticker),
        fetch_news_task.s(ticker)
    )
    
    # Chain: data fetch -> process results
    workflow = chord(
        data_workflow,
        process_data_results.s(ticker)
    )
    
    result = workflow.apply_async()
    
    return {
        "workflow_id": str(result.id),
        "ticker": ticker,
        "status": "started"
    }


@celery_app.task(bind=True, queue="aggregate_queue")
def process_data_results(self, data_results: list, ticker: str) -> dict:
    """
    Process data fetch results and spawn LLM tasks.
    
    Args:
        data_results: [stock_data, news_articles] from data tasks
        ticker: Stock ticker symbol
        
    Returns:
        dict with next phase task IDs
    """
    from app.tasks.llm_tasks import analyze_sentiment_task, generate_summary_task
    from app.tasks.embed_tasks import embed_documents_task
    
    stock_data, news_articles = data_results
    
    # Phase 2: Run embedding + sentiment + summary in parallel
    llm_workflow = chord(
        group(
            embed_documents_task.s(ticker, stock_data, news_articles),
            analyze_sentiment_task.s(news_articles),
            generate_summary_task.s(ticker, news_articles),
        ),
        finalize_analysis.s(ticker, stock_data, news_articles)
    )
    
    result = llm_workflow.apply_async()
    
    return {
        "phase": "llm_processing",
        "workflow_id": str(result.id),
        "ticker": ticker
    }


@celery_app.task(bind=True, queue="aggregate_queue")
def finalize_analysis(
    self, 
    llm_results: list, 
    ticker: str, 
    stock_data: dict, 
    news_articles: list
) -> dict:
    """
    Final step: generate insights and save report.
    
    Args:
        llm_results: [embedding_id, sentiment, summary] from LLM tasks
        ticker: Stock ticker symbol
        stock_data: Stock price and company data
        news_articles: List of news articles
        
    Returns:
        dict with completed report info
    """
    from app.tasks.llm_tasks import generate_insights_task
    
    embedding_id, sentiment, summary = llm_results
    
    # Generate final insights
    insights = generate_insights_task.apply_async(
        args=[ticker, stock_data, sentiment, summary],
        queue="llm_queue"
    ).get(timeout=120)
    
    # Save report to database (will be implemented)
    report_id = save_analysis_report(
        ticker=ticker,
        stock_data=stock_data,
        news_articles=news_articles,
        sentiment=sentiment,
        summary=summary,
        insights=insights
    )
    
    return {
        "status": "completed",
        "report_id": report_id,
        "ticker": ticker
    }


def save_analysis_report(
    ticker: str,
    stock_data: dict,
    news_articles: list,
    sentiment: dict,
    summary: str,
    insights: str
) -> str:
    """Save analysis report to database."""
    from app.models.database import SessionLocal, AnalysisReport
    from datetime import datetime
    
    db = SessionLocal()
    try:
        # Extract company name from stock data
        company_name = stock_data.get("company_info", {}).get("name", ticker)
        
        # Convert price history to JSON-serializable format
        price_data = []
        if stock_data.get("price_history"):
            for point in stock_data["price_history"]:
                price_data.append({
                    "date": point.get("date", datetime.now().isoformat()),
                    "open": point.get("open", 0),
                    "high": point.get("high", 0),
                    "low": point.get("low", 0),
                    "close": point.get("close", 0),
                    "volume": point.get("volume", 0)
                })
        
        # Extract sentiment details
        sentiment_score = sentiment.get("overall_score", 0.0)
        sentiment_breakdown = sentiment.get("breakdown", {})
        sentiment_details = sentiment.get("details", [])
        
        report = AnalysisReport(
            ticker=ticker.upper(),
            company_name=company_name,
            analyzed_at=datetime.utcnow(),
            price_data=price_data,
            news_summary=summary,
            sentiment_score=sentiment_score,
            sentiment_breakdown=sentiment_breakdown,
            sentiment_details=sentiment_details,
            ai_insights=insights
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        report_id = str(report.id)
        logger.info(f"Saved analysis report {report_id} for {ticker}")
        return report_id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving analysis report for {ticker}: {e}")
        raise
    finally:
        db.close()


@celery_app.task(bind=True, queue="dead_letter")
def dead_letter_task(
    self, 
    task_id: str, 
    error: str, 
    args: list, 
    kwargs: dict
) -> dict:
    """
    Handle permanently failed tasks.
    
    Args:
        task_id: Original task ID
        error: Error message
        args: Original task args
        kwargs: Original task kwargs
        
    Returns:
        dict with failure info
    """
    logger.error(f"Task {task_id} permanently failed: {error}")
    logger.error(f"Args: {args}, Kwargs: {kwargs}")
    
    # Could send alerts here (Slack, email, etc.)
    
    return {
        "task_id": task_id,
        "error": error,
        "status": "dead_letter"
    }
