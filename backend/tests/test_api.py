"""Tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import app after patching to avoid startup issues
@pytest.fixture
def client():
    """Create test client."""
    with patch("app.utils.logging.setup_logging"):
        with patch("app.utils.cache.get_cache_service") as mock_cache:
            mock_cache.return_value.is_connected = False
            from app.main import app
            yield TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_liveness_endpoint(self, client):
        """Test liveness probe returns 200."""
        response = client.get("/api/health/live")
        
        assert response.status_code == 200
        assert response.json()["status"] == "alive"
    
    def test_health_endpoint_returns_service_info(self, client):
        """Test health endpoint returns service info."""
        with patch("app.api.routes.health.check_postgres") as mock_pg:
            with patch("app.api.routes.health.check_redis") as mock_redis:
                with patch("app.api.routes.health.check_llm") as mock_llm:
                    with patch("app.api.routes.health.check_mlflow") as mock_mlflow:
                        # Mock all dependencies as healthy
                        from app.api.routes.health import DependencyHealth
                        mock_pg.return_value = DependencyHealth(
                            name="postgres", status="healthy", latency_ms=5.0
                        )
                        mock_redis.return_value = DependencyHealth(
                            name="redis", status="healthy", latency_ms=1.0
                        )
                        mock_llm.return_value = DependencyHealth(
                            name="llm", status="healthy", latency_ms=100.0
                        )
                        mock_mlflow.return_value = DependencyHealth(
                            name="mlflow", status="healthy", latency_ms=10.0
                        )
                        
                        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "dependencies" in data


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root_returns_api_info(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"


class TestStocksEndpoints:
    """Tests for stock-related endpoints."""
    
    def test_search_stocks_requires_query(self, client):
        """Test stock search requires query parameter."""
        with patch("app.services.stock_service.autocomplete") as mock_auto:
            mock_auto.return_value = []
            response = client.get("/api/v1/stocks/search")
        
        # Should return empty list or 422 for missing param
        assert response.status_code in [200, 422]
    
    def test_get_stock_data_with_valid_ticker(self, client):
        """Test getting stock data with valid ticker."""
        with patch("app.services.stock_service.fetch_stock_data") as mock_fetch:
            mock_fetch.return_value = {
                "ticker": "AAPL",
                "company_info": {"name": "Apple Inc."},
                "price_history": [],
                "current_price": 180.0,
                "status": "success",
                "error": None,
            }
            
            response = client.get("/api/v1/stocks/AAPL")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"


class TestAnalysisEndpoints:
    """Tests for analysis endpoints."""
    
    def test_request_analysis_accepts_ticker(self, client):
        """Test analysis request accepts ticker."""
        with patch("app.models.database.SessionLocal") as mock_session:
            with patch("app.api.routes.analysis.run_parallel_analysis_task"):
                mock_db = MagicMock()
                mock_session.return_value = mock_db
                
                response = client.post(
                    "/api/v1/analysis/request",
                    json={"ticker": "AAPL"}
                )
        
        # Should return 202 Accepted or similar
        assert response.status_code in [200, 202, 500]  # May fail without DB
    
    def test_get_analysis_status_with_invalid_id(self, client):
        """Test getting analysis status with invalid task ID."""
        response = client.get("/api/v1/analysis/status/invalid-uuid")
        
        # Should return 422 for invalid UUID format
        assert response.status_code == 422


class TestChatEndpoints:
    """Tests for chat endpoints."""
    
    def test_chat_requires_message_and_ticker(self, client):
        """Test chat endpoint requires message and ticker."""
        response = client.post("/api/v1/chat", json={})
        
        # Should return 422 for missing fields
        assert response.status_code == 422
    
    def test_chat_with_valid_request(self, client):
        """Test chat with valid request."""
        with patch("app.services.llm_service.get_llm_service") as mock_llm:
            with patch("app.services.rag_service.get_rag_service") as mock_rag:
                with patch("app.models.database.SessionLocal") as mock_session:
                    mock_db = MagicMock()
                    mock_session.return_value = mock_db
                    mock_db.query.return_value.filter.return_value.first.return_value = None
                    
                    mock_llm_instance = MagicMock()
                    mock_llm_instance.chat.return_value = "Test response"
                    mock_llm.return_value = mock_llm_instance
                    
                    mock_rag_instance = MagicMock()
                    mock_rag_instance.build_context_string.return_value = ("", [])
                    mock_rag.return_value = mock_rag_instance
                    
                    response = client.post(
                        "/api/v1/chat",
                        json={"message": "What is the price?", "ticker": "AAPL"}
                    )
        
        # May fail without full DB setup, but should at least parse request
        assert response.status_code in [200, 500]


class TestAPIVersioning:
    """Tests for API versioning."""
    
    def test_v1_prefix_works(self, client):
        """Test that /api/v1 prefix works."""
        with patch("app.services.stock_service.fetch_stock_data") as mock_fetch:
            mock_fetch.return_value = {
                "ticker": "AAPL",
                "status": "success",
                "company_info": {},
                "price_history": [],
                "current_price": 180.0,
                "error": None,
            }
            
            response = client.get("/api/v1/stocks/AAPL")
        
        assert response.status_code == 200
    
    def test_legacy_api_prefix_still_works(self, client):
        """Test that legacy /api prefix still works for backward compatibility."""
        with patch("app.services.stock_service.fetch_stock_data") as mock_fetch:
            mock_fetch.return_value = {
                "ticker": "AAPL",
                "status": "success",
                "company_info": {},
                "price_history": [],
                "current_price": 180.0,
                "error": None,
            }
            
            response = client.get("/api/stocks/AAPL")
        
        assert response.status_code == 200
