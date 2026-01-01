"""Activity: Aggregate all analysis results and save to database."""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def main(input_data: dict) -> dict:
    from shared.webpubsub_utils import send_progress
    from shared.database import save_analysis_report
    
    ticker = input_data["ticker"]
    task_id = input_data["task_id"]
    stock_data = input_data["stock_data"]
    news_data = input_data["news_data"]
    analysis_results = input_data["analysis_results"]
    llm_enabled = input_data["llm_enabled"]
    
    send_progress(task_id, 90, "Aggregating results")
    
    result = {
        "ticker": ticker,
        "task_id": task_id,
        "timestamp": datetime.utcnow().isoformat(),
        "stock_data": stock_data,
        "news_count": len(news_data),
        "ml_analysis": None,
        "llm_analysis": None,
    }
    
    for item in analysis_results:
        if item["type"] == "ml_analysis":
            result["ml_analysis"] = item["data"]
        elif item["type"] == "llm_analysis":
            result["llm_analysis"] = item["data"]
    
    # Save to database
    save_analysis_report(result)
    
    send_progress(task_id, 100, "Analysis complete")
    logger.info(f"Aggregated results for {ticker}, LLM enabled: {llm_enabled}")
    
    return result
