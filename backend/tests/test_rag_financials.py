"""Tests for financials-aware RAG context building."""
from unittest.mock import patch, MagicMock


def _make_service():
    with patch("app.services.rag_service.OpenAIEmbeddings"):
        from app.services.rag_service import RAGService
        return RAGService()


class TestBuildContextString:
    def test_financials_citation_includes_quarter_and_statement(self):
        service = _make_service()

        docs = [
            {
                "id": "1",
                "content": "AAPL — Income Statement ... Net income: $36.33B",
                "doc_type": "quarterly_financials",
                "metadata": {"statement_type": "income_statement", "fiscal_quarter": "2024-12-31"},
                "ticker": "AAPL",
            }
        ]

        with patch.object(service, "retrieve_context", return_value=docs), \
             patch.object(service, "has_financials", return_value=True), \
             patch.object(service, "get_analysis_context", return_value=None):
            context, sources = service.build_context_string(MagicMock(), "What was net income?", "AAPL")

        assert "Income Statement · 2024-12-31" in sources
        assert "quarterly_financials" in context

    def test_prompts_to_analyze_when_no_financials(self):
        service = _make_service()

        with patch.object(service, "retrieve_context", return_value=[]), \
             patch.object(service, "has_financials", return_value=False), \
             patch.object(service, "get_analysis_context", return_value=None):
            context, sources = service.build_context_string(MagicMock(), "How are the financials?", "AAPL")

        assert "No quarterly financials" in context
        assert "run an analysis" in context.lower()
        assert sources == []
