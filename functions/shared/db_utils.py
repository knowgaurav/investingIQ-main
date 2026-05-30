"""Database utilities for Azure Functions."""
import logging
import uuid
from datetime import datetime
import psycopg2
from psycopg2.extras import Json

from shared.config import get_settings
from shared.webpubsub_utils import send_progress, send_completed_with_data, send_error

logger = logging.getLogger(__name__)


def get_quarterly_financials(ticker: str, fiscal_quarter: str) -> dict:
    """Return the stored quarterly financials row for a ticker+quarter, or None."""
    settings = get_settings()
    conn = psycopg2.connect(settings.database_url)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, ticker, fiscal_quarter
            FROM quarterly_financials
            WHERE ticker = %s AND fiscal_quarter = %s
            """,
            (ticker.upper(), fiscal_quarter),
        )
        row = cur.fetchone()
        cur.close()
        if not row:
            return None
        return {"id": str(row[0]), "ticker": row[1], "fiscal_quarter": row[2]}
    finally:
        conn.close()


def save_quarterly_financials(ticker: str, fiscal_quarter: str, statements: dict) -> str:
    """Persist quarterly financial statements for a ticker+quarter. Returns row id."""
    settings = get_settings()
    conn = psycopg2.connect(settings.database_url)
    try:
        cur = conn.cursor()
        row_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO quarterly_financials (
                id, ticker, fiscal_quarter, income_statement,
                balance_sheet, cash_flow, earnings, fetched_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, fiscal_quarter) DO NOTHING
            """,
            (
                row_id,
                ticker.upper(),
                fiscal_quarter,
                Json(statements.get("income_statement", {})),
                Json(statements.get("balance_sheet", {})),
                Json(statements.get("cash_flow", {})),
                Json(statements.get("earnings", {})),
                datetime.utcnow(),
            ),
        )
        conn.commit()
        cur.close()
        logger.info(f"Saved quarterly financials for {ticker} {fiscal_quarter}")
        return row_id
    finally:
        conn.close()


def save_analysis_report(data: dict) -> dict:
    """Save analysis report to PostgreSQL and stream full results via SSE."""
    task_id = data.get("task_id")
    ticker = data.get("ticker")
    settings = get_settings()

    ml_analysis = data.get("ml_analysis") or {}
    llm_analysis = data.get("llm_analysis") or {}
    stock_data = data.get("stock_data") or {}
    company_info = stock_data.get("company_info") or {}

    llm_sentiment = llm_analysis.get("sentiment") or {}
    sentiment_score = llm_sentiment.get("score", 0)
    news_summary = llm_analysis.get("insight", "")
    ai_insights = llm_analysis.get("insight", "")

    try:
        send_progress(task_id, 90, "Saving report")

        conn = psycopg2.connect(settings.database_url)
        cur = conn.cursor()

        report_id = str(uuid.uuid4())

        cur.execute("""
            INSERT INTO analysis_reports (
                id, ticker, company_name, price_data, news_summary,
                sentiment_score, sentiment_breakdown, sentiment_details, ai_insights, analyzed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            report_id,
            ticker,
            company_info.get("name", ticker),
            Json(stock_data.get("price_history", [])),
            news_summary,
            sentiment_score,
            Json(llm_sentiment),
            Json([]),
            ai_insights,
            datetime.utcnow(),
        ))

        if task_id:
            cur.execute("""
                UPDATE analysis_tasks
                SET status = 'completed', progress = 100, current_step = 'Analysis complete'
                WHERE id = %s
            """, (task_id,))

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Saved report {report_id} for {ticker}")

        send_completed_with_data(task_id, ticker, {
            "stock_data": stock_data,
            "news": data.get("news", []),
            "ml_prediction": ml_analysis.get("prediction"),
            "ml_technical": ml_analysis.get("technical"),
            "ml_sentiment": ml_analysis.get("sentiment"),
            "llm_sentiment": llm_sentiment or None,
            "llm_summary": news_summary or None,
            "llm_insights": ai_insights or None,
            "llm_outlook": llm_analysis.get("outlook"),
            "dual_comparison": data.get("dual_comparison"),
            "llm_status": data.get("llm_status"),
            "financials_status": data.get("financials_status"),
            "financials_quarter": data.get("financials_quarter"),
            "report_id": report_id,
        })
        return {"id": report_id, "status": "success"}

    except Exception as e:
        logger.error(f"Failed to save report: {e}")
        send_error(task_id, str(e))
        return {"status": "error", "error": str(e)}
