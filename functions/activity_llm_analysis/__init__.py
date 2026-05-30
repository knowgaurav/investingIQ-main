"""Activity: Run LLM-based analysis with tool calling."""
import logging

logger = logging.getLogger(__name__)

# Map the LLM recommendation action to a directional outlook for dual comparison.
_ACTION_TO_OUTLOOK = {
    "strong_buy": "bullish",
    "buy": "bullish",
    "hold": "neutral",
    "sell": "bearish",
    "strong_sell": "bearish",
}

# Map the LLM trend enum to a directional outlook (fallback when no recommendation).
_TREND_TO_OUTLOOK = {
    "strong_bullish": "bullish",
    "bullish": "bullish",
    "neutral": "neutral",
    "bearish": "bearish",
    "strong_bearish": "bearish",
}


def _normalize(analysis: dict, gathered_data: dict) -> dict:
    """Map the structured analyzer output into the dual-analysis shape."""
    recommendation = analysis.get("recommendation", {})
    sentiment = analysis.get("sentiment", {})
    technical = analysis.get("technical", {})

    action = recommendation.get("action")
    outlook = _ACTION_TO_OUTLOOK.get(action) or _TREND_TO_OUTLOOK.get(technical.get("trend"), "neutral")

    insight_parts = []
    if sentiment.get("news_summary"):
        insight_parts.append(sentiment["news_summary"])
    for reason in recommendation.get("key_reasons", []):
        insight_parts.append(f"- {reason}")
    insight = "\n".join(insight_parts)

    return {
        "outlook": outlook,
        "sentiment": {
            "label": sentiment.get("overall_sentiment", "neutral"),
            "score": sentiment.get("sentiment_score", 0.0),
        },
        "insight": insight,
        "sources": list(gathered_data.keys()),
    }


def main(input_data: dict) -> dict:
    from shared.webpubsub_utils import send_progress
    from shared.llm_analysis_service import LLMAnalyzerFactory

    ticker = input_data["ticker"]
    task_id = input_data["task_id"]
    llm_config = input_data["llm_config"]

    try:
        send_progress(task_id, 55, "Running LLM analysis")

        analyzer = LLMAnalyzerFactory.create(
            provider=llm_config.get("provider"),
            api_key=llm_config.get("api_key"),
            model=llm_config.get("model"),
        )

        result = analyzer.analyze(ticker)

        if not result.get("success"):
            logger.error(f"LLM analysis unsuccessful for {ticker}: {result.get('error')}")
            return {
                "type": "llm_analysis",
                "status": "failed",
                "error": result.get("error", "LLM analysis failed"),
                "data": None,
            }

        send_progress(task_id, 75, "LLM analysis complete")
        logger.info(f"LLM analysis completed for {ticker}")

        return {
            "type": "llm_analysis",
            "status": "ok",
            "data": _normalize(result.get("analysis", {}), result.get("gathered_data", {})),
        }
    except Exception as e:
        logger.error(f"LLM analysis failed for {ticker}: {e}")
        return {
            "type": "llm_analysis",
            "status": "failed",
            "error": str(e),
            "data": None,
        }
