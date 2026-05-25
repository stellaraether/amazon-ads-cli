"""Tests for target commands."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from amazon_ads_cli.main import cli


class TestTargets:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_list_all_targets(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_product_targets.return_value = Mock(payload={"productTargets": []})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["targets", "list-all"])
        assert result.exit_code == 0

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_delete_target(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.delete_product_targets.return_value = Mock(payload={})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["targets", "delete", "tgt-123"])
        assert result.exit_code == 0
        assert "Deleted target" in result.output
