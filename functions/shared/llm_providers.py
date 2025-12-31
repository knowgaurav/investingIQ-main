"""Strategy pattern implementations for LLM providers."""
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.default_model
        self._client = self._create_client()
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model for this provider."""
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL for the provider API."""
        pass
    
    def _create_client(self) -> ChatOpenAI:
        """Create LangChain client for OpenAI-compatible APIs."""
        return ChatOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            temperature=0.7,
            max_tokens=2048,
        )
    
    def analyze_sentiment(self, headlines: list) -> dict:
        """Analyze sentiment of news headlines."""
        if not headlines:
            return self._empty_sentiment()
        
        headlines_text = "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])
        
        system_msg = SystemMessage(content=(
            "You are a financial sentiment analyst. Analyze news headlines and "
            "classify each as bullish, bearish, or neutral from an investor's perspective."
        ))
        
        human_msg = HumanMessage(content=f"""Analyze these headlines:

{headlines_text}

Return JSON only:
{{"results": [{{"headline": "...", "sentiment": "bullish|bearish|neutral", "confidence": 0.0-1.0, "reasoning": "..."}}]}}""")
        
        try:
            response = self._client.invoke([system_msg, human_msg])
            return self._parse_sentiment_response(response.content)
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return self._empty_sentiment(error=str(e))
    
    def generate_summary(self, articles: list, ticker: str) -> str:
        """Generate news summary for a stock."""
        if not articles:
            return f"No recent news articles found for {ticker}."
        
        articles_text = ""
        for i, article in enumerate(articles[:10], 1):
            articles_text += f"\n--- Article {i} ---\n"
            articles_text += f"Title: {article.get('title', 'N/A')}\n"
            articles_text += f"Description: {article.get('description', 'N/A')}\n"
        
        system_msg = SystemMessage(content=(
            "You are a financial news analyst. Summarize news articles "
            "highlighting key developments and market implications."
        ))
        
        human_msg = HumanMessage(content=f"""Summarize these news articles about {ticker}:

{articles_text}

Provide a 2-3 paragraph summary covering key events, market sentiment, and potential impact.""")
        
        try:
            response = self._client.invoke([system_msg, human_msg])
            return response.content
        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return f"Unable to generate summary for {ticker}."
    
    def generate_insights(
        self, 
        ticker: str, 
        stock_data: dict, 
        sentiment: dict, 
        summary: str
    ) -> str:
        """Generate AI investment insights."""
        system_msg = SystemMessage(content=(
            "You are InvestingIQ, an AI financial analyst. Generate comprehensive "
            "investment insights. Remind users this is not financial advice."
        ))
        
        stock_info = self._format_stock_data(stock_data)
        sentiment_info = self._format_sentiment(sentiment)
        
        human_msg = HumanMessage(content=f"""Generate insights for {ticker}:

## Stock Data
{stock_info}

## Sentiment
{sentiment_info}

## News Summary
{summary}

Cover: Current position, sentiment overview, key factors, considerations, and risks.""")
        
        try:
            response = self._client.invoke([system_msg, human_msg])
            return response.content
        except Exception as e:
            logger.error(f"Insights generation error: {e}")
            return f"Unable to generate insights for {ticker}."
    
    def _parse_sentiment_response(self, content: str) -> dict:
        """Parse LLM sentiment response."""
        try:
            text = content.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            
            parsed = json.loads(text)
            results = parsed.get("results", [])
            
            scores = {"bullish": 1, "bearish": -1, "neutral": 0}
            breakdown = {"positive": 0, "negative": 0, "neutral": 0}
            total_score = 0
            
            for r in results:
                sentiment = r.get("sentiment", "neutral").lower()
                total_score += scores.get(sentiment, 0)
                if sentiment == "bullish":
                    breakdown["positive"] += 1
                elif sentiment == "bearish":
                    breakdown["negative"] += 1
                else:
                    breakdown["neutral"] += 1
            
            overall_score = total_score / len(results) if results else 0
            
            return {
                "overall_score": overall_score,
                "breakdown": breakdown,
                "details": results,
            }
        except Exception as e:
            logger.error(f"Failed to parse sentiment: {e}")
            return self._empty_sentiment(error=str(e))
    
    def _empty_sentiment(self, error: str = None) -> dict:
        """Return empty sentiment result."""
        result = {
            "overall_score": 0.0,
            "breakdown": {"positive": 0, "negative": 0, "neutral": 0},
            "details": [],
        }
        if error:
            result["error"] = error
        return result
    
    def _format_stock_data(self, data: dict) -> str:
        """Format stock data for prompt."""
        if not data:
            return "No stock data available."
        
        lines = []
        if data.get("company_info", {}).get("name"):
            lines.append(f"- Company: {data['company_info']['name']}")
        if data.get("current_price"):
            lines.append(f"- Current Price: ${data['current_price']:.2f}")
        if data.get("company_info", {}).get("market_cap"):
            lines.append(f"- Market Cap: ${data['company_info']['market_cap']:,}")
        if data.get("company_info", {}).get("pe_ratio"):
            lines.append(f"- P/E Ratio: {data['company_info']['pe_ratio']:.2f}")
        
        return "\n".join(lines) if lines else "Limited data available."
    
    def _format_sentiment(self, data: dict) -> str:
        """Format sentiment data for prompt."""
        if not data:
            return "No sentiment data available."
        
        score = data.get("overall_score", 0)
        label = "Bullish" if score > 0.3 else "Bearish" if score < -0.3 else "Neutral"
        return f"Overall: {label} (score: {score:.2f})"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider implementation."""
    
    @property
    def default_model(self) -> str:
        return "gpt-4o-mini"
    
    @property
    def base_url(self) -> str:
        return "https://api.openai.com/v1"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic provider implementation."""
    
    @property
    def default_model(self) -> str:
        return "claude-haiku-4-5-latest"
    
    @property
    def base_url(self) -> str:
        return "https://api.anthropic.com/v1"
    
    def _create_client(self) -> ChatOpenAI:
        """Create Anthropic client via LangChain."""
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            api_key=self.api_key,
            model=self.model,
            temperature=0.7,
            max_tokens=2048,
        )


class GoogleProvider(BaseLLMProvider):
    """Google Gemini provider implementation."""
    
    @property
    def default_model(self) -> str:
        return "gemini-2.5-flash"
    
    @property
    def base_url(self) -> str:
        return "https://generativelanguage.googleapis.com/v1beta/openai"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter provider implementation."""
    
    @property
    def default_model(self) -> str:
        return "openai/gpt-4o-mini"
    
    @property
    def base_url(self) -> str:
        return "https://openrouter.ai/api/v1"


class MegaLLMProvider(BaseLLMProvider):
    """MegaLLM provider implementation."""
    
    @property
    def default_model(self) -> str:
        return "gpt-4o-mini"
    
    @property
    def base_url(self) -> str:
        return "https://api.megallm.com/v1"


class AgentRouterProvider(BaseLLMProvider):
    """AgentRouter provider implementation."""
    
    @property
    def default_model(self) -> str:
        return "gpt-4o-mini"
    
    @property
    def base_url(self) -> str:
        return "https://api.agentrouter.ai/v1"
