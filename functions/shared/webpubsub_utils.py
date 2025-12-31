"""Progress callback utilities for Azure Functions - sends updates to API via HTTP."""
import logging
import requests

from shared.config import get_settings

logger = logging.getLogger(__name__)


def _send_callback(payload: dict):
    """Send callback to backend API."""
    try:
        settings = get_settings()
        url = f"{settings.backend_callback_url}/api/v1/callback/progress"
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        logger.info(f"Sent progress callback: {payload.get('progress')}%")
    except Exception as e:
        logger.warning(f"Failed to send callback: {e}")


def send_progress(task_id: str, progress: int, step: str, status: str = "processing", ticker: str = ""):
    """Send progress update to backend API."""
    _send_callback({
        "task_id": task_id,
        "progress": progress,
        "current_step": step,
        "status": status,
        "ticker": ticker,
    })


def send_completed(task_id: str, ticker: str, report_id: str):
    """Send completion notification."""
    _send_callback({
        "task_id": task_id,
        "progress": 100,
        "current_step": "Analysis complete",
        "status": "completed",
        "ticker": ticker,
        "report_id": report_id,
    })


def send_completed_with_data(task_id: str, ticker: str, results: dict):
    """Send completion with full analysis data (no DB storage)."""
    _send_callback({
        "task_id": task_id,
        "progress": 100,
        "current_step": "Analysis complete",
        "status": "completed",
        "ticker": ticker,
        "data": {
            "stock_data": results.get("stock_data"),
            "news": results.get("news"),
            "ml_prediction": results.get("ml_prediction"),
            "ml_technical": results.get("ml_technical"),
            "ml_sentiment": results.get("ml_sentiment"),
            "llm_sentiment": results.get("llm_sentiment"),
            "llm_summary": results.get("llm_summary"),
            "llm_insights": results.get("llm_insights"),
        }
    })


def send_error(task_id: str, error: str, ticker: str = ""):
    """Send error notification."""
    _send_callback({
        "task_id": task_id,
        "progress": 0,
        "current_step": "Failed",
        "status": "failed",
        "ticker": ticker,
        "error": error,
    })
