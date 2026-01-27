"""Tests for activity_cache_data function."""
import pytest
from unittest.mock import patch, MagicMock


class TestActivityCacheData:
    """Tests for the cache data activity function."""
    
    def test_main_caches_all_data_types(self):
        """Test main function caches prices, company info, earnings, and news."""
        mock_cache = MagicMock()
        
        input_data = {
            "ticker": "AAPL",
            "stock_data": {
                "price_history": [{"date": "2024-01-01", "close": 150.0}],
                "company_info": {"name": "Apple Inc.", "sector": "Technology"},
                "earnings": {"annual_earnings": [], "quarterly_earnings": []}
            },
            "news_data": [{"title": "Apple news"}]
        }
        
        with patch('shared.cache.get_stock_cache', return_value=mock_cache):
            from activity_cache_data import main
            
            result = main(input_data)
            
            mock_cache.set_prices.assert_called_once_with("AAPL", input_data["stock_data"]["price_history"])
            mock_cache.set_company_info.assert_called_once_with("AAPL", input_data["stock_data"]["company_info"])
            mock_cache.set_earnings.assert_called_once_with("AAPL", input_data["stock_data"]["earnings"])
            mock_cache.set_news.assert_called_once_with("AAPL", input_data["news_data"])
            assert result is True
    
    def test_main_skips_empty_company_info(self):
        """Test main skips caching when company_info is empty."""
        mock_cache = MagicMock()
        
        input_data = {
            "ticker": "TEST",
            "stock_data": {
                "price_history": [],
                "company_info": None,
                "earnings": None
            },
            "news_data": []
        }
        
        with patch('shared.cache.get_stock_cache', return_value=mock_cache):
            from activity_cache_data import main
            
            result = main(input_data)
            
            mock_cache.set_prices.assert_called_once()
            mock_cache.set_company_info.assert_not_called()
            mock_cache.set_earnings.assert_not_called()
            mock_cache.set_news.assert_called_once()
            assert result is True
