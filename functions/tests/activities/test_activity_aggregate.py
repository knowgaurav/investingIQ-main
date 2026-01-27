"""Tests for activity_aggregate function."""
import sys
import pytest
from unittest.mock import patch, MagicMock


# Create mock database module since it may not exist
mock_database = MagicMock()
sys.modules['shared.database'] = mock_database


class TestActivityAggregate:
    """Tests for the aggregate activity function."""
    
    def test_main_aggregates_results_correctly(self):
        """Test main function aggregates ML and LLM results."""
        mock_database.save_analysis_report.return_value = True
        
        input_data = {
            "ticker": "AAPL",
            "task_id": "test-123",
            "stock_data": {
                "price_history": [{"date": "2024-01-01", "close": 150.0}],
                "company_info": {"name": "Apple Inc."}
            },
            "news_data": [{"title": "Apple news"}, {"title": "Tech news"}],
            "analysis_results": [
                {
                    "type": "ml_analysis",
                    "data": {"prediction": {"target": 160.0}, "technical": {"rsi": 55}}
                },
                {
                    "type": "llm_analysis",
                    "data": {"recommendation": "Buy", "analysis": {}}
                }
            ],
            "llm_enabled": True
        }
        
        with patch('shared.webpubsub_utils.send_progress') as mock_progress:
            import importlib
            import activity_aggregate
            importlib.reload(activity_aggregate)
            
            result = activity_aggregate.main(input_data)
            
            assert result["ticker"] == "AAPL"
            assert result["task_id"] == "test-123"
            assert result["news_count"] == 2
            assert result["ml_analysis"]["prediction"]["target"] == 160.0
            assert result["llm_analysis"]["recommendation"] == "Buy"
            assert "timestamp" in result
            
            mock_database.save_analysis_report.assert_called_once()
            assert mock_progress.call_count == 2
    
    def test_main_with_ml_only(self):
        """Test main handles ML-only analysis (no LLM)."""
        mock_database.save_analysis_report.return_value = True
        
        input_data = {
            "ticker": "MSFT",
            "task_id": "test-456",
            "stock_data": {"price_history": []},
            "news_data": [],
            "analysis_results": [
                {"type": "ml_analysis", "data": {"technical": {"trend": "up"}}}
            ],
            "llm_enabled": False
        }
        
        with patch('shared.webpubsub_utils.send_progress'):
            import importlib
            import activity_aggregate
            importlib.reload(activity_aggregate)
            
            result = activity_aggregate.main(input_data)
            
            assert result["ticker"] == "MSFT"
            assert result["ml_analysis"]["technical"]["trend"] == "up"
            assert result["llm_analysis"] is None
            assert result["news_count"] == 0
