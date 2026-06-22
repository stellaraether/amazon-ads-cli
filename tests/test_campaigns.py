"""Tests for campaign commands."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from amazon_ads_cli.main import cli


class TestCampaigns:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_list_campaigns(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_campaigns.return_value = Mock(payload={"campaigns": []})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["campaigns", "list"])
        assert result.exit_code == 0

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_pause_campaign(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.edit_campaigns.return_value = Mock(payload={})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["campaigns", "pause", "camp-123"])
        assert result.exit_code == 0
        assert "paused" in result.output
        mock_client.edit_campaigns.assert_called_once()

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_enable_campaign(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.edit_campaigns.return_value = Mock(payload={})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["campaigns", "enable", "camp-123"])
        assert result.exit_code == 0
        assert "enabled" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_set_budget(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.edit_campaigns.return_value = Mock(payload={})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["campaigns", "budget", "camp-123", "50.0"])
        assert result.exit_code == 0
        assert "$50.0" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_set_bidding(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_campaigns.return_value = Mock(
            payload={
                "campaigns": [
                    {
                        "campaignId": "camp-123",
                        "dynamicBidding": {
                            "strategy": "LEGACY_FOR_SALES",
                            "placementBidding": [{"placement": "PLACEMENT_TOP", "percentage": 25}],
                        },
                    }
                ]
            }
        )
        mock_client.edit_campaigns.return_value = Mock(payload={})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["campaigns", "bidding", "camp-123", "--strategy", "AUTO_FOR_SALES"])
        assert result.exit_code == 0
        assert "AUTO_FOR_SALES" in result.output
        mock_client.edit_campaigns.assert_called_once()
        call_body = mock_client.edit_campaigns.call_args[1]["body"]
        assert call_body["campaigns"][0]["dynamicBidding"]["strategy"] == "AUTO_FOR_SALES"
        assert call_body["campaigns"][0]["dynamicBidding"]["placementBidding"] == [
            {"placement": "PLACEMENT_TOP", "percentage": 25}
        ]

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_set_placement(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_campaigns.return_value = Mock(
            payload={
                "campaigns": [
                    {
                        "campaignId": "camp-123",
                        "dynamicBidding": {"strategy": "AUTO_FOR_SALES", "placementBidding": []},
                    }
                ]
            }
        )
        mock_client.edit_campaigns.return_value = Mock(payload={})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli, ["campaigns", "placement", "camp-123", "--top-of-search", "50", "--product-page", "20"]
        )
        assert result.exit_code == 0
        assert "PLACEMENT_TOP" in result.output
        mock_client.edit_campaigns.assert_called_once()
        call_body = mock_client.edit_campaigns.call_args[1]["body"]
        dynamic_bidding = call_body["campaigns"][0]["dynamicBidding"]
        assert dynamic_bidding["strategy"] == "AUTO_FOR_SALES"
        assert dynamic_bidding["placementBidding"] == [
            {"placement": "PLACEMENT_TOP", "percentage": 50.0},
            {"placement": "PLACEMENT_PRODUCT_PAGE", "percentage": 20.0},
        ]

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_set_placement_requires_option(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_campaigns.return_value = Mock(
            payload={"campaigns": [{"campaignId": "camp-123", "dynamicBidding": {"strategy": "AUTO_FOR_SALES"}}]}
        )
        mock_client.edit_campaigns.return_value = Mock(payload={})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["campaigns", "placement", "camp-123"])
        assert result.exit_code != 0
        mock_client.edit_campaigns.assert_not_called()
