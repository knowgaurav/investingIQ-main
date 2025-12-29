"""Initial schema with all tables

Revision ID: 001
Revises: 
Create Date: 2024-12-29

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Analysis Reports table
    op.create_table(
        'analysis_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ticker', sa.String(10), nullable=False, index=True),
        sa.Column('company_name', sa.String(255)),
        sa.Column('analyzed_at', sa.DateTime, nullable=False),
        sa.Column('price_data', postgresql.JSON),
        sa.Column('news_summary', sa.Text),
        sa.Column('sentiment_score', sa.Float),
        sa.Column('sentiment_breakdown', postgresql.JSON),
        sa.Column('sentiment_details', postgresql.JSON),
        sa.Column('ai_insights', sa.Text),
        sa.Column('news_count', sa.Integer, default=0),
        sa.Column('data_sources', postgresql.ARRAY(sa.String)),
        sa.Column('processing_time_seconds', sa.Float),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    
    # Analysis Tasks table
    op.create_table(
        'analysis_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('celery_task_id', sa.String(255), unique=True, index=True),
        sa.Column('ticker', sa.String(10), nullable=False, index=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('progress', sa.Integer, default=0),
        sa.Column('current_step', sa.String(100)),
        sa.Column('error_message', sa.Text),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('analysis_reports.id'), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )
    
    # Chat Conversations table
    op.create_table(
        'chat_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ticker', sa.String(10), index=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
    )
    
    # Chat Messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('chat_conversations.id'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('sources', postgresql.ARRAY(sa.String)),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    
    # Financial Documents table (for RAG)
    op.create_table(
        'financial_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ticker', sa.String(10), nullable=False, index=True),
        sa.Column('doc_type', sa.String(50), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('metadata', postgresql.JSON),
        sa.Column('embedding', sa.Column('embedding', sa.LargeBinary)),  # Will be vector(1536)
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    
    # Create vector column separately (pgvector specific)
    op.execute('ALTER TABLE financial_documents DROP COLUMN IF EXISTS embedding')
    op.execute('ALTER TABLE financial_documents ADD COLUMN embedding vector(1536)')
    
    # Create vector index for similarity search
    op.execute('''
        CREATE INDEX idx_financial_documents_embedding 
        ON financial_documents 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    ''')


def downgrade() -> None:
    op.drop_table('financial_documents')
    op.drop_table('chat_messages')
    op.drop_table('chat_conversations')
    op.drop_table('analysis_tasks')
    op.drop_table('analysis_reports')
    op.execute('DROP EXTENSION IF EXISTS vector')
