"""Stock-related API endpoints.

Note: Stock data fetching is handled by Azure Functions.
This route only handles search/autocomplete for the search bar.
"""
from typing import List
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.models.schemas import StockSearchResult
from app.services import stock_service

router = APIRouter()


class TickerValidationResponse(BaseModel):
    """Response for ticker validation endpoint."""
    ticker: str
    valid: bool
    message: str


class StockSearchResponse(BaseModel):
    """Response for stock search endpoint."""
    query: str
    results: List[StockSearchResult]
    count: int


@router.get(
    "/stocks/search",
    response_model=StockSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search for stocks",
    description="Search for stocks by partial ticker symbol or company name."
)
async def search_stocks(
    q: str = Query(..., min_length=1, max_length=20, description="Search query"),
    limit: int = Query(default=10, ge=1, le=50, description="Max results")
) -> StockSearchResponse:
    """Search for stocks by partial ticker or company name."""
    try:
        results = stock_service.autocomplete(q, limit=limit)
        return StockSearchResponse(query=q, results=results, count=len(results))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching: {str(e)}")


@router.get(
    "/stocks/{ticker}/validate",
    response_model=TickerValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate a ticker symbol"
)
async def validate_ticker(ticker: str) -> TickerValidationResponse:
    """Validate that a ticker symbol exists."""
    try:
        ticker_upper = ticker.upper()
        is_valid = stock_service.validate_ticker(ticker_upper)
        return TickerValidationResponse(
            ticker=ticker_upper,
            valid=is_valid,
            message=f"Ticker '{ticker_upper}' is {'valid' if is_valid else 'not found'}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating: {str(e)}")
