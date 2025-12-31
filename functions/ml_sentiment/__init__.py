"""ML Sentiment Analysis Azure Function - VADER and TextBlob."""
import json
import logging
from datetime import datetime

import azure.functions as func
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


vader_analyzer = SentimentIntensityAnalyzer()

BULLISH_KEYWORDS = {
    'surge', 'soar', 'rally', 'gain', 'rise', 'jump', 'climb', 'boost',
    'record', 'high', 'growth', 'profit', 'beat', 'exceed', 'strong',
    'upgrade', 'buy', 'bullish', 'outperform', 'positive', 'upside'
}

BEARISH_KEYWORDS = {
    'fall', 'drop', 'decline', 'plunge', 'crash', 'loss', 'miss', 'weak',
    'downgrade', 'sell', 'bearish', 'underperform', 'negative', 'risk',
    'concern', 'warning', 'cut', 'slash', 'layoff', 'recession'
}


def main(msg: func.ServiceBusMessage, outputSbMsg: func.Out[str]):
    """
    Process sentiment analysis using VADER and TextBlob.
    
    Triggered by: ml-queue (task_type: ml_sentiment)
    Outputs to: aggregate-queue
    """
    from shared.webpubsub_utils import send_progress
    
    try:
        message = json.loads(msg.get_body().decode('utf-8'))
        task_id = message.get("task_id")
        ticker = message.get("ticker")
        headlines = message.get("data", {}).get("headlines", [])
        
        logger.info(f"Running ML sentiment for {ticker}, task_id: {task_id}")
        send_progress(task_id, 35, "Analyzing news sentiment")
        
        result = analyze_sentiment(headlines)
        
        output_message = {
            "task_type": "ml_sentiment_ready",
            "task_id": task_id,
            "ticker": ticker,
            "data": result,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        outputSbMsg.set(json.dumps(output_message))
        logger.info(f"Completed ML sentiment for {ticker}")
        
    except Exception as e:
        logger.error(f"ML sentiment error: {e}")
        raise


def analyze_sentiment(headlines: list) -> dict:
    """Analyze sentiment using VADER, TextBlob, and keyword analysis."""
    if not headlines:
        return empty_sentiment()
    
    details = []
    vader_scores = []
    textblob_scores = []
    
    for headline in headlines:
        text = headline.get('title', '') if isinstance(headline, dict) else str(headline)
        if not text:
            continue
        
        vader_score = analyze_vader(text)
        textblob_score = analyze_textblob(text)
        keyword_score = analyze_keywords(text)
        
        combined_score = (vader_score * 0.4 + textblob_score * 0.3 + keyword_score * 0.3)
        
        label = score_to_label(combined_score)
        
        details.append({
            "headline": text[:200],
            "score": round(combined_score, 3),
            "label": label,
        })
        
        vader_scores.append(vader_score)
        textblob_scores.append(textblob_score)
    
    if not details:
        return empty_sentiment()
    
    overall_score = sum(d['score'] for d in details) / len(details)
    
    positive_count = sum(1 for d in details if d['label'] == 'positive')
    negative_count = sum(1 for d in details if d['label'] == 'negative')
    neutral_count = sum(1 for d in details if d['label'] == 'neutral')
    total = len(details)
    
    return {
        "overall_score": round(overall_score, 3),
        "label": score_to_label(overall_score),
        "positive_pct": round(positive_count / total * 100, 1),
        "neutral_pct": round(neutral_count / total * 100, 1),
        "negative_pct": round(negative_count / total * 100, 1),
        "details": details,
    }


def analyze_vader(text: str) -> float:
    """Analyze text with VADER (returns -1 to 1)."""
    try:
        scores = vader_analyzer.polarity_scores(text)
        return scores['compound']
    except Exception:
        return 0.0


def analyze_textblob(text: str) -> float:
    """Analyze text with TextBlob (returns -1 to 1)."""
    try:
        blob = TextBlob(text)
        return blob.sentiment.polarity
    except Exception:
        return 0.0


def analyze_keywords(text: str) -> float:
    """Analyze text for bullish/bearish keywords (returns -1 to 1)."""
    text_lower = text.lower()
    words = set(text_lower.split())
    
    bullish_count = len(words & BULLISH_KEYWORDS)
    bearish_count = len(words & BEARISH_KEYWORDS)
    
    total = bullish_count + bearish_count
    if total == 0:
        return 0.0
    
    return (bullish_count - bearish_count) / total


def score_to_label(score: float) -> str:
    """Convert score to sentiment label."""
    if score > 0.1:
        return "positive"
    elif score < -0.1:
        return "negative"
    return "neutral"


def empty_sentiment() -> dict:
    """Return empty sentiment result."""
    return {
        "overall_score": 0.0,
        "label": "neutral",
        "positive_pct": 0.0,
        "neutral_pct": 100.0,
        "negative_pct": 0.0,
        "details": [],
    }
