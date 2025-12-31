"""Database utilities for Azure Functions."""
import logging
import uuid
from datetime import datetime
import psycopg2
from psycopg2.extras import Json

from shared.config import get_settings
from shared.webpubsub_utils import send_progress, send_completed, send_error

logger = logging.getLogger(__name__)


def save_analysis_report(data: dict) -> dict:
    """Save analysis report to PostgreSQL."""
    task_id = data.get("task_id")
    ticker = data.get("ticker")
    settings = get_settings()
    
    try:
        send_progress(task_id, 90, "Saving report")
        
        conn = psycopg2.connect(settings.database_url)
        cur = conn.cursor()
        
        report_id = str(uuid.uuid4())
        
        cur.execute("""
            INSERT INTO analysis_reports (
                id, ticker, company_name, price_data, news_summary,
                sentiment_score, sentiment_breakdown, sentiment_details, ai_insights, analyzed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            report_id,
            data["ticker"],
            data.get("company_name", data["ticker"]),
            Json(data.get("price_data", [])),
            data.get("news_summary", ""),
            data.get("sentiment_score", 0),
            Json(data.get("sentiment_breakdown", {})),
            Json(data.get("sentiment_details", [])),
            data.get("ai_insights", ""),
            datetime.utcnow()
        ))
        
        # Update task status
        if data.get("task_id"):
            cur.execute("""
                UPDATE analysis_tasks 
                SET status = 'completed', progress = 100, current_step = 'Analysis complete'
                WHERE id = %s
            """, (data["task_id"],))
        
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Saved report {report_id} for {ticker}")
        send_completed(task_id, ticker, report_id)
        return {"id": report_id, "status": "success"}
        
    except Exception as e:
        logger.error(f"Failed to save report: {e}")
        send_error(task_id, str(e))
        return {"status": "error", "error": str(e)}
