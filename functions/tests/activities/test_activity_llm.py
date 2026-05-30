"""Tests for activity_llm_analysis function."""
import pytest
from unittest.mock import patch, MagicMock


def _analysis_payload():
    return {
        "success": True,
        "analysis": {
            "ticker": "AAPL",
            "technical": {"trend": "bullish"},
            "sentiment": {"overall_sentiment": "positive", "sentiment_score": 0.7, "news_summary": "Strong quarter."},
            "recommendation": {"action": "buy", "key_reasons": ["Revenue growth", "Margin expansion"]},
        },
        "gathered_data": {"get_stock_prices": {}, "get_company_info": {}},
    }


class TestActivityLLMAnalysis:
    """Tests for the LLM analysis activity function."""

    def test_main_normalizes_analysis_output(self):
        """Main returns the dual-analysis shape with outlook, sentiment, insight."""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = _analysis_payload()

        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_analyzer

        input_data = {
            "ticker": "AAPL",
            "task_id": "test-123",
            "llm_config": {"provider": "openai", "api_key": "test-key", "model": "gpt-4o-mini"},
        }

        with patch('shared.llm_analysis_service.LLMAnalyzerFactory', mock_factory), \
             patch('shared.webpubsub_utils.send_progress') as mock_progress:
            from activity_llm_analysis import main

            result = main(input_data)

            mock_factory.create.assert_called_once_with(
                provider="openai", api_key="test-key", model="gpt-4o-mini"
            )
            mock_analyzer.analyze.assert_called_once_with("AAPL")

            assert result["type"] == "llm_analysis"
            assert result["status"] == "ok"
            assert result["data"]["outlook"] == "bullish"
            assert result["data"]["sentiment"]["label"] == "positive"
            assert result["data"]["sentiment"]["score"] == 0.7
            assert "Revenue growth" in result["data"]["insight"]
            assert mock_progress.call_count == 2

    def test_main_marks_failed_on_unsuccessful_analysis(self):
        """An unsuccessful analyzer result yields status='failed'."""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = {"success": False, "error": "boom"}

        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_analyzer

        input_data = {
            "ticker": "MSFT",
            "task_id": "test-456",
            "llm_config": {"provider": "anthropic", "api_key": "k", "model": "claude-haiku-4-5"},
        }

        with patch('shared.llm_analysis_service.LLMAnalyzerFactory', mock_factory), \
             patch('shared.webpubsub_utils.send_progress'):
            from activity_llm_analysis import main

            result = main(input_data)

            assert result["type"] == "llm_analysis"
            assert result["status"] == "failed"
            assert result["data"] is None

    def test_main_never_raises_on_exception(self):
        """Analyzer exceptions are caught and returned as failed status."""
        mock_factory = MagicMock()
        mock_factory.create.side_effect = RuntimeError("provider down")

        input_data = {
            "ticker": "NVDA",
            "task_id": "test-789",
            "llm_config": {"provider": "openai", "api_key": "k", "model": "gpt-4o-mini"},
        }

        with patch('shared.llm_analysis_service.LLMAnalyzerFactory', mock_factory), \
             patch('shared.webpubsub_utils.send_progress'):
            from activity_llm_analysis import main

            result = main(input_data)

            assert result["status"] == "failed"
            assert "provider down" in result["error"]
