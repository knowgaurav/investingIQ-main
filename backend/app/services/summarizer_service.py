"""Summarizer Service - wrapper around LLM service for summarization operations."""
import logging
from typing import List, Optional

from app.services.llm_service import get_llm_service, LLMService

logger = logging.getLogger(__name__)


class SummarizerService:
    """Service for news summarization operations using LLM."""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize the summarizer service.
        
        Args:
            llm_service: Optional LLM service instance (uses singleton if not provided)
        """
        self._llm_service = llm_service or get_llm_service()
    
    def summarize_news(self, articles: List[dict], ticker: str) -> str:
        """
        Summarize news articles for a stock ticker.
        
        Args:
            articles: List of article dicts
            ticker: Stock ticker symbol
            
        Returns:
            Summary string
        """
        return self._llm_service.summarize_news(articles, ticker)
    
    def summarize_with_metadata(self, articles: List[dict], ticker: str) -> dict:
        """
        Summarize news articles and return with metadata.
        
        Args:
            articles: List of article dicts
            ticker: Stock ticker symbol
            
        Returns:
            dict with summary, article_count, and status
        """
        if not articles:
            return {
                "summary": f"No recent news articles found for {ticker}.",
                "article_count": 0,
                "ticker": ticker,
                "status": "no_articles"
            }
        
        try:
            summary = self._llm_service.summarize_news(articles, ticker)
            
            return {
                "summary": summary,
                "article_count": len(articles),
                "ticker": ticker,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"News summarization error for {ticker}: {e}")
            return {
                "summary": f"Unable to generate summary for {ticker}.",
                "article_count": len(articles),
                "ticker": ticker,
                "status": "error",
                "error": str(e)
            }
    
    def generate_brief_summary(self, articles: List[dict], ticker: str, max_sentences: int = 3) -> str:
        """
        Generate a brief summary of news articles.
        
        Args:
            articles: List of article dicts
            ticker: Stock ticker symbol
            max_sentences: Maximum number of sentences in summary
            
        Returns:
            Brief summary string
        """
        if not articles:
            return f"No recent news for {ticker}."
        
        try:
            # Get full summary first
            full_summary = self._llm_service.summarize_news(articles, ticker)
            
            # Extract first few sentences
            sentences = full_summary.replace('\n', ' ').split('. ')
            brief = '. '.join(sentences[:max_sentences])
            
            if not brief.endswith('.'):
                brief += '.'
            
            return brief
            
        except Exception as e:
            logger.error(f"Brief summary generation error for {ticker}: {e}")
            return f"Unable to generate summary for {ticker}."


# Singleton instance
_summarizer_service: Optional[SummarizerService] = None


def get_summarizer_service() -> SummarizerService:
    """Get or create the summarizer service singleton."""
    global _summarizer_service
    if _summarizer_service is None:
        _summarizer_service = SummarizerService()
    return _summarizer_service
