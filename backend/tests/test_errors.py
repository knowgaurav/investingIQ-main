"""Tests for error handling utilities."""
import pytest
from uuid import uuid4

from app.utils.errors import (
    AppError,
    ErrorCode,
    ErrorResponse,
    ValidationError,
    NotFoundError,
    TickerNotFoundError,
    ExternalServiceError,
    LLMError,
    DatabaseError,
    generate_request_id,
)


class TestErrorCode:
    """Tests for ErrorCode enum."""
    
    def test_error_codes_are_strings(self):
        """Test that error codes are string values."""
        assert isinstance(ErrorCode.INTERNAL_ERROR.value, str)
        assert ErrorCode.INTERNAL_ERROR.value == "E1000"
    
    def test_error_codes_follow_pattern(self):
        """Test that error codes follow the Exxxx pattern."""
        for code in ErrorCode:
            assert code.value.startswith("E")
            assert len(code.value) == 5
            assert code.value[1:].isdigit()


class TestAppError:
    """Tests for AppError base class."""
    
    def test_app_error_creation(self):
        """Test creating an AppError."""
        error = AppError(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Something went wrong",
            status_code=500,
            details={"component": "test"},
        )
        
        assert error.error_code == ErrorCode.INTERNAL_ERROR
        assert error.message == "Something went wrong"
        assert error.status_code == 500
        assert error.details == {"component": "test"}
    
    def test_app_error_to_response(self):
        """Test converting AppError to response."""
        request_id = str(uuid4())
        error = AppError(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Invalid input",
            status_code=400,
        )
        
        response = error.to_response(request_id)
        
        assert isinstance(response, ErrorResponse)
        assert response.success is False
        assert response.error_code == "E1001"
        assert response.message == "Invalid input"
        assert response.request_id == request_id
    
    def test_app_error_with_original_error(self):
        """Test AppError with original exception."""
        original = ValueError("Original error")
        error = AppError(
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            message="Service failed",
            original_error=original,
        )
        
        assert error.original_error is original


class TestSpecificErrors:
    """Tests for specific error classes."""
    
    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError(
            message="Field 'ticker' is required",
            details={"field": "ticker"},
        )
        
        assert error.error_code == ErrorCode.VALIDATION_ERROR
        assert error.status_code == 400
        assert error.details["field"] == "ticker"
    
    def test_not_found_error(self):
        """Test NotFoundError."""
        error = NotFoundError(resource="Report", identifier="123")
        
        assert error.error_code == ErrorCode.NOT_FOUND
        assert error.status_code == 404
        assert "Report '123' not found" in error.message
        assert error.details["resource"] == "Report"
        assert error.details["identifier"] == "123"
    
    def test_ticker_not_found_error(self):
        """Test TickerNotFoundError."""
        error = TickerNotFoundError(ticker="INVALID")
        
        assert error.error_code == ErrorCode.TICKER_NOT_FOUND
        assert error.status_code == 404
        assert "INVALID" in error.message
        assert error.details["ticker"] == "INVALID"
    
    def test_external_service_error(self):
        """Test ExternalServiceError."""
        original = ConnectionError("Connection refused")
        error = ExternalServiceError(
            service="yfinance",
            message="Connection refused",
            original_error=original,
        )
        
        assert error.error_code == ErrorCode.EXTERNAL_SERVICE_ERROR
        assert error.status_code == 502
        assert "yfinance" in error.message
        assert error.original_error is original
    
    def test_llm_error(self):
        """Test LLMError."""
        error = LLMError(message="Rate limit exceeded")
        
        assert error.error_code == ErrorCode.LLM_UNAVAILABLE
        assert error.status_code == 503
        assert "Rate limit exceeded" in error.message
    
    def test_database_error(self):
        """Test DatabaseError."""
        error = DatabaseError(message="Connection pool exhausted")
        
        assert error.error_code == ErrorCode.DATABASE_ERROR
        assert error.status_code == 500


class TestErrorResponse:
    """Tests for ErrorResponse model."""
    
    def test_error_response_creation(self):
        """Test creating an ErrorResponse."""
        response = ErrorResponse(
            error_code="E1000",
            message="Test error",
            request_id="test-123",
        )
        
        assert response.success is False
        assert response.error_code == "E1000"
        assert response.message == "Test error"
        assert response.details is None
    
    def test_error_response_with_details(self):
        """Test ErrorResponse with details."""
        response = ErrorResponse(
            error_code="E2001",
            message="Ticker not found",
            details={"ticker": "INVALID", "suggestions": ["AAPL", "GOOGL"]},
            request_id="test-456",
        )
        
        assert response.details["ticker"] == "INVALID"
        assert "AAPL" in response.details["suggestions"]


class TestGenerateRequestId:
    """Tests for generate_request_id function."""
    
    def test_generates_uuid_format(self):
        """Test that request IDs are valid UUID format."""
        request_id = generate_request_id()
        
        # Should be valid UUID format (36 chars with hyphens)
        assert len(request_id) == 36
        assert request_id.count("-") == 4
    
    def test_generates_unique_ids(self):
        """Test that request IDs are unique."""
        ids = {generate_request_id() for _ in range(100)}
        assert len(ids) == 100  # All unique
