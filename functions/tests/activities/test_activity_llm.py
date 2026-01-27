"""Tests for activity_llm_analysis function."""
import pytest
from unittest.mock import patch, MagicMock


class TestActivityLLMAnalysis:
    """Tests for the LLM analysis activity function."""
    
    def test_main_creates_analyzer_and_runs_analysis(self):
        """Test main function creates analyzer and runs analysis."""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = {
            "success": True,
            "analysis": {"ticker": "AAPL", "recommendation": "Buy"}
        }
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_analyzer
        
        input_data = {
            "ticker": "AAPL",
            "task_id": "test-123",
            "llm_config": {
                "provider": "openai",
                "api_key": "test-key",
                "model": "gpt-4o-mini"
            }
        }
        
        with patch('shared.llm_analysis_service.LLMAnalyzerFactory', mock_factory), \
             patch('shared.webpubsub_utils.send_progress') as mock_progress:
            
            from activity_llm_analysis import main
            
            result = main(input_data)
            
            mock_factory.create.assert_called_once_with(
                provider="openai",
                api_key="test-key",
                model="gpt-4o-mini"
            )
            mock_analyzer.analyze.assert_called_once_with("AAPL")
            
            assert result["type"] == "llm_analysis"
            assert result["data"]["success"] is True
            assert mock_progress.call_count == 2
    
    def test_main_with_different_provider(self):
        """Test main function works with different LLM providers."""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = {"success": True, "analysis": {}}
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_analyzer
        
        input_data = {
            "ticker": "MSFT",
            "task_id": "test-456",
            "llm_config": {
                "provider": "anthropic",
                "api_key": "anthropic-key",
                "model": "claude-haiku-4-5"
            }
        }
        
        with patch('shared.llm_analysis_service.LLMAnalyzerFactory', mock_factory), \
             patch('shared.webpubsub_utils.send_progress'):
            
            from activity_llm_analysis import main
            
            result = main(input_data)
            
            mock_factory.create.assert_called_once_with(
                provider="anthropic",
                api_key="anthropic-key",
                model="claude-haiku-4-5"
            )
            assert result["type"] == "llm_analysis"
