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
    # Will be fully implemented when database is connected
    import uuid
    report_id = str(uuid.uuid4())
    logger.info(f"Saved analysis report {report_id} for {ticker}")
    return report_id


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
