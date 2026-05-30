"""Tests for the financials-to-text conversion module."""
from shared.financials_text import (
    income_statement_to_text,
    balance_sheet_to_text,
    cash_flow_to_text,
    earnings_to_text,
    _money,
)


class TestMoneyFormatting:
    def test_billions(self):
        assert _money("124300000000") == "$124.30B"

    def test_millions(self):
        assert _money("58270000") == "$58.27M"

    def test_negative(self):
        assert _money("-5000000000") == "-$5.00B"

    def test_missing(self):
        assert _money(None) == "N/A"
        assert _money("None") == "N/A"
        assert _money("-") == "N/A"


class TestStatementPassages:
    def test_income_statement_includes_quarter_and_metrics(self):
        text = income_statement_to_text("AAPL", "2024-12-31", {
            "totalRevenue": "124300000000",
            "netIncome": "36330000000",
        })
        assert "AAPL" in text
        assert "Income Statement" in text
        assert "2024-12-31" in text
        assert "$124.30B" in text

    def test_balance_sheet_includes_label(self):
        text = balance_sheet_to_text("MSFT", "2024-09-30", {"totalAssets": "500000000000"})
        assert "Balance Sheet" in text
        assert "2024-09-30" in text

    def test_cash_flow_includes_label(self):
        text = cash_flow_to_text("NVDA", "2024-10-31", {"operatingCashflow": "15000000000"})
        assert "Cash Flow" in text
        assert "$15.00B" in text

    def test_earnings_uses_latest_quarter(self):
        text = earnings_to_text("AAPL", "2024-12-31", {
            "quarterly_earnings": [
                {"reported_eps": 2.41, "estimated_eps": 2.35, "surprise_pct": 2.55},
            ]
        })
        assert "Earnings" in text
        assert "2.41" in text
