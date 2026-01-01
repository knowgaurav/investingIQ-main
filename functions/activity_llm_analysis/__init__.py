"""Activity: Run LLM-based analysis with tool calling."""
import logging

logger = logging.getLogger(__name__)


def main(input_data: dict) -> dict:
    from shared.webpubsub_utils import send_progress
    from shared.llm_analysis_service import LLMAnalyzerFactory
    
    ticker = input_data["ticker"]
    task_id = input_data["task_id"]
    llm_config = input_data["llm_config"]
    
    send_progress(task_id, 55, "Running LLM analysis")
    
    analyzer = LLMAnalyzerFactory.create(
        provider=llm_config.get("provider"),
        api_key=llm_config.get("api_key"),
        model=llm_config.get("model"),
    )
    
    result = analyzer.analyze(ticker)
    
    send_progress(task_id, 75, "LLM analysis complete")
    logger.info(f"LLM analysis completed for {ticker}")
    
    return {
        "type": "llm_analysis",
        "data": result,
    }
