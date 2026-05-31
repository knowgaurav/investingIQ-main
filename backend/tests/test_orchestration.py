"""Tests for the Durable Functions orchestration client and analysis route."""
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    with patch("app.utils.logging.setup_logging"):
        with patch("app.utils.cache.get_cache_service") as mock_cache:
            mock_cache.return_value.is_connected = False
            from app.main import app
            yield TestClient(app)


class TestOrchestrationClient:
    """Tests for OrchestrationClient.start_analysis."""

    def test_posts_expected_payload(self):
        from app.services.orchestration_client import OrchestrationClient

        with patch("app.services.orchestration_client.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=202)
            mock_post.return_value.raise_for_status = MagicMock()

            client = OrchestrationClient()
            client._starter_url = "http://func/api/orchestrator/start"
            client._functions_key = "secret"

            client.start_analysis("AAPL", "task-123", {"provider": "openai", "api_key": "k", "model": "m"}, "av-key")

            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            assert kwargs["params"] == {"code": "secret"}
            assert kwargs["json"]["ticker"] == "AAPL"
            assert kwargs["json"]["task_id"] == "task-123"
            assert kwargs["json"]["llm_config"]["provider"] == "openai"
            assert kwargs["json"]["alpha_vantage_key"] == "av-key"

    def test_no_key_sends_no_params(self):
        from app.services.orchestration_client import OrchestrationClient

        with patch("app.services.orchestration_client.requests.post") as mock_post:
            mock_post.return_value = MagicMock()
            mock_post.return_value.raise_for_status = MagicMock()

            client = OrchestrationClient()
            client._starter_url = "http://func/api/orchestrator/start"
            client._functions_key = ""

            client.start_analysis("MSFT", "task-456", None)

            _, kwargs = mock_post.call_args
            assert kwargs["params"] is None
            assert kwargs["json"]["llm_config"] is None


class TestAnalysisRoute:
    """Tests for the /analysis/request route using the orchestration client."""

    def test_request_returns_task_id(self, client):
        with patch("app.api.routes.analysis.get_orchestration_client") as mock_get:
            mock_client = MagicMock()
            mock_get.return_value = mock_client

            response = client.post("/api/v1/analysis/request", json={"ticker": "AAPL"})

            assert response.status_code == 202
            data = response.json()
            assert data["task_id"]
            assert data["status"] == "processing"
            mock_client.start_analysis.assert_called_once()

    def test_request_failure_returns_503(self, client):
        with patch("app.api.routes.analysis.get_orchestration_client") as mock_get:
            mock_client = MagicMock()
            mock_client.start_analysis.side_effect = RuntimeError("functions down")
            mock_get.return_value = mock_client

            response = client.post("/api/v1/analysis/request", json={"ticker": "AAPL"})

            assert response.status_code == 503
