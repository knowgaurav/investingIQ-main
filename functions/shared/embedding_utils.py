"""Embedding utilities for Azure Functions."""
import logging
import psycopg2
from openai import OpenAI

from shared.config import get_settings

logger = logging.getLogger(__name__)

_embedding_client = None


def _get_embedding_client() -> OpenAI:
    global _embedding_client
    if _embedding_client is None:
        settings = get_settings()
        _embedding_client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
    return _embedding_client


def get_embedding(text: str) -> list:
    """Generate embedding for text."""
    client = _get_embedding_client()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def embed_and_store(ticker: str, doc_type: str, content: str, metadata: dict = None):
    """Embed and store document in PostgreSQL."""
    if not content or not content.strip():
        return
    
    settings = get_settings()
    
    try:
        embedding = get_embedding(content[:2000])  # Limit content length
        
        conn = psycopg2.connect(settings.database_url)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO financial_documents (ticker, doc_type, content, embedding, doc_metadata)
            VALUES (%s, %s, %s, %s, %s)
        """, (ticker.upper(), doc_type, content, embedding, metadata or {}))
        
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Stored embedding for {ticker} ({doc_type})")
    except Exception as e:
        logger.error(f"Embedding storage failed: {e}")


def embed_financials_passage(
    ticker: str,
    fiscal_quarter: str,
    statement_type: str,
    content: str,
    chunk_index: int,
):
    """Embed and store a quarterly financials passage, skipping duplicates.

    Deduplicates on (ticker, doc_type='quarterly_financials', fiscal_quarter,
    statement_type, chunk_index) so re-ingesting the same quarter does not create
    duplicate embeddings.
    """
    if not content or not content.strip():
        return

    from psycopg2.extras import Json

    settings = get_settings()
    ticker = ticker.upper()
    metadata = {
        "fiscal_quarter": fiscal_quarter,
        "statement_type": statement_type,
        "chunk_index": chunk_index,
    }

    conn = psycopg2.connect(settings.database_url)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 1 FROM financial_documents
            WHERE ticker = %s
              AND doc_type = 'quarterly_financials'
              AND doc_metadata->>'fiscal_quarter' = %s
              AND doc_metadata->>'statement_type' = %s
              AND doc_metadata->>'chunk_index' = %s
            LIMIT 1
            """,
            (ticker, fiscal_quarter, statement_type, str(chunk_index)),
        )
        if cur.fetchone():
            cur.close()
            logger.info(
                f"Skipping duplicate financials embedding for {ticker} "
                f"{fiscal_quarter} {statement_type} chunk {chunk_index}"
            )
            return

        embedding = get_embedding(content[:2000])
        cur.execute(
            """
            INSERT INTO financial_documents (ticker, doc_type, content, embedding, doc_metadata)
            VALUES (%s, 'quarterly_financials', %s, %s, %s)
            """,
            (ticker, content, embedding, Json(metadata)),
        )
        conn.commit()
        cur.close()
        logger.info(
            f"Stored financials embedding for {ticker} {fiscal_quarter} "
            f"{statement_type} chunk {chunk_index}"
        )
    except Exception as e:
        logger.error(f"Financials embedding storage failed: {e}")
    finally:
        conn.close()
