"""RAG (Retrieval-Augmented Generation) Service for InvestingIQ."""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session
from langchain_openai import OpenAIEmbeddings

from app.config import get_settings
from app.models.database import FinancialDocument, AnalysisReport

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG operations - document embedding and retrieval."""
    
    def __init__(self):
        """Initialize the RAG service with embeddings model."""
        settings = get_settings()
        
        self._embeddings = OpenAIEmbeddings(
            api_key=settings.ohmygpt_api_key,
            base_url=settings.ohmygpt_api_base,
            model="text-embedding-3-small",
        )
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a text string.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            return self._embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def retrieve_context(
        self,
        db: Session,
        query: str,
        ticker: str,
        limit: int = 5
    ) -> List[dict]:
        """
        Retrieve relevant context documents for a query.
        
        Args:
            db: Database session
            query: User query to find relevant context for
            ticker: Stock ticker to filter documents
            limit: Maximum number of documents to retrieve
            
        Returns:
            List of relevant document dicts with content and metadata
        """
        try:
            # Generate embedding for the query
            query_embedding = self.get_embedding(query)
            
            # Search for similar documents using pgvector
            # Using cosine similarity via the <=> operator
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
                    "metadata": doc.metadata or {},
                    "ticker": doc.ticker
                }
                for doc in results
            ]
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            # Return empty list on error to allow chat to continue without RAG
            return []
    
    def get_analysis_context(
        self,
        db: Session,
        ticker: str
    ) -> Optional[dict]:
        """
        Get the latest analysis report as context.
        
        Args:
            db: Database session
            ticker: Stock ticker
            
        Returns:
            Dict with analysis context or None
        """
        try:
            report = db.query(AnalysisReport).filter(
                AnalysisReport.ticker == ticker.upper()
            ).order_by(
                AnalysisReport.analyzed_at.desc()
            ).first()
            
            if not report:
                return None
            
            return {
                "ticker": report.ticker,
                "company_name": report.company_name,
                "analyzed_at": report.analyzed_at.isoformat() if report.analyzed_at else None,
                "news_summary": report.news_summary,
                "sentiment_score": report.sentiment_score,
                "sentiment_breakdown": report.sentiment_breakdown,
                "ai_insights": report.ai_insights
            }
        except Exception as e:
            logger.error(f"Error getting analysis context: {e}")
            return None
    
    def build_context_string(
        self,
        db: Session,
        query: str,
        ticker: str
    ) -> tuple[str, List[str]]:
        """
        Build a context string for the LLM from retrieved documents.
        
        Args:
            db: Database session
            query: User query
            ticker: Stock ticker
            
        Returns:
            Tuple of (context_string, list_of_sources)
        """
        context_parts = []
        sources = []
        
        # Get latest analysis report context
        analysis = self.get_analysis_context(db, ticker)
        if analysis:
            context_parts.append(f"## Latest Analysis for {ticker}")
            if analysis.get("company_name"):
                context_parts.append(f"Company: {analysis['company_name']}")
            if analysis.get("analyzed_at"):
                context_parts.append(f"Analysis Date: {analysis['analyzed_at']}")
            if analysis.get("news_summary"):
                context_parts.append(f"\n### News Summary\n{analysis['news_summary']}")
            if analysis.get("sentiment_score") is not None:
                score = analysis["sentiment_score"]
                sentiment_label = "Bullish" if score > 0.3 else "Bearish" if score < -0.3 else "Neutral"
                context_parts.append(f"\n### Sentiment: {sentiment_label} (score: {score:.2f})")
            if analysis.get("ai_insights"):
                context_parts.append(f"\n### AI Insights\n{analysis['ai_insights']}")
            sources.append(f"Analysis Report ({analysis.get('analyzed_at', 'recent')})")
        
        # Get relevant documents via vector search
        documents = self.retrieve_context(db, query, ticker)
        if documents:
            context_parts.append(f"\n## Relevant Documents")
            for doc in documents:
                context_parts.append(f"\n### {doc['doc_type'].title()}")
                context_parts.append(doc['content'])
                source_info = doc.get('metadata', {}).get('source', doc['doc_type'])
                if source_info not in sources:
                    sources.append(source_info)
        
        context_string = "\n".join(context_parts) if context_parts else ""
        return context_string, sources
    
    def store_document(
        self,
        db: Session,
        ticker: str,
        doc_type: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> FinancialDocument:
        """
        Store a document with its embedding.
        
        Args:
            db: Database session
            ticker: Stock ticker
            doc_type: Type of document (news, price_history, company_info)
            content: Document content
            metadata: Optional metadata dict
            
        Returns:
            Created FinancialDocument
        """
        try:
            embedding = self.get_embedding(content)
            
            doc = FinancialDocument(
                ticker=ticker.upper(),
                doc_type=doc_type,
                content=content,
                metadata=metadata or {},
                embedding=embedding
            )
            
            db.add(doc)
            db.commit()
            db.refresh(doc)
            
            return doc
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing document: {e}")
            raise
    
    def embed_documents(
        self,
        ticker: str,
        stock_data: dict,
        news_articles: list
    ) -> str:
        """
        Embed multiple documents for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            stock_data: Stock price and company data
            news_articles: List of news articles
            
        Returns:
            Batch ID for the embedding operation
        """
        import uuid
        from app.models.database import SessionLocal
        
        batch_id = str(uuid.uuid4())
        db = SessionLocal()
        
        try:
            # Embed company info if available
            if stock_data.get("company_info"):
                info = stock_data["company_info"]
                content = f"Company: {info.get('name', ticker)}\n"
                content += f"Sector: {info.get('sector', 'N/A')}\n"
                content += f"Industry: {info.get('industry', 'N/A')}\n"
                content += f"Description: {info.get('description', 'N/A')}"
                
                self.store_document(
                    db=db,
                    ticker=ticker,
                    doc_type="company_info",
                    content=content,
                    metadata={"batch_id": batch_id, "source": "yfinance"}
                )
            
            # Embed price summary
            if stock_data.get("price_history"):
                prices = stock_data["price_history"]
                if prices:
                    latest = prices[-1] if isinstance(prices, list) else prices
                    content = f"Stock {ticker} price data:\n"
                    content += f"Latest close: ${latest.get('close', 'N/A')}\n"
                    content += f"Volume: {latest.get('volume', 'N/A')}"
                    
                    self.store_document(
                        db=db,
                        ticker=ticker,
                        doc_type="price_history",
                        content=content,
                        metadata={"batch_id": batch_id, "source": "yfinance"}
                    )
            
            # Embed news articles
            for article in news_articles[:10]:  # Limit to 10 articles
                content = f"Title: {article.get('title', 'N/A')}\n"
                content += f"Source: {article.get('source', 'N/A')}\n"
                content += f"Published: {article.get('published_at', 'N/A')}\n"
                content += f"Content: {article.get('description', article.get('content', 'N/A'))}"
                
                self.store_document(
                    db=db,
                    ticker=ticker,
                    doc_type="news",
                    content=content,
                    metadata={
                        "batch_id": batch_id,
                        "source": article.get("source", "news"),
                        "url": article.get("url", ""),
                        "published_at": article.get("published_at", "")
                    }
                )
            
            logger.info(f"Embedded documents for {ticker}, batch_id: {batch_id}")
            return batch_id
            
        except Exception as e:
            logger.error(f"Error embedding documents for {ticker}: {e}")
            raise
        finally:
            db.close()


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
