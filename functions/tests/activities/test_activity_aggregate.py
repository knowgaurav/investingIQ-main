"""Tests for activity_aggregate function."""
from unittest.mock import patch

import shared.db_utils as db_utils
import shared.webpubsub_utils as webpubsub_utils
import activity_aggregate


class TestActivityAggregate:
    """Tests for the aggregate activity function."""

    def test_aggregates_results_and_builds_comparison(self):
        """Aggregates ML/LLM/financials and builds a dual_comparison when both signals exist."""
        input_data = {
            "ticker": "AAPL",
            "task_id": "test-123",
            "stock_data": {
                "price_history": [{"date": "2024-01-01", "close": 150.0}],
                "company_info": {"name": "Apple Inc."},
            },
            "news_data": [{"title": "Apple news"}, {"title": "Tech news"}],
            "analysis_results": [
                {"type": "ml_analysis", "status": "ok", "data": {"prediction": {"trend": "upward"}, "technical": {"rsi": 55}}},
                {"type": "llm_analysis", "status": "ok", "data": {"outlook": "bullish", "sentiment": {"label": "positive", "score": 0.7}}},
                {"type": "financials_ingest", "status": "ok", "fiscal_quarter": "2024-12-31"},
            ],
            "llm_enabled": True,
        }

        with patch.object(db_utils, 'save_analysis_report', return_value=True) as mock_save, \
             patch.object(webpubsub_utils, 'send_progress') as mock_progress:
            result = activity_aggregate.main(input_data)

            assert result["ticker"] == "AAPL"
            assert result["news_count"] == 2
            assert result["ml_status"] == "ok"
            assert result["llm_status"] == "ok"
            assert result["financials_status"] == "ok"
            assert result["financials_quarter"] == "2024-12-31"
            assert result["dual_comparison"] == {
                "ml_signal": "bullish",
                "llm_signal": "bullish",
                "agreement": True,
            }
            mock_save.assert_called_once()
            assert mock_progress.call_count == 2

    def test_ml_only_has_no_comparison(self):
        """ML-only analysis omits dual_comparison and marks LLM not run."""
        input_data = {
            "ticker": "MSFT",
            "task_id": "test-456",
            "stock_data": {"price_history": [], "company_info": {}},
            "news_data": [],
            "analysis_results": [
                {"type": "ml_analysis", "status": "ok", "data": {"prediction": {"trend": "sideways"}}},
                {"type": "financials_ingest", "status": "reused", "fiscal_quarter": "2024-09-30"},
            ],
            "llm_enabled": False,
        }

        with patch.object(db_utils, 'save_analysis_report', return_value=True), \
             patch.object(webpubsub_utils, 'send_progress'):
            result = activity_aggregate.main(input_data)

            assert result["llm_status"] == "not_run"
            assert result["llm_analysis"] is None
            assert result["dual_comparison"] is None
            assert result["financials_status"] == "reused"

    def test_disagreement_flagged(self):
        """When ML and LLM signals differ, agreement is False."""
        input_data = {
            "ticker": "TSLA",
            "task_id": "test-789",
            "stock_data": {"price_history": [], "company_info": {}},
            "news_data": [],
            "analysis_results": [
                {"type": "ml_analysis", "status": "ok", "data": {"prediction": {"trend": "downward"}}},
                {"type": "llm_analysis", "status": "ok", "data": {"outlook": "bullish"}},
            ],
            "llm_enabled": True,
        }

        with patch.object(db_utils, 'save_analysis_report', return_value=True), \
             patch.object(webpubsub_utils, 'send_progress'):
            result = activity_aggregate.main(input_data)

            assert result["dual_comparison"] == {
                "ml_signal": "bearish",
                "llm_signal": "bullish",
                "agreement": False,
            }
