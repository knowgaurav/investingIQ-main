"""Tests for activity_fetch_data function."""
import pytest
from unittest.mock import patch, MagicMock


class TestActivityFetchData:
    """Tests for the fetch data activity function."""
    
    def test_main_fetches_stock_data_and_news(self):
        """Test main function fetches stock data and news."""
        mock_stock_data = {
            "ticker": "AAPL",
            "price_history": [{"date": "2024-01-01", "close": 150.0}],
            "current_price": 150.0,
            "company_info": {"name": "Apple Inc."}
        }
        mock_earnings = {"annual_earnings": [], "quarterly_earnings": []}
        mock_news = [{"title": "Apple news", "summary": "Test"}]
        
        with patch('shared.alpha_vantage.fetch_stock_data', return_value=mock_stock_data) as mock_fetch_stock, \
             patch('shared.alpha_vantage.fetch_earnings', return_value=mock_earnings) as mock_fetch_earnings, \
             patch('shared.alpha_vantage.fetch_news', return_value=mock_news) as mock_fetch_news, \
             patch('shared.webpubsub_utils.send_progress') as mock_progress:
            
            from activity_fetch_data import main
            
            result = main({"ticker": "AAPL", "task_id": "test-123"})
            
            mock_fetch_stock.assert_called_once_with("AAPL", api_key=None)
            mock_fetch_earnings.assert_called_once_with("AAPL", api_key=None)
            mock_fetch_news.assert_called_once_with("AAPL", limit=20, api_key=None)
            
            assert result["stock_data"]["ticker"] == "AAPL"
            assert result["stock_data"]["earnings"] == mock_earnings
            assert result["news_data"] == mock_news
            assert mock_progress.call_count == 3
    
    def test_main_with_empty_price_history(self):
        """Test main handles empty price history."""
        mock_stock_data = {
            "ticker": "INVALID",
            "price_history": [],
            "current_price": None,
            "company_info": {}
        }
        
        with patch('shared.alpha_vantage.fetch_stock_data', return_value=mock_stock_data), \
             patch('shared.alpha_vantage.fetch_earnings', return_value={}), \
             patch('shared.alpha_vantage.fetch_news', return_value=[]), \
             patch('shared.webpubsub_utils.send_progress'):
            
            from activity_fetch_data import main
            
            result = main({"ticker": "INVALID", "task_id": "test-456"})
            
            assert result["stock_data"]["price_history"] == []
            assert result["news_data"] == []
