"""Activity: Aggregate all analysis results and save to database."""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Map the ML prediction trend to a directional signal for dual comparison.
_ML_TREND_TO_SIGNAL = {
    "strong_upward": "bullish",
    "upward": "bullish",
    "sideways": "neutral",
    "downward": "bearish",
    "strong_downward": "bearish",
}


def _ml_signal(ml_data: dict) -> str:
    """Derive a directional signal from the ML prediction trend."""
    if not ml_data:
        return None
    trend = (ml_data.get("prediction") or {}).get("trend")
    return _ML_TREND_TO_SIGNAL.get(trend)


def main(input_data: dict) -> dict:
    from shared.webpubsub_utils import send_progress
    from shared.db_utils import save_analysis_report

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
        "news": news_data,
        "news_count": len(news_data),
        "ml_analysis": None,
        "ml_status": "missing",
        "llm_analysis": None,
        "llm_status": "not_run",
        "financials_status": "not_run",
        "financials_quarter": None,
        "dual_comparison": None,
    }

    for item in analysis_results:
        item_type = item.get("type")
        if item_type == "ml_analysis":
            result["ml_status"] = item.get("status", "ok")
            result["ml_analysis"] = item.get("data")
        elif item_type == "llm_analysis":
            result["llm_status"] = item.get("status", "ok")
            result["llm_analysis"] = item.get("data")
        elif item_type == "financials_ingest":
            result["financials_status"] = item.get("status", "ok")
            result["financials_quarter"] = item.get("fiscal_quarter")

    # Dual comparison only when both pipelines produced a directional signal.
    ml_signal = _ml_signal(result["ml_analysis"]) if result["ml_status"] == "ok" else None
    llm_signal = (result["llm_analysis"] or {}).get("outlook") if result["llm_status"] == "ok" else None
    if ml_signal and llm_signal:
        result["dual_comparison"] = {
            "ml_signal": ml_signal,
            "llm_signal": llm_signal,
            "agreement": ml_signal == llm_signal,
        }

    # Save to database
    save_analysis_report(result)

    send_progress(task_id, 100, "Analysis complete")
    logger.info(
        f"Aggregated results for {ticker}: ml={result['ml_status']}, "
        f"llm={result['llm_status']}, financials={result['financials_status']}"
    )

    return result
