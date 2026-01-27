"""Tests for Alpha Vantage API client."""
import pytest
import responses
from unittest.mock import patch, MagicMock

from shared.alpha_vantage import (
    get_api_keys,
    get_api_key,
    safe_float,
    safe_int,
    fetch_daily_prices,
    fetch_company_overview,
    BASE_URL,
)
from tests.mocks.alpha_vantage_mocks import (
    MOCK_DAILY_RESPONSE,
    MOCK_OVERVIEW_RESPONSE,
    MOCK_RATE_LIMIT_RESPONSE,
    MOCK_ERROR_RESPONSE,
)


class TestGetApiKeys:
    """Tests for get_api_keys function."""

    def test_single_key(self):
        """Test with single ALPHA_VANTAGE_API_KEY."""
        with patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "key1"}, clear=True):
            keys = get_api_keys()
            assert keys == ["key1"]

    def test_multiple_keys(self):
        """Test with comma-separated ALPHA_VANTAGE_API_KEYS."""
        with patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEYS": "key1,key2,key3"}, clear=True):
            keys = get_api_keys()
            assert keys == ["key1", "key2", "key3"]

    def test_multiple_keys_with_spaces(self):
        """Test keys with whitespace are trimmed."""
        with patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEYS": " key1 , key2 , key3 "}, clear=True):
            keys = get_api_keys()
            assert keys == ["key1", "key2", "key3"]

    def test_no_keys(self):
        """Test returns empty list when no keys configured."""
        with patch.dict("os.environ", {}, clear=True):
            keys = get_api_keys()
            assert keys == []


class TestGetApiKey:
    """Tests for get_api_key rotation."""

    def test_single_key_returns_same(self):
        """Single key always returns that key."""
        with patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "only_key"}, clear=True):
            key = get_api_key()
            assert key == "only_key"

    def test_no_keys_raises(self):
        """No keys configured raises ValueError."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="No Alpha Vantage API keys"):
                get_api_key()

    def test_rotation_with_redis(self):
        """Multiple keys rotate via Redis."""
        mock_redis = MagicMock()
        mock_redis.incr.side_effect = [1, 2, 3, 4]
        
        with patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEYS": "k1,k2,k3"}, clear=True):
            with patch("shared.alpha_vantage._get_redis", return_value=mock_redis):
                assert get_api_key() == "k1"
                assert get_api_key() == "k2"
                assert get_api_key() == "k3"
                assert get_api_key() == "k1"  # Wraps around

    def test_redis_error_fallback(self):
        """Redis error falls back to first key."""
        mock_redis = MagicMock()
        mock_redis.incr.side_effect = Exception("Redis down")
        
        with patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEYS": "k1,k2"}, clear=True):
            with patch("shared.alpha_vantage._get_redis", return_value=mock_redis):
                key = get_api_key()
                assert key == "k1"


class TestSafeFloat:
    """Tests for safe_float conversion."""

    def test_valid_float(self):
        assert safe_float("3.14") == 3.14

    def test_valid_int_string(self):
        assert safe_float("42") == 42.0

    def test_none(self):
        assert safe_float(None) is None

    def test_empty_string(self):
        assert safe_float("") is None

    def test_dash(self):
        assert safe_float("-") is None

    def test_none_string(self):
        assert safe_float("None") is None

    def test_invalid_string(self):
        assert safe_float("abc") is None


class TestSafeInt:
    """Tests for safe_int conversion."""

    def test_valid_int(self):
        assert safe_int("42") == 42

    def test_float_string_truncates(self):
        assert safe_int("3.9") == 3

    def test_none(self):
        assert safe_int(None) is None

    def test_empty_string(self):
        assert safe_int("") is None

    def test_dash(self):
        assert safe_int("-") is None

    def test_invalid_string(self):
        assert safe_int("abc") is None


class TestFetchDailyPrices:
    """Tests for fetch_daily_prices with mocked responses."""

    @responses.activate
    def test_success(self):
        """Test successful price fetch."""
        responses.add(responses.GET, BASE_URL, json=MOCK_DAILY_RESPONSE, status=200)
        
        with patch("shared.alpha_vantage.get_api_key", return_value="test_key"):
            result = fetch_daily_prices("AAPL")
        
        assert result["ticker"] == "AAPL"
        assert len(result["price_history"]) == 2
        assert result["current_price"] == 153.0
        assert result["price_history"][0]["date"] == "2024-01-01"
        assert result["price_history"][1]["date"] == "2024-01-02"

    @responses.activate
    def test_rate_limit(self):
        """Test rate limit response handling."""
        responses.add(responses.GET, BASE_URL, json=MOCK_RATE_LIMIT_RESPONSE, status=200)
        
        with patch("shared.alpha_vantage.get_api_key", return_value="test_key"):
            result = fetch_daily_prices("AAPL")
        
        assert result["ticker"] == "AAPL"
        assert result["price_history"] == []
        assert result.get("_rate_limited") is True

    @responses.activate
    def test_error_response(self):
        """Test error response handling."""
        responses.add(responses.GET, BASE_URL, json=MOCK_ERROR_RESPONSE, status=200)
        
        with patch("shared.alpha_vantage.get_api_key", return_value="test_key"):
            result = fetch_daily_prices("INVALID")
        
        assert result["ticker"] == "INVALID"
        assert result["price_history"] == []
        assert "error" in result

    @responses.activate
    def test_network_error(self):
        """Test network error handling."""
        responses.add(responses.GET, BASE_URL, body=Exception("Network error"))
        
        with patch("shared.alpha_vantage.get_api_key", return_value="test_key"):
            result = fetch_daily_prices("AAPL")
        
        assert result["ticker"] == "AAPL"
        assert result["price_history"] == []
        assert "error" in result


class TestFetchCompanyOverview:
    """Tests for fetch_company_overview with mocked responses."""

    @responses.activate
    def test_success(self):
        """Test successful overview fetch."""
        responses.add(responses.GET, BASE_URL, json=MOCK_OVERVIEW_RESPONSE, status=200)
        
        with patch("shared.alpha_vantage.get_api_key", return_value="test_key"):
            result = fetch_company_overview("AAPL")
        
        assert result["name"] == "Apple Inc."
        assert result["sector"] == "Technology"
        assert result["industry"] == "Consumer Electronics"
        assert result["market_cap"] == 3000000000000
        assert result["pe_ratio"] == 28.5

    @responses.activate
    def test_rate_limit(self):
        """Test rate limit response handling."""
        responses.add(responses.GET, BASE_URL, json=MOCK_RATE_LIMIT_RESPONSE, status=200)
        
        with patch("shared.alpha_vantage.get_api_key", return_value="test_key"):
            result = fetch_company_overview("AAPL")
        
        assert result["name"] == "AAPL"
        assert result.get("_rate_limited") is True

    @responses.activate
    def test_empty_response(self):
        """Test empty response handling."""
        responses.add(responses.GET, BASE_URL, json={}, status=200)
        
        with patch("shared.alpha_vantage.get_api_key", return_value="test_key"):
            result = fetch_company_overview("UNKNOWN")
        
        assert result["name"] == "UNKNOWN"
        assert result["sector"] is None


# Property-Based Tests
from hypothesis import given, strategies as st, settings


class TestApiKeyRotationProperty:
    """Property-based tests for API key rotation.
    
    **Feature: functions-testing-setup, Property 2: API Key Rotation Distribution**
    **Validates: Requirements 6.1**
    """

    @settings(max_examples=100)
    @given(st.lists(st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"), min_size=2, max_size=10, unique=True))
    def test_rotation_distribution(self, keys):
        """For any list of N API keys (N > 1), after N consecutive calls to get_api_key(),
        each key SHALL have been returned exactly once (round-robin distribution).
        """
        if len(keys) < 2:
            return
        
        mock_redis = MagicMock()
        call_count = [0]
        
        def mock_incr(key):
            call_count[0] += 1
            return call_count[0]
        
        mock_redis.incr.side_effect = mock_incr
        
        keys_str = ",".join(keys)
        returned_keys = []
        
        with patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEYS": keys_str}, clear=True):
            with patch("shared.alpha_vantage._get_redis", return_value=mock_redis):
                for _ in range(len(keys)):
                    returned_keys.append(get_api_key())
        
        # Each key should appear exactly once in N calls
        assert sorted(returned_keys) == sorted(keys)


class TestSafeConversionProperty:
    """Property-based tests for safe conversion functions.
    
    **Feature: functions-testing-setup, Property 5: Safe Conversion Functions**
    **Validates: Requirements 6.5**
    """

    @settings(max_examples=100)
    @given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
    def test_safe_float_valid_numeric(self, value):
        """For any valid numeric string, safe_float SHALL return the correct float value."""
        str_value = str(value)
        result = safe_float(str_value)
        assert result is not None
        assert abs(result - value) < 1e-6 or (value != 0 and abs((result - value) / value) < 1e-6)

    @settings(max_examples=100)
    @given(st.integers(min_value=-10**9, max_value=10**9))
    def test_safe_float_integer_string(self, value):
        """For any integer string, safe_float SHALL return the correct float value."""
        result = safe_float(str(value))
        assert result == float(value)

    @settings(max_examples=100)
    @given(st.sampled_from([None, "", "-", "None", "abc", "not_a_number", "NaN"]))
    def test_safe_float_invalid_returns_none(self, value):
        """For any invalid input, safe_float SHALL return None."""
        result = safe_float(value)
        assert result is None

    @settings(max_examples=100)
    @given(st.integers(min_value=-10**9, max_value=10**9))
    def test_safe_int_valid_integer(self, value):
        """For any valid integer string, safe_int SHALL return the correct int value."""
        result = safe_int(str(value))
        assert result == value

    @settings(max_examples=100)
    @given(st.sampled_from([None, "", "-", "None", "abc", "not_a_number"]))
    def test_safe_int_invalid_returns_none(self, value):
        """For any invalid input, safe_int SHALL return None."""
        result = safe_int(value)
        assert result is None
