"""Mock responses for Alpha Vantage API testing."""
import responses

BASE_URL = "https://www.alphavantage.co/query"

MOCK_DAILY_RESPONSE = {
    "Meta Data": {
        "1. Information": "Daily Prices (open, high, low, close) and Volumes",
        "2. Symbol": "AAPL",
        "3. Last Refreshed": "2024-01-02",
        "4. Output Size": "Compact",
        "5. Time Zone": "US/Eastern"
    },
    "Time Series (Daily)": {
        "2024-01-02": {
            "1. open": "151.0",
            "2. high": "156.0",
            "3. low": "149.0",
            "4. close": "153.0",
            "5. volume": "1100000"
        },
        "2024-01-01": {
            "1. open": "150.0",
            "2. high": "155.0",
            "3. low": "148.0",
            "4. close": "152.0",
            "5. volume": "1000000"
        }
    }
}

MOCK_OVERVIEW_RESPONSE = {
    "Symbol": "AAPL",
    "Name": "Apple Inc.",
    "Description": "Apple Inc. designs, manufactures, and markets smartphones.",
    "Sector": "Technology",
    "Industry": "Consumer Electronics",
    "MarketCapitalization": "3000000000000",
    "PERatio": "28.5",
    "PEGRatio": "2.1",
    "BookValue": "4.25",
    "DividendYield": "0.005",
    "EPS": "6.15",
    "RevenueTTM": "383000000000",
    "ProfitMargin": "0.25",
    "52WeekHigh": "199.62",
    "52WeekLow": "124.17",
    "50DayMovingAverage": "178.50",
    "200DayMovingAverage": "165.30",
    "AnalystTargetPrice": "195.00"
}

MOCK_RATE_LIMIT_RESPONSE = {
    "Note": "Thank you for using Alpha Vantage! Our standard API rate limit is 25 requests per day."
}

MOCK_ERROR_RESPONSE = {
    "Error Message": "Invalid API call. Please retry or visit the documentation."
}


def setup_alpha_vantage_mocks(
    daily_response=None,
    overview_response=None,
    rate_limited=False,
    error=False
):
    """Set up responses mocks for Alpha Vantage API.
    
    Args:
        daily_response: Custom daily prices response (uses default if None)
        overview_response: Custom overview response (uses default if None)
        rate_limited: If True, return rate limit response
        error: If True, return error response
    """
    if rate_limited:
        responses.add(
            responses.GET,
            BASE_URL,
            json=MOCK_RATE_LIMIT_RESPONSE,
            status=200
        )
        return
    
    if error:
        responses.add(
            responses.GET,
            BASE_URL,
            json=MOCK_ERROR_RESPONSE,
            status=200
        )
        return
    
    # Add daily prices mock
    responses.add(
        responses.GET,
        BASE_URL,
        json=daily_response or MOCK_DAILY_RESPONSE,
        status=200
    )
    
    # Add overview mock
    responses.add(
        responses.GET,
        BASE_URL,
        json=overview_response or MOCK_OVERVIEW_RESPONSE,
        status=200
    )
