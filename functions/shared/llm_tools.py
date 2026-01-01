"""LLM Tool Functions for retrieving stock data from Redis cache.

These tools follow the OpenAI function calling specification and can be used
with any OpenAI-compatible LLM provider.
"""
import json
import logging
from typing import Any
from dataclasses import dataclass

from .cache import get_stock_cache, StockCache

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    data: Any
    error: str = None


class StockDataTools:
    """Tool functions for retrieving stock data from Redis cache."""
    
    def __init__(self, cache: StockCache = None):
        self._cache = cache or get_stock_cache()
    
    def get_stock_prices(self, ticker: str) -> ToolResult:
        """Retrieve historical price data for a stock."""
        try:
            data = self._cache.get_prices(ticker.upper())
            if data:
                return ToolResult(success=True, data=data)
            return ToolResult(success=False, data=None, error=f"No price data found for {ticker}")
        except Exception as e:
            logger.error(f"Error fetching prices for {ticker}: {e}")
            return ToolResult(success=False, data=None, error=str(e))
    
    def get_company_info(self, ticker: str) -> ToolResult:
        """Retrieve company information and fundamentals."""
        try:
            data = self._cache.get_company_info(ticker.upper())
            if data:
                return ToolResult(success=True, data=data)
            return ToolResult(success=False, data=None, error=f"No company info found for {ticker}")
        except Exception as e:
            logger.error(f"Error fetching company info for {ticker}: {e}")
            return ToolResult(success=False, data=None, error=str(e))
    
    def get_news_articles(self, ticker: str) -> ToolResult:
        """Retrieve recent news articles for a stock."""
        try:
            data = self._cache.get_news(ticker.upper())
            if data:
                return ToolResult(success=True, data=data)
            return ToolResult(success=False, data=None, error=f"No news found for {ticker}")
        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")
            return ToolResult(success=False, data=None, error=str(e))
    
    def get_earnings_data(self, ticker: str) -> ToolResult:
        """Retrieve earnings history and estimates."""
        try:
            data = self._cache.get_earnings(ticker.upper())
            if data:
                return ToolResult(success=True, data=data)
            return ToolResult(success=False, data=None, error=f"No earnings data found for {ticker}")
        except Exception as e:
            logger.error(f"Error fetching earnings for {ticker}: {e}")
            return ToolResult(success=False, data=None, error=str(e))
    
    def execute_tool(self, tool_name: str, arguments: dict) -> ToolResult:
        """Execute a tool by name with given arguments."""
        tool_map = {
            "get_stock_prices": self.get_stock_prices,
            "get_company_info": self.get_company_info,
            "get_news_articles": self.get_news_articles,
            "get_earnings_data": self.get_earnings_data,
        }
        
        if tool_name not in tool_map:
            return ToolResult(success=False, data=None, error=f"Unknown tool: {tool_name}")
        
        return tool_map[tool_name](**arguments)


# OpenAI-compatible tool definitions
STOCK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_prices",
            "description": "Retrieve historical price data including open, high, low, close, and volume for a stock ticker. Use this to analyze price trends, calculate returns, and identify patterns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, GOOGL, MSFT)"
                    }
                },
                "required": ["ticker"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_info",
            "description": "Retrieve company fundamentals including market cap, P/E ratio, sector, industry, and other key metrics. Use this for fundamental analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, GOOGL, MSFT)"
                    }
                },
                "required": ["ticker"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_news_articles",
            "description": "Retrieve recent news articles and headlines for a stock. Use this to understand market sentiment and recent events affecting the stock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, GOOGL, MSFT)"
                    }
                },
                "required": ["ticker"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_earnings_data",
            "description": "Retrieve earnings history, EPS data, and analyst estimates. Use this to assess earnings growth and company performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, GOOGL, MSFT)"
                    }
                },
                "required": ["ticker"]
            }
        }
    }
]


def get_tool_definitions() -> list:
    """Get OpenAI-compatible tool definitions."""
    return STOCK_TOOLS
