"""SQLAlchemy database models."""
from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, String, DateTime, JSON, Float, Integer, ForeignKey, Text, create_engine
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector

from app.config import get_settings

settings = get_settings()

Base = declarative_base()

# Database engine and session
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AnalysisReport(Base):
    """Stores completed stock analysis reports."""
    __tablename__ = "analysis_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), nullable=False, index=True)
    company_name = Column(String(255))
    analyzed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Price data stored as JSON array
    price_data = Column(JSON)
    
    # Analysis results
    news_summary = Column(Text)
    sentiment_score = Column(Float)  # -1.0 to 1.0
    sentiment_breakdown = Column(JSON)  # {bullish: 5, bearish: 2, neutral: 3}
    sentiment_details = Column(JSON)  # List of individual headline sentiments
    ai_insights = Column(Text)
    
    # Metadata
    news_count = Column(Integer, default=0)
    data_sources = Column(ARRAY(String))
    processing_time_seconds = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tasks = relationship("AnalysisTask", back_populates="report")


class AnalysisTask(Base):
    """Tracks Celery analysis tasks."""
    __tablename__ = "analysis_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    celery_task_id = Column(String(255), unique=True, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    progress = Column(Integer, default=0)
    current_step = Column(String(100))
    error_message = Column(Text)
    
    report_id = Column(UUID(as_uuid=True), ForeignKey("analysis_reports.id"), nullable=True)
    report = relationship("AnalysisReport", back_populates="tasks")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class ChatConversation(Base):
    """Stores chat conversation sessions."""
    __tablename__ = "chat_conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = relationship("ChatMessage", back_populates="conversation", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    """Stores individual chat messages."""
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("chat_conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sources = Column(ARRAY(String))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("ChatConversation", back_populates="messages")


class FinancialDocument(Base):
    """Stores embedded financial documents for RAG."""
    __tablename__ = "financial_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), nullable=False, index=True)
    doc_type = Column(String(50), nullable=False)  # 'news', 'price_history', 'company_info'
    content = Column(Text, nullable=False)
    metadata = Column(JSON)
    embedding = Column(Vector(1536))  # OpenAI embedding dimension
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
