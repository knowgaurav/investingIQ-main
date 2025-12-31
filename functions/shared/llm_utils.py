"""LLM utilities for Azure Functions."""
import json
import logging
from openai import OpenAI

from shared.config import get_settings

logger = logging.getLogger(__name__)

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        _client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
    return _client


def analyze_sentiment_batch(headlines: list) -> list:
    """Analyze sentiment of headlines."""
    if not headlines:
        return []
    
    client = get_client()
    settings = get_settings()
    headlines_text = "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])
    
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "Analyze sentiment of each headline. Return JSON with results array containing {headline, sentiment (bullish/bearish/neutral), confidence, reasoning}."},
                {"role": "user", "content": f"Headlines:\n{headlines_text}\n\nRespond only with valid JSON."}
            ],
            max_tokens=2000
        )
        
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:-1])
        
        parsed = json.loads(text)
        return parsed.get("results", [])
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return [{"headline": h, "sentiment": "neutral", "confidence": 0.5, "reasoning": "Error"} for h in headlines]


def summarize_news(articles: list, ticker: str) -> str:
    """Summarize news articles."""
    if not articles:
        return f"No recent news found for {ticker}."
    
    client = get_client()
    settings = get_settings()
    headlines = "\n".join([f"- {a.get('title', '')}" for a in articles[:10]])
    
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "You are a financial analyst. Summarize the news concisely."},
                {"role": "user", "content": f"Summarize these {ticker} headlines:\n{headlines}"}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Summary failed: {e}")
        return f"Unable to generate summary for {ticker}."


def generate_insights(ticker: str, stock_data: dict, sentiment: dict, summary: str) -> str:
    """Generate AI insights."""
    client = get_client()
    settings = get_settings()
    
    price = stock_data.get("current_price", "N/A")
    company = stock_data.get("company_info", {}).get("name", ticker)
    
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "You are a financial analyst. Provide investment insights."},
                {"role": "user", "content": f"Provide insights for {company} ({ticker}) trading at ${price}."}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Insights failed: {e}")
        return f"Unable to generate insights for {ticker}."
