"""Tests for ad group commands."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from amazon_ads_cli.main import cli


class TestAdGroups:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_list_adgroups(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_ad_groups.return_value = Mock(payload={"adGroups": []})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "list"])
        assert result.exit_code == 0
