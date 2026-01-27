"""Tests for activity_ml_analysis function."""
import sys
import pytest
from unittest.mock import patch, MagicMock


# Create mock ml_models module since it doesn't exist yet
mock_ml_models = MagicMock()
sys.modules['shared.ml_models'] = mock_ml_models


class TestActivityMLAnalysis:
    """Tests for the ML analysis activity function."""
    
    def test_main_runs_all_ml_models(self):
        """Test main function runs prediction, technical, and sentiment models."""
        mock_prediction = {"forecast": [155.0, 160.0], "confidence": 0.8}
        mock_technical = {"rsi": 55, "macd": "bullish", "trend": "up"}
        mock_sentiment = {"score": 0.6, "label": "positive"}
        
        mock_ml_models.ml_prediction.return_value = mock_prediction
        mock_ml_models.ml_technical.return_value = mock_technical
        mock_ml_models.ml_sentiment.return_value = mock_sentiment
        
        input_data = {
            "ticker": "AAPL",
            "task_id": "test-123",
            "stock_data": {
                "price_history": [
                    {"date": "2024-01-01", "close": 150.0},
                    {"date": "2024-01-02", "close": 152.0}
                ]
            },
            "news_data": [
                {"title": "Apple reports strong earnings"},
                {"title": "Tech sector outlook positive"}
            ]
        }
        
        with patch('shared.webpubsub_utils.send_progress') as mock_progress:
            # Need to reimport to pick up the mocked module
            import importlib
            import activity_ml_analysis
            importlib.reload(activity_ml_analysis)
            
            result = activity_ml_analysis.main(input_data)
            
            mock_ml_models.ml_prediction.assert_called_with(input_data["stock_data"]["price_history"])
            mock_ml_models.ml_technical.assert_called_with(input_data["stock_data"]["price_history"])
            mock_ml_models.ml_sentiment.assert_called()
            
            assert result["type"] == "ml_analysis"
            assert result["data"]["prediction"] == mock_prediction
            assert result["data"]["technical"] == mock_technical
            assert result["data"]["sentiment"] == mock_sentiment
            assert mock_progress.call_count == 3
    
    def test_main_with_empty_data(self):
        """Test main handles empty price history and news."""
        mock_ml_models.ml_prediction.return_value = {}
        mock_ml_models.ml_technical.return_value = {}
        mock_ml_models.ml_sentiment.return_value = {}
        
        input_data = {
            "ticker": "TEST",
            "task_id": "test-456",
            "stock_data": {"price_history": []},
            "news_data": []
        }
        
        with patch('shared.webpubsub_utils.send_progress'):
            import importlib
            import activity_ml_analysis
            importlib.reload(activity_ml_analysis)
            
            result = activity_ml_analysis.main(input_data)
            
            mock_ml_models.ml_prediction.assert_called_with([])
            mock_ml_models.ml_technical.assert_called_with([])
            mock_ml_models.ml_sentiment.assert_called_with([])
            
            assert result["type"] == "ml_analysis"
