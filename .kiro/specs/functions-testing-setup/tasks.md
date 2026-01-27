# Implementation Plan: Functions Testing Setup

## Overview

This plan implements comprehensive testing infrastructure for the InvestingIQ Azure Functions (Python) application using pytest. The implementation uses Python as specified in the existing codebase.

## Tasks

- [x] 1. Install pytest and configure test environment
  - [x] 1.1 Update requirements.txt with test dependencies
    - Add pytest, pytest-cov, pytest-asyncio, responses, hypothesis
    - _Requirements: 9.1_
  - [x] 1.2 Create pytest.ini configuration
    - Configure testpaths, asyncio_mode, markers
    - Configure coverage source and fail_under=80
    - _Requirements: 1.1, 1.2, 1.6, 2.1, 2.2, 2.3_
  - [x] 1.3 Create tests directory structure
    - Create tests/, tests/mocks/, tests/unit/, tests/activities/
    - Create __init__.py files
    - _Requirements: 1.5_

- [x] 2. Create mock infrastructure and fixtures
  - [x] 2.1 Create tests/conftest.py with shared fixtures
    - MockRedis class with get, setex, delete, incr
    - mock_redis and mock_redis_client fixtures
    - mock_stock_data and mock_llm_response fixtures
    - _Requirements: 3.1, 3.2, 3.4_
  - [x] 2.2 Create tests/mocks/alpha_vantage_mocks.py
    - Mock responses for daily prices, overview, rate limits
    - setup_alpha_vantage_mocks helper function
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  - [x] 2.3 Create tests/mocks/llm_mocks.py
    - create_mock_openai_client function
    - create_mock_anthropic_client function
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 3. Write shared utilities tests
  - [x] 3.1 Create tests/unit/test_alpha_vantage.py
    - Test get_api_keys with single and multiple keys
    - Test get_api_key rotation
    - Test safe_float and safe_int conversions
    - Test fetch_daily_prices with mocked responses
    - Test fetch_company_overview with mocked responses
    - Test error and rate limit handling
    - _Requirements: 6.1, 6.5_
  - [x] 3.2 Write property test for API key rotation
    - **Property 2: API Key Rotation Distribution**
    - **Validates: Requirements 6.1**
  - [x] 3.3 Write property test for safe conversion functions
    - **Property 5: Safe Conversion Functions**
    - **Validates: Requirements 6.5**
  - [x] 3.4 Create tests/unit/test_cache.py
    - Test RedisClient get, set, delete operations
    - Test StockCache get/set for prices, company_info, news, earnings
    - _Requirements: 6.2_
  - [x] 3.5 Write property test for StockCache round-trip
    - **Property 3: StockCache Round-Trip**
    - **Validates: Requirements 6.2**
  - [x] 3.6 Create tests/unit/test_config.py
    - Test get_settings loads from environment
    - Test default values when env vars not set
    - _Requirements: 6.3_
  - [x] 3.7 Create tests/unit/test_llm_factory.py
    - Test LLMProviderFactory.create for each provider
    - Test get_supported_providers returns all providers
    - Test invalid provider raises ValueError
    - _Requirements: 6.4_
  - [x] 3.8 Write property test for LLM factory provider creation
    - **Property 4: LLM Factory Provider Creation**
    - **Validates: Requirements 6.4**

- [x] 4. Checkpoint - Verify shared utility tests pass
  - Run `pytest tests/unit/ -v` and ensure all tests pass
  - Ask user if questions arise

- [x] 5. Write activity function tests
  - [x] 5.1 Create tests/activities/test_activity_fetch.py
    - Test main function fetches stock data and news
    - Test with mocked Alpha Vantage responses
    - _Requirements: 7.1_
  - [x] 5.2 Create tests/activities/test_activity_cache.py
    - Test main function caches all data types
    - Test with mock Redis client
    - _Requirements: 7.2_
  - [x] 5.3 Create tests/activities/test_activity_llm.py
    - Test main function creates analyzer and runs analysis
    - Test with mock LLM client
    - _Requirements: 7.3_
  - [x] 5.4 Create tests/activities/test_activity_ml.py
    - Test main function runs all ML models
    - Test with mock ML functions
    - _Requirements: 7.4_
  - [x] 5.5 Create tests/activities/test_activity_aggregate.py
    - Test main function aggregates results correctly
    - Test with mock database save
    - _Requirements: 7.5_

- [x] 6. Checkpoint - Verify all tests pass with coverage
  - Run `pytest --cov --cov-fail-under=80` and ensure coverage threshold met
  - Ask user if questions arise

- [x] 7. Set up GitHub Actions CI
  - [x] 7.1 Create .github/workflows/functions-tests.yml
    - Trigger on PR to main/master for functions/** paths
    - Use Python 3.11 with pip cache
    - Run pytest with coverage and 80% threshold
    - Upload coverage artifact
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [x] 8. Final checkpoint - Run full test suite
  - Run `pytest --cov --cov-report=html --cov-fail-under=80`
  - Verify all tests pass and coverage meets threshold
  - Ask user if questions arise

## Notes

- All tasks are required including property-based tests
- Property-based tests use hypothesis library for input generation
- All mocks use unittest.mock and responses library
- Coverage threshold of 80% enforced in CI
