"""Tests for activity_ml_analysis function."""
from unittest.mock import patch

import shared.ml_models as ml_models
import shared.webpubsub_utils as webpubsub_utils
import activity_ml_analysis


class TestActivityMLAnalysis:
    """Tests for the ML analysis activity function."""

    def test_main_runs_all_ml_models(self):
        """Test main function runs prediction, technical, and sentiment models."""
        mock_prediction = {"forecast_30d": 160.0, "trend": "upward"}
        mock_technical = {"rsi": 55, "macd_signal": "bullish"}
        mock_sentiment = {"overall_score": 0.6, "label": "positive"}

        input_data = {
            "ticker": "AAPL",
            "task_id": "test-123",
            "stock_data": {
                "price_history": [
                    {"date": "2024-01-01", "close": 150.0},
                    {"date": "2024-01-02", "close": 152.0},
                ]
            },
            "news_data": [
                {"title": "Apple reports strong earnings"},
                {"title": "Tech sector outlook positive"},
            ],
        }

        with patch.object(ml_models, 'ml_prediction', return_value=mock_prediction) as mock_pred, \
             patch.object(ml_models, 'ml_technical', return_value=mock_technical) as mock_tech, \
             patch.object(ml_models, 'ml_sentiment', return_value=mock_sentiment) as mock_sent, \
             patch.object(webpubsub_utils, 'send_progress') as mock_progress:
            result = activity_ml_analysis.main(input_data)

            mock_pred.assert_called_with(input_data["stock_data"]["price_history"])
            mock_tech.assert_called_with(input_data["stock_data"]["price_history"])
            mock_sent.assert_called()

            assert result["type"] == "ml_analysis"
            assert result["status"] == "ok"
            assert result["data"]["prediction"] == mock_prediction
            assert result["data"]["technical"] == mock_technical
            assert result["data"]["sentiment"] == mock_sentiment
            assert mock_progress.call_count == 3

    def test_main_with_empty_data(self):
        """Test main handles empty price history and news."""
        input_data = {
            "ticker": "TEST",
            "task_id": "test-456",
            "stock_data": {"price_history": []},
            "news_data": [],
        }

        with patch.object(ml_models, 'ml_prediction', return_value={}) as mock_pred, \
             patch.object(ml_models, 'ml_technical', return_value={}) as mock_tech, \
             patch.object(ml_models, 'ml_sentiment', return_value={}) as mock_sent, \
             patch.object(webpubsub_utils, 'send_progress'):
            result = activity_ml_analysis.main(input_data)

            mock_pred.assert_called_with([])
            mock_tech.assert_called_with([])
            mock_sent.assert_called_with([])
            assert result["type"] == "ml_analysis"
            assert result["status"] == "ok"

    def test_main_returns_failed_on_exception(self):
        """Exceptions during ML analysis are caught and returned as failed status."""
        input_data = {
            "ticker": "ERR",
            "task_id": "test-789",
            "stock_data": {"price_history": []},
            "news_data": [],
        }

        with patch.object(ml_models, 'ml_prediction', side_effect=RuntimeError("boom")), \
             patch.object(webpubsub_utils, 'send_progress'):
            result = activity_ml_analysis.main(input_data)

            assert result["type"] == "ml_analysis"
            assert result["status"] == "failed"
            assert result["data"] is None
