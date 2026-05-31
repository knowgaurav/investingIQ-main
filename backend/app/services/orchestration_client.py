"""Client for starting the Azure Durable Functions analysis orchestration over HTTP."""
import logging
from typing import Any, Dict, Optional

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)


class OrchestrationClient:
    """Starts the Azure Durable orchestration via its HTTP starter."""

    def __init__(self):
        settings = get_settings()
        self._starter_url = settings.functions_orchestrator_url
        self._functions_key = settings.functions_key

    def start_analysis(
        self,
        ticker: str,
        task_id: str,
        llm_config: Optional[Dict[str, Any]],
        alpha_vantage_key: Optional[str] = None,
    ) -> None:
        """Start the analysis orchestration for a ticker.

        Args:
            ticker: Stock ticker symbol.
            task_id: UUID tracking the analysis task.
            llm_config: Optional LLM provider configuration.
            alpha_vantage_key: Optional user-provided Alpha Vantage API key.
        """
        params = {"code": self._functions_key} if self._functions_key else None
        response = requests.post(
            self._starter_url,
            params=params,
            json={
                "ticker": ticker,
                "task_id": task_id,
                "llm_config": llm_config,
                "alpha_vantage_key": alpha_vantage_key,
            },
            timeout=15,
        )
        response.raise_for_status()
        logger.info(f"Started orchestration for {ticker}, task_id: {task_id}")


_orchestration_client: Optional[OrchestrationClient] = None


def get_orchestration_client() -> OrchestrationClient:
    """Get or create the orchestration client singleton."""
    global _orchestration_client
    if _orchestration_client is None:
        _orchestration_client = OrchestrationClient()
    return _orchestration_client
