"""Tests for negative keyword commands."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from amazon_ads_cli.main import cli


class TestNegatives:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_list_negatives(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_negative_keywords.return_value = Mock(payload={"negativeKeywords": []})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["negatives", "list", "camp-123"])
        assert result.exit_code == 0

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_add_negative(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.create_negative_keyword.return_value = Mock(payload={})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["negatives", "add", "camp-123", "ag-123", "bad keyword"])
        assert result.exit_code == 0
        assert "Added negative keyword" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_remove_negative(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.delete_negative_keywords.return_value = Mock(payload={})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["negatives", "remove", "neg-123"])
        assert result.exit_code == 0
        assert "Removed negative keyword" in result.output
