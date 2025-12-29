"""Stock-related API endpoints."""
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
    description="Search for stocks by partial ticker symbol or company name. Returns matching stocks with their ticker, name, and exchange."
)
async def search_stocks(
    q: str = Query(
        ...,
        min_length=1,
        max_length=20,
        description="Search query (ticker symbol or company name)"
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return"
    )
) -> StockSearchResponse:
    """
    Search for stocks by partial ticker or company name.
    
    This endpoint provides autocomplete functionality for stock search.
    
    Args:
        q: Search query string
        limit: Maximum number of results (default: 10, max: 50)
        
    Returns:
        StockSearchResponse with matching stocks
    """
    try:
        results = stock_service.autocomplete(q, limit=limit)
        return StockSearchResponse(
            query=q,
            results=results,
            count=len(results)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching for stocks: {str(e)}"
        )


@router.get(
    "/stocks/{ticker}/validate",
    response_model=TickerValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate a ticker symbol",
    description="Check if a ticker symbol is valid and exists in the market."
)
async def validate_ticker(ticker: str) -> TickerValidationResponse:
    """
    Validate that a ticker symbol exists.
    
    Args:
        ticker: Stock ticker symbol to validate (e.g., 'AAPL')
        
    Returns:
        TickerValidationResponse indicating if the ticker is valid
    """
    try:
        ticker_upper = ticker.upper()
        is_valid = stock_service.validate_ticker(ticker_upper)
        
        if is_valid:
            return TickerValidationResponse(
                ticker=ticker_upper,
                valid=True,
                message=f"Ticker '{ticker_upper}' is valid"
            )
        else:
            return TickerValidationResponse(
                ticker=ticker_upper,
                valid=False,
                message=f"Ticker '{ticker_upper}' was not found or is invalid"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating ticker: {str(e)}"
        )


@router.get(
    "/stocks/{ticker}",
    status_code=status.HTTP_200_OK,
    summary="Get stock data",
    description="Fetch detailed stock data including price history and company information."
)
async def get_stock_data(
    ticker: str,
    period: str = Query(
        default="1y",
        description="Time period for historical data (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)"
    )
) -> dict:
    """
    Get stock data including price history and company info.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        period: Time period for historical data
        
    Returns:
        Dict with company_info, price_history, and current_price
    """
    valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    if period not in valid_periods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
        )
    
    try:
        data = stock_service.fetch_stock_data(ticker, period=period)
        
        if data["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=data["error"]
            )
        
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching stock data: {str(e)}"
        )
