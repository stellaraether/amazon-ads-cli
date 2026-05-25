"""Tests for ASIN target commands."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from amazon_ads_cli.main import cli


class TestAsinTargets:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_add_asin_target(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.create_product_targets.return_value = Mock(
            payload={"targetingClauses": {"success": [{"targetId": "tgt-123"}]}}
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["asin-targets", "add", "camp-123", "ag-123", "B09BBL8T4Z"])
        assert result.exit_code == 0
        assert "Added ASIN target" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_remove_asin_target(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.delete_product_targets.return_value = Mock(payload={})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["asin-targets", "remove", "tgt-123"])
        assert result.exit_code == 0
        assert "Removed ASIN target" in result.output
