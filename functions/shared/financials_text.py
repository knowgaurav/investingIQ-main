"""Convert Alpha Vantage quarterly statements into readable text passages for RAG."""


def _money(value) -> str:
    """Format a numeric string as an abbreviated dollar amount."""
    if value in (None, "", "None", "-"):
        return "N/A"
    try:
        num = float(value)
    except (ValueError, TypeError):
        return str(value)

    sign = "-" if num < 0 else ""
    abs_num = abs(num)
    if abs_num >= 1e9:
        return f"{sign}${abs_num / 1e9:.2f}B"
    if abs_num >= 1e6:
        return f"{sign}${abs_num / 1e6:.2f}M"
    return f"{sign}${abs_num:,.0f}"


def income_statement_to_text(ticker: str, fiscal_quarter: str, report: dict) -> str:
    """Build a passage describing the quarterly income statement."""
    return (
        f"{ticker} — Income Statement (fiscal quarter ending {fiscal_quarter})\n"
        f"Total revenue: {_money(report.get('totalRevenue'))}; "
        f"Gross profit: {_money(report.get('grossProfit'))}; "
        f"Operating income: {_money(report.get('operatingIncome'))}; "
        f"Net income: {_money(report.get('netIncome'))}; "
        f"EBITDA: {_money(report.get('ebitda'))}; "
        f"Cost of revenue: {_money(report.get('costOfRevenue'))}."
    )


def balance_sheet_to_text(ticker: str, fiscal_quarter: str, report: dict) -> str:
    """Build a passage describing the quarterly balance sheet."""
    return (
        f"{ticker} — Balance Sheet (fiscal quarter ending {fiscal_quarter})\n"
        f"Total assets: {_money(report.get('totalAssets'))}; "
        f"Total liabilities: {_money(report.get('totalLiabilities'))}; "
        f"Total shareholder equity: {_money(report.get('totalShareholderEquity'))}; "
        f"Cash and equivalents: {_money(report.get('cashAndCashEquivalentsAtCarryingValue'))}; "
        f"Total current assets: {_money(report.get('totalCurrentAssets'))}; "
        f"Total current liabilities: {_money(report.get('totalCurrentLiabilities'))}; "
        f"Long-term debt: {_money(report.get('longTermDebt'))}."
    )


def cash_flow_to_text(ticker: str, fiscal_quarter: str, report: dict) -> str:
    """Build a passage describing the quarterly cash flow statement."""
    return (
        f"{ticker} — Cash Flow (fiscal quarter ending {fiscal_quarter})\n"
        f"Operating cash flow: {_money(report.get('operatingCashflow'))}; "
        f"Capital expenditures: {_money(report.get('capitalExpenditures'))}; "
        f"Cash flow from investment: {_money(report.get('cashflowFromInvestment'))}; "
        f"Cash flow from financing: {_money(report.get('cashflowFromFinancing'))}; "
        f"Dividend payout: {_money(report.get('dividendPayout'))}; "
        f"Net income: {_money(report.get('netIncome'))}."
    )


def earnings_to_text(ticker: str, fiscal_quarter: str, earnings: dict) -> str:
    """Build a passage describing the latest quarterly earnings."""
    quarterly = earnings.get("quarterly_earnings", [])
    latest = quarterly[0] if quarterly else {}
    reported = latest.get("reported_eps")
    estimated = latest.get("estimated_eps")
    surprise_pct = latest.get("surprise_pct")
    return (
        f"{ticker} — Earnings (fiscal quarter ending {fiscal_quarter})\n"
        f"Reported EPS: {reported if reported is not None else 'N/A'}; "
        f"Estimated EPS: {estimated if estimated is not None else 'N/A'}; "
        f"Surprise: {surprise_pct if surprise_pct is not None else 'N/A'}%."
    )
