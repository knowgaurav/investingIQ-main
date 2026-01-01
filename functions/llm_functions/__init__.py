"""LLM processing Azure Functions - handles sentiment, summary, and insights."""
import json
import logging
from datetime import datetime

import azure.functions as func

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(msg: func.ServiceBusMessage):
    """
    Process LLM queue messages using user-provided API key.
    
    Triggered by: llm-queue
    Outputs to: aggregate-queue
    
    IMPORTANT: Only processes if llm_config is present in message.
    Uses Factory pattern to create provider based on user's config.
    """
    from shared.webpubsub_utils import send_progress
    from shared.llm_factory import LLMProviderFactory
    from azure.servicebus import ServiceBusClient, ServiceBusMessage as SBMessage
    from shared.config import get_settings
    
    try:
        message = json.loads(msg.get_body().decode('utf-8'))
        
        task_type = message.get("task_type")
        task_id = message.get("task_id")
        ticker = message.get("ticker")
        data = message.get("data", {})
        llm_config = message.get("llm_config")
        
        if not llm_config:
            logger.info(f"No LLM config for {task_id}, skipping LLM processing")
            return
        
        logger.info(f"Processing {task_type} for {ticker} with {llm_config.get('provider')}")
        send_progress(task_id, 50, f"Running {task_type.replace('_', ' ')} (LLM)")
        
        provider = LLMProviderFactory.create(
            provider=llm_config.get("provider"),
            api_key=llm_config.get("api_key"),
            model=llm_config.get("model"),
        )
        
        settings = get_settings()
        messages_to_send = []
        
        if task_type == "analyze_sentiment":
            headlines = data.get("headlines", [])
            sentiment_result = provider.analyze_sentiment(headlines)
            summary_result = provider.generate_summary(headlines, ticker)
            
            # Also generate insights in same call (combines all analysis)
            insights_result = provider.generate_insights(
                ticker=ticker,
                stock_data=data.get("stock_data", {}),
                sentiment=sentiment_result,
                summary=summary_result,
            )
            
            messages_to_send = [
                {"task_type": "llm_sentiment_ready", "task_id": task_id, "ticker": ticker, 
                 "data": sentiment_result, "timestamp": datetime.utcnow().isoformat()},
                {"task_type": "llm_summary_ready", "task_id": task_id, "ticker": ticker,
                 "data": summary_result, "timestamp": datetime.utcnow().isoformat()},
                {"task_type": "llm_insights_ready", "task_id": task_id, "ticker": ticker,
                 "data": insights_result, "timestamp": datetime.utcnow().isoformat()},
            ]
            
        elif task_type == "generate_insights":
            result = provider.generate_insights(
                ticker=ticker,
                stock_data=data.get("stock_data", {}),
                sentiment=data.get("sentiment", {}),
                summary=data.get("summary", ""),
            )
            messages_to_send = [
                {"task_type": "llm_insights_ready", "task_id": task_id, "ticker": ticker,
                 "data": result, "timestamp": datetime.utcnow().isoformat()},
            ]
        else:
            logger.error(f"Unknown task type: {task_type}")
            return
        
        with ServiceBusClient.from_connection_string(settings.servicebus_connection) as client:
            with client.get_queue_sender("aggregate-queue") as sender:
                for msg_data in messages_to_send:
                    sender.send_messages(SBMessage(json.dumps(msg_data)))
                    logger.info(f"Sent {msg_data['task_type']} to aggregate-queue")
        
        logger.info(f"Completed {task_type} for {ticker}")
        
    except Exception as e:
        logger.error(f"Error processing LLM message: {e}")
        raise


# Legacy functions kept for backward compatibility
def analyze_sentiment(llm, headlines: list) -> dict:
    """Analyze sentiment of news headlines."""
    if not headlines:
        return {
            "overall_score": 0.0,
            "breakdown": {"positive": 0, "negative": 0, "neutral": 0},
            "details": [],
        }
    
    headlines_text = "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])
    
    system_msg = SystemMessage(content=(
        "You are a financial sentiment analyst. Analyze news headlines and "
        "classify each as bullish, bearish, or neutral from an investor's perspective."
    ))
    
    human_msg = HumanMessage(content=f"""Analyze these headlines:

{headlines_text}

Return JSON:
{{
    "results": [
        {{"headline": "...", "sentiment": "bullish|bearish|neutral", "confidence": 0.0-1.0, "reasoning": "..."}}
    ]
}}""")
    
    try:
        response = llm.invoke([system_msg, human_msg])
        parsed = json.loads(response.content)
        results = parsed.get("results", [])
        
        # Calculate overall score and breakdown
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
        logger.error(f"Sentiment analysis error: {e}")
        return {
            "overall_score": 0.0,
            "breakdown": {"positive": 0, "negative": 0, "neutral": 0},
            "details": [],
            "error": str(e),
        }


def generate_summary(llm, ticker: str, articles: list) -> str:
    """Generate news summary."""
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
        response = llm.invoke([system_msg, human_msg])
        return response.content
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        return f"Unable to generate summary for {ticker}."


def generate_insights(llm, ticker: str, stock_data: dict, sentiment: dict, summary: str) -> str:
    """Generate AI insights combining all analysis data."""
    system_msg = SystemMessage(content=(
        "You are InvestingIQ, an AI financial analyst. Generate comprehensive "
        "investment insights. Remind users this is not financial advice."
    ))
    
    stock_info = format_stock_data(stock_data)
    sentiment_info = format_sentiment(sentiment)
    
    human_msg = HumanMessage(content=f"""Generate insights for {ticker}:

## Stock Data
{stock_info}

## Sentiment
{sentiment_info}

## News Summary
{summary}

Cover: Current position, sentiment overview, key factors, considerations, and risks.""")
    
    try:
        response = llm.invoke([system_msg, human_msg])
        return response.content
    except Exception as e:
        logger.error(f"Insights generation error: {e}")
        return f"Unable to generate insights for {ticker}."


def format_stock_data(data: dict) -> str:
    """Format stock data for prompt."""
    if not data:
        return "No stock data available."
    
    lines = []
    if data.get("company_info", {}).get("name"):
        lines.append(f"- Company: {data['company_info']['name']}")
    if data.get("current_price"):
        lines.append(f"- Current Price: ${data['current_price']:.2f}")
    
    return "\n".join(lines) if lines else "Limited data available."


def format_sentiment(data: dict) -> str:
    """Format sentiment data for prompt."""
    if not data:
        return "No sentiment data available."
    
    score = data.get("overall_score", 0)
    label = "Bullish" if score > 0.3 else "Bearish" if score < -0.3 else "Neutral"
    
    return f"Overall: {label} (score: {score:.2f})"
