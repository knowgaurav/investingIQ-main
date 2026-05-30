"""Tests for activity_financials_ingest function."""
from unittest.mock import patch, MagicMock

import shared.alpha_vantage as av
import shared.db_utils as db_utils
import shared.embedding_utils as embedding_utils
import shared.webpubsub_utils as webpubsub_utils


def _base_input():
    return {"ticker": "AAPL", "task_id": "test-123"}


def _statement(quarter):
    return {"fiscal_quarter": quarter, "report": {"totalRevenue": "1000000000"}}


class TestFinancialsIngest:
    def test_fetches_and_embeds_when_new(self):
        """When no stored financials exist, fetch, persist, and embed each statement."""
        with patch.object(av, 'fetch_income_statement', return_value=_statement("2024-12-31")), \
             patch.object(av, 'fetch_balance_sheet', return_value=_statement("2024-12-31")), \
             patch.object(av, 'fetch_cash_flow', return_value=_statement("2024-12-31")), \
             patch.object(av, 'fetch_earnings', return_value={"quarterly_earnings": [{"reported_eps": 2.41}]}), \
             patch.object(db_utils, 'get_quarterly_financials', return_value=None), \
             patch.object(db_utils, 'save_quarterly_financials') as mock_save, \
             patch.object(embedding_utils, 'embed_financials_passage') as mock_embed, \
             patch.object(webpubsub_utils, 'send_progress'):
            from activity_financials_ingest import main

            result = main(_base_input())

            assert result["status"] == "ok"
            assert result["fiscal_quarter"] == "2024-12-31"
            mock_save.assert_called_once()
            assert mock_embed.call_count >= 4

    def test_reuses_when_already_stored(self):
        """When financials already exist for the quarter, skip fetch/save/embed of new rows."""
        with patch.object(av, 'fetch_income_statement', return_value=_statement("2024-12-31")), \
             patch.object(av, 'fetch_balance_sheet', return_value=_statement("2024-12-31")), \
             patch.object(av, 'fetch_cash_flow', return_value=_statement("2024-12-31")), \
             patch.object(av, 'fetch_earnings', return_value={"quarterly_earnings": []}), \
             patch.object(db_utils, 'get_quarterly_financials', return_value={"id": "abc"}), \
             patch.object(db_utils, 'save_quarterly_financials') as mock_save, \
             patch.object(embedding_utils, 'embed_financials_passage') as mock_embed, \
             patch.object(webpubsub_utils, 'send_progress'):
            from activity_financials_ingest import main

            result = main(_base_input())

            assert result["status"] == "reused"
            assert result["fiscal_quarter"] == "2024-12-31"
            mock_save.assert_not_called()
            mock_embed.assert_not_called()

    def test_unavailable_when_no_quarter(self):
        """When no fiscal quarter is resolvable, return unavailable without raising."""
        with patch.object(av, 'fetch_income_statement', return_value=_statement(None)), \
             patch.object(av, 'fetch_balance_sheet', return_value=_statement(None)), \
             patch.object(av, 'fetch_cash_flow', return_value=_statement(None)), \
             patch.object(av, 'fetch_earnings', return_value={"quarterly_earnings": []}), \
             patch.object(db_utils, 'get_quarterly_financials', return_value=None), \
             patch.object(webpubsub_utils, 'send_progress'):
            from activity_financials_ingest import main

            result = main(_base_input())

            assert result["status"] == "unavailable"
            assert result["fiscal_quarter"] is None

    def test_never_raises_on_exception(self):
        """Exceptions during ingest are caught and returned as unavailable."""
        with patch.object(av, 'fetch_income_statement', side_effect=RuntimeError("api down")), \
             patch.object(webpubsub_utils, 'send_progress'):
            from activity_financials_ingest import main

            result = main(_base_input())

            assert result["status"] == "unavailable"
            assert "api down" in result["error"]
