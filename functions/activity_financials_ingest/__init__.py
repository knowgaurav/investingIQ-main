"""Activity: Fetch, persist, and embed a company's quarterly financials (on-demand)."""
import logging

logger = logging.getLogger(__name__)


def _chunk(text: str, chunk_size: int = 2000, overlap: int = 100) -> list:
    """Split text into overlapping chunks that fit the embedding input limit."""
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start:start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def main(input_data: dict) -> dict:
    from shared.webpubsub_utils import send_progress
    from shared.alpha_vantage import (
        fetch_income_statement, fetch_balance_sheet, fetch_cash_flow, fetch_earnings,
    )
    from shared.db_utils import get_quarterly_financials, save_quarterly_financials
    from shared.embedding_utils import embed_financials_passage
    from shared import financials_text

    ticker = input_data["ticker"]
    task_id = input_data["task_id"]

    try:
        send_progress(task_id, 30, "Fetching quarterly financials")

        income = fetch_income_statement(ticker)
        balance = fetch_balance_sheet(ticker)
        cash = fetch_cash_flow(ticker)
        earnings = fetch_earnings(ticker)

        # Resolve the latest fiscal quarter present across the statements.
        fiscal_quarter = (
            income.get("fiscal_quarter")
            or balance.get("fiscal_quarter")
            or cash.get("fiscal_quarter")
        )

        if not fiscal_quarter:
            logger.warning(f"No quarterly financials available for {ticker}")
            return {"type": "financials_ingest", "status": "unavailable", "fiscal_quarter": None}

        # Reuse if already ingested for this ticker+quarter.
        if get_quarterly_financials(ticker, fiscal_quarter):
            logger.info(f"Reusing stored financials for {ticker} {fiscal_quarter}")
            return {"type": "financials_ingest", "status": "reused", "fiscal_quarter": fiscal_quarter}

        statements = {
            "income_statement": income.get("report", {}),
            "balance_sheet": balance.get("report", {}),
            "cash_flow": cash.get("report", {}),
            "earnings": earnings,
        }
        save_quarterly_financials(ticker, fiscal_quarter, statements)

        send_progress(task_id, 40, "Embedding quarterly financials")

        passages = {
            "income_statement": financials_text.income_statement_to_text(ticker, fiscal_quarter, income.get("report", {})),
            "balance_sheet": financials_text.balance_sheet_to_text(ticker, fiscal_quarter, balance.get("report", {})),
            "cash_flow": financials_text.cash_flow_to_text(ticker, fiscal_quarter, cash.get("report", {})),
            "earnings": financials_text.earnings_to_text(ticker, fiscal_quarter, earnings),
        }

        for statement_type, passage in passages.items():
            for chunk_index, chunk in enumerate(_chunk(passage)):
                embed_financials_passage(ticker, fiscal_quarter, statement_type, chunk, chunk_index)

        logger.info(f"Financials ingest complete for {ticker} {fiscal_quarter}")
        return {"type": "financials_ingest", "status": "ok", "fiscal_quarter": fiscal_quarter}

    except Exception as e:
        logger.error(f"Financials ingest failed for {ticker}: {e}")
        return {"type": "financials_ingest", "status": "unavailable", "error": str(e), "fiscal_quarter": None}
