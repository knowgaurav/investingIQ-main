"""LLM Service for InvestingIQ using OhMyGPT API via LangChain."""
import json
import logging
import time
from typing import List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

from app.config import get_settings
from app.utils.mlflow_tracker import get_mlflow_tracker

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM operations using OpenAI-compatible API."""
    
    def __init__(self):
        """Initialize the LLM service."""
        settings = get_settings()
        
        self._llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.llm_model,
            temperature=0.7,
            max_tokens=4000,
        )
        self._parser = StrOutputParser()
        self._model_name = settings.llm_model
        self._tracker = get_mlflow_tracker()
    
    @property
    def llm(self) -> ChatOpenAI:
        """Get the LLM instance."""
        return self._llm
    
    def chat(self, query: str, context: str = "") -> str:
        """
        Basic chat completion with optional context.
        
        Args:
            query: User query/question
            context: Optional context to include in the prompt
            
        Returns:
            LLM response string
        """
        try:
            messages = []
            
            system_content = (
                "You are InvestingIQ, an AI financial assistant specializing in "
                "stock market analysis, investment insights, and financial news interpretation. "
                "Provide accurate, helpful, and balanced financial information. "
                "Always remind users that this is not financial advice and they should "
                "consult with a qualified financial advisor for investment decisions."
            )
            
            if context:
                system_content += f"\n\nContext:\n{context}"
            
            messages.append(SystemMessage(content=system_content))
            messages.append(HumanMessage(content=query))
            
            start_time = time.time()
            response = self._llm.invoke(messages)
            latency_ms = (time.time() - start_time) * 1000
            
            result = self._parser.invoke(response)
            
            # Track LLM call with MLflow
            usage = getattr(response, 'usage_metadata', None) or {}
            input_tokens = usage.get("input_tokens", 0) if isinstance(usage, dict) else 0
            output_tokens = usage.get("output_tokens", 0) if isinstance(usage, dict) else 0
            
            self._tracker.log_llm_call(
                operation="chat",
                model_name=self._model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                prompt_template="chat_system_prompt",
                metadata={"has_context": bool(context)}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            raise
    
    def analyze_sentiment(self, headlines: List[str]) -> List[dict]:
        """
        Analyze sentiment of news headlines.
        
        Args:
            headlines: List of news headlines to analyze
            
        Returns:
            List of dicts with {headline, sentiment, confidence, reasoning}
        """
        if not headlines:
            return []
        
        try:
            headlines_text = "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])
            
            system_message = SystemMessage(content=(
                "You are a financial sentiment analysis expert. Analyze the sentiment "
                "of each news headline provided. For each headline, determine if the "
                "sentiment is 'bullish', 'bearish', or 'neutral' from an investor's perspective."
            ))
            
            human_message = HumanMessage(content=f"""Analyze the sentiment of each of the following news headlines.

Headlines:
{headlines_text}

For each headline, provide your analysis in the following JSON format:
{{
    "results": [
        {{
            "headline": "the headline text",
            "sentiment": "bullish|bearish|neutral",
            "confidence": 0.0-1.0,
            "reasoning": "brief explanation"
        }}
    ]
}}

Respond ONLY with valid JSON, no additional text.""")
            
            start_time = time.time()
            response = self._llm.invoke([system_message, human_message])
            latency_ms = (time.time() - start_time) * 1000
            
            response_text = self._parser.invoke(response)
            
            # Track LLM call with MLflow
            usage = getattr(response, "usage_metadata", None) or {}; input_tokens = usage.get("input_tokens", 0) if isinstance(usage, dict) else 0
            output_tokens = usage.get("output_tokens", 0) if isinstance(usage, dict) else 0
            
            self._tracker.log_llm_call(
                operation="sentiment_analysis",
                model_name=self._model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                prompt_template="sentiment_analysis_prompt",
                metadata={"headline_count": len(headlines)}
            )
            
            # Parse JSON response - handle markdown code blocks
            response_text = response_text.strip()
            if response_text.startswith("```"):
                # Remove markdown code block
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            
            parsed = json.loads(response_text)
            return parsed.get("results", [])
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse sentiment response as JSON: {e}")
            # Return basic structure on parse failure
            return [
                {
                    "headline": h,
                    "sentiment": "neutral",
                    "confidence": 0.5,
                    "reasoning": "Unable to analyze"
                }
                for h in headlines
            ]
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            raise
    
    def summarize_news(self, articles: List[dict], ticker: str) -> str:
        """
        Summarize news articles for a specific stock ticker.
        
        Args:
            articles: List of article dicts with 'title', 'description', 'content' keys
            ticker: Stock ticker symbol
            
        Returns:
            Summary string
        """
        if not articles:
            return f"No recent news articles found for {ticker}."
        
        try:
            # Build article text for summarization
            articles_text = ""
            for i, article in enumerate(articles[:10], 1):  # Limit to 10 articles
                title = article.get("title", "No title")
                description = article.get("description", "")
                content = article.get("content", "")[:500]  # Truncate content
                
                articles_text += f"\n--- Article {i} ---\n"
                articles_text += f"Title: {title}\n"
                if description:
                    articles_text += f"Description: {description}\n"
                if content:
                    articles_text += f"Content: {content}\n"
            
            system_message = SystemMessage(content=(
                "You are a financial news analyst. Your task is to summarize news articles "
                "about a specific stock, highlighting key developments, market implications, "
                "and important events that investors should know about."
            ))
            
            human_message = HumanMessage(content=f"""Summarize the following news articles about {ticker}.

{articles_text}

Provide a comprehensive but concise summary (2-3 paragraphs) that covers:
1. Key developments and announcements
2. Market sentiment and analyst opinions (if mentioned)
3. Potential impact on the stock

Focus on the most important and recent information.""")
            
            start_time = time.time()
            response = self._llm.invoke([system_message, human_message])
            latency_ms = (time.time() - start_time) * 1000
            
            result = self._parser.invoke(response)
            
            # Track LLM call with MLflow
            usage = getattr(response, "usage_metadata", None) or {}; input_tokens = usage.get("input_tokens", 0) if isinstance(usage, dict) else 0
            output_tokens = usage.get("output_tokens", 0) if isinstance(usage, dict) else 0
            
            self._tracker.log_llm_call(
                operation="news_summarization",
                model_name=self._model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                prompt_template="news_summarization_prompt",
                metadata={"ticker": ticker, "article_count": len(articles)}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"News summarization error: {e}")
            raise
    
    def generate_insights(
        self,
        ticker: str,
        stock_data: dict,
        sentiment: dict,
        summary: str
    ) -> str:
        """
        Generate comprehensive AI insights combining all analysis data.
        
        Args:
            ticker: Stock ticker symbol
            stock_data: Stock price and company data
            sentiment: Sentiment analysis results
            summary: News summary
            
        Returns:
            AI insights string
        """
        try:
            # Format stock data
            stock_info = self._format_stock_data(stock_data)
            
            # Format sentiment data
            sentiment_info = self._format_sentiment_data(sentiment)
            
            system_message = SystemMessage(content=(
                "You are InvestingIQ, an expert AI financial analyst. Generate comprehensive "
                "investment insights by analyzing stock data, market sentiment, and recent news. "
                "Provide balanced, informative analysis while reminding users this is not "
                "financial advice."
            ))
            
            human_message = HumanMessage(content=f"""Generate investment insights for {ticker} based on the following data:

## Stock Data
{stock_info}

## Sentiment Analysis
{sentiment_info}

## News Summary
{summary}

Provide comprehensive insights covering:
1. **Current Position**: Brief overview of the stock's current state
2. **Sentiment Overview**: What the market sentiment suggests
3. **Key Factors**: Important factors affecting the stock
4. **Considerations**: Things investors should consider
5. **Risk Factors**: Potential risks to be aware of

End with a reminder that this is AI-generated analysis and not financial advice.""")
            
            start_time = time.time()
            response = self._llm.invoke([system_message, human_message])
            latency_ms = (time.time() - start_time) * 1000
            
            result = self._parser.invoke(response)
            
            # Track LLM call with MLflow
            usage = getattr(response, "usage_metadata", None) or {}; input_tokens = usage.get("input_tokens", 0) if isinstance(usage, dict) else 0
            output_tokens = usage.get("output_tokens", 0) if isinstance(usage, dict) else 0
            
            self._tracker.log_llm_call(
                operation="insights_generation",
                model_name=self._model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                prompt_template="insights_generation_prompt",
                metadata={"ticker": ticker}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Insights generation error: {e}")
            raise
    
    def _format_stock_data(self, stock_data: dict) -> str:
        """Format stock data for prompt inclusion."""
        if not stock_data:
            return "No stock data available."
        
        lines = []
        
        if "current_price" in stock_data:
            lines.append(f"- Current Price: ${stock_data['current_price']:.2f}")
        if "change_percent" in stock_data:
            lines.append(f"- Change: {stock_data['change_percent']:.2f}%")
        if "market_cap" in stock_data:
            lines.append(f"- Market Cap: ${stock_data['market_cap']:,.0f}")
        if "volume" in stock_data:
            lines.append(f"- Volume: {stock_data['volume']:,}")
        if "pe_ratio" in stock_data:
            lines.append(f"- P/E Ratio: {stock_data['pe_ratio']:.2f}")
        if "52_week_high" in stock_data:
            lines.append(f"- 52-Week High: ${stock_data['52_week_high']:.2f}")
        if "52_week_low" in stock_data:
            lines.append(f"- 52-Week Low: ${stock_data['52_week_low']:.2f}")
        if "company_name" in stock_data:
            lines.insert(0, f"- Company: {stock_data['company_name']}")
        if "sector" in stock_data:
            lines.append(f"- Sector: {stock_data['sector']}")
        
        return "\n".join(lines) if lines else "Limited stock data available."
    
    def _format_sentiment_data(self, sentiment: dict) -> str:
        """Format sentiment data for prompt inclusion."""
        if not sentiment:
            return "No sentiment data available."
        
        lines = []
        
        if "sentiment_score" in sentiment:
            score = sentiment["sentiment_score"]
            if score > 0.3:
                sentiment_label = "Bullish"
            elif score < -0.3:
                sentiment_label = "Bearish"
            else:
                sentiment_label = "Neutral"
            lines.append(f"- Overall Sentiment: {sentiment_label} (score: {score:.2f})")
        
        if "sentiment_breakdown" in sentiment:
            breakdown = sentiment["sentiment_breakdown"]
            lines.append(f"- Bullish articles: {breakdown.get('bullish', 0)}")
            lines.append(f"- Bearish articles: {breakdown.get('bearish', 0)}")
            lines.append(f"- Neutral articles: {breakdown.get('neutral', 0)}")
        
        return "\n".join(lines) if lines else "Limited sentiment data available."


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
