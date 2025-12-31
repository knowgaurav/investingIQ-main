"""Sentiment Analysis Service - wrapper around LLM service for sentiment operations."""
import logging
from typing import List, Optional

from app.services.llm_service import get_llm_service, LLMService

logger = logging.getLogger(__name__)


class SentimentService:
    """Service for sentiment analysis operations using LLM."""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize the sentiment service.
        
        Args:
            llm_service: Optional LLM service instance (uses singleton if not provided)
        """
        self._llm_service = llm_service or get_llm_service()
    
    def analyze_headlines(self, headlines: List[str]) -> List[dict]:
        """
        Analyze sentiment of news headlines.
        
        Args:
            headlines: List of news headlines
            
        Returns:
            List of sentiment analysis results
        """
        return self._llm_service.analyze_sentiment(headlines)
    
    def analyze_articles(self, articles: List[dict]) -> dict:
        """
        Analyze sentiment of news articles and compute aggregate scores.
        
        Args:
            articles: List of article dicts with 'title' key
            
        Returns:
            dict with sentiment_score, sentiment_breakdown, and details
        """
        if not articles:
            return {
                "sentiment_score": 0.0,
                "sentiment_breakdown": {"bullish": 0, "bearish": 0, "neutral": 0},
                "details": [],
                "status": "no_articles"
            }
        
        try:
            # Extract headlines from articles
            headlines = [
                article.get("title", "") 
                for article in articles 
                if article.get("title")
            ]
            
            if not headlines:
                return {
                    "sentiment_score": 0.0,
                    "sentiment_breakdown": {"bullish": 0, "bearish": 0, "neutral": 0},
                    "details": [],
                    "status": "no_headlines"
                }
            
            # Analyze sentiment
            sentiment_results = self._llm_service.analyze_sentiment(headlines)
            
            # Compute aggregate metrics
            breakdown = {"bullish": 0, "bearish": 0, "neutral": 0}
            total_score = 0.0
            
            for result in sentiment_results:
                sentiment = result.get("sentiment", "neutral").lower()
                confidence = result.get("confidence", 0.5)
                
                if sentiment in breakdown:
                    breakdown[sentiment] += 1
                else:
                    breakdown["neutral"] += 1
                
                # Calculate weighted score (-1 to 1)
                if sentiment == "bullish":
                    total_score += confidence
                elif sentiment == "bearish":
                    total_score -= confidence
                # neutral contributes 0
            
            # Normalize score
            num_results = len(sentiment_results)
            sentiment_score = total_score / num_results if num_results > 0 else 0.0
            
            return {
                "sentiment_score": round(sentiment_score, 3),
                "sentiment_breakdown": breakdown,
                "details": sentiment_results,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Article sentiment analysis error: {e}")
            return {
                "sentiment_score": 0.0,
                "sentiment_breakdown": {"bullish": 0, "bearish": 0, "neutral": 0},
                "details": [],
                "status": "error",
                "error": str(e)
            }
    
    def get_sentiment_label(self, score: float) -> str:
        """
        Convert sentiment score to human-readable label.
        
        Args:
            score: Sentiment score (-1 to 1)
            
        Returns:
            Sentiment label string
        """
        if score > 0.5:
            return "Very Bullish"
        elif score > 0.2:
            return "Bullish"
        elif score > -0.2:
            return "Neutral"
        elif score > -0.5:
            return "Bearish"
        else:
            return "Very Bearish"


# Singleton instance
_sentiment_service: Optional[SentimentService] = None


def get_sentiment_service() -> SentimentService:
    """Get or create the sentiment service singleton."""
    global _sentiment_service
    if _sentiment_service is None:
        _sentiment_service = SentimentService()
    return _sentiment_service
