"""RAG (Retrieval-Augmented Generation) Service for InvestingIQ."""
import logging
from typing import List, Optional
import uuid

from sqlalchemy.orm import Session
from langchain_openai import OpenAIEmbeddings

from app.config import get_settings
from app.models.database import FinancialDocument, AnalysisReport

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks


class RAGService:
    """Service for RAG operations - document embedding and retrieval."""
    
    def __init__(self):
        """Initialize the RAG service with embeddings model."""
        settings = get_settings()
        self._embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model="text-embedding-3-small",
        )
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a text string."""
        try:
            return self._embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def embed_and_store_document(
        self,
        db: Session,
        ticker: str,
        doc_type: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> Optional[str]:
        """Embed and store a document in the database."""
        if not content or not content.strip():
            return None
        
        try:
            # Chunk if content is long
            chunks = chunk_text(content, chunk_size=500, overlap=50)
            doc_ids = []
            
            for i, chunk in enumerate(chunks):
                embedding = self.get_embedding(chunk)
                
                doc = FinancialDocument(
                    id=uuid.uuid4(),
                    ticker=ticker.upper(),
                    doc_type=doc_type,
                    content=chunk,
                    embedding=embedding,
                    doc_metadata={**(metadata or {}), "chunk_index": i, "total_chunks": len(chunks)}
                )
                db.add(doc)
                doc_ids.append(str(doc.id))
            
            db.commit()
            logger.info(f"Stored {len(chunks)} chunks for {ticker} ({doc_type})")
            return doc_ids[0] if doc_ids else None
            
        except Exception as e:
            logger.error(f"Error storing document: {e}")
            db.rollback()
            return None
    
    def retrieve_context(
        self,
        db: Session,
        query: str,
        ticker: str,
        limit: int = 5
    ) -> List[dict]:
        """Retrieve relevant context documents for a query."""
        try:
            query_embedding = self.get_embedding(query)
            
            # Search using pgvector cosine distance
            results = db.query(FinancialDocument).filter(
                FinancialDocument.ticker == ticker.upper(),
                FinancialDocument.embedding.isnot(None)
            ).order_by(
                FinancialDocument.embedding.cosine_distance(query_embedding)
            ).limit(limit).all()
            
            return [
                {
                    "id": str(doc.id),
                    "content": doc.content,
                    "doc_type": doc.doc_type,
                    "metadata": doc.doc_metadata or {},
                    "ticker": doc.ticker
                }
                for doc in results
            ]
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []
    
    def get_analysis_context(self, db: Session, ticker: str) -> Optional[dict]:
        """Get the latest analysis report as context."""
        try:
            report = db.query(AnalysisReport).filter(
                AnalysisReport.ticker == ticker.upper()
            ).order_by(AnalysisReport.analyzed_at.desc()).first()
            
            if not report:
                return None
            
            return {
                "ticker": report.ticker,
                "company_name": report.company_name,
                "news_summary": report.news_summary,
                "sentiment_score": report.sentiment_score,
                "sentiment_breakdown": report.sentiment_breakdown,
                "ai_insights": report.ai_insights,
                "analyzed_at": report.analyzed_at.isoformat() if report.analyzed_at else None
            }
        except Exception as e:
            logger.error(f"Error getting analysis context: {e}")
            return None
    
    def build_context_string(self, db: Session, query: str, ticker: str, limit: int = 5) -> tuple:
        """Build context string and sources for chat."""
        context_parts = []
        sources = []
        
        # Get relevant documents via vector search
        try:
            docs = self.retrieve_context(db, query, ticker, limit)
            for doc in docs:
                context_parts.append(f"[{doc['doc_type']}]: {doc['content']}")
                sources.append({"title": doc['content'][:50] + "...", "doc_type": doc['doc_type']})
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
        
        # Get latest analysis report
        analysis = self.get_analysis_context(db, ticker)
        if analysis:
            context_parts.append(f"[Latest Analysis for {ticker}]")
            if analysis.get("news_summary"):
                context_parts.append(f"Summary: {analysis['news_summary'][:500]}")
            if analysis.get("ai_insights"):
                context_parts.append(f"Insights: {analysis['ai_insights'][:500]}")
            if analysis.get("sentiment_score") is not None:
                context_parts.append(f"Sentiment Score: {analysis['sentiment_score']:.2f}")
        
        context = "\n\n".join(context_parts) if context_parts else ""
        return context, sources


# Singleton
_rag_service: Optional[RAGService] = None

def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
