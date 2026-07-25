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

        result = runner.invoke(cli, ["campaigns", "camp-123", "pause"])
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

        result = runner.invoke(cli, ["campaigns", "camp-123", "enable"])
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

        result = runner.invoke(cli, ["campaigns", "camp-123", "budget", "50.0"])
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

        result = runner.invoke(cli, ["campaigns", "camp-123", "bidding", "--strategy", "AUTO_FOR_SALES"])
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
            cli,
            [
                "campaigns",
                "camp-123",
                "placement",
                "--top-of-search",
                "50",
                "--product-page",
                "20",
                "--rest-of-search",
                "5",
            ],
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
            {"placement": "PLACEMENT_REST_OF_SEARCH", "percentage": 5.0},
        ]

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_set_placement_only_rest_of_search(self, mock_client_class, mock_auth_class, runner):
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

        result = runner.invoke(cli, ["campaigns", "camp-123", "placement", "--rest-of-search", "15"])
        assert result.exit_code == 0
        mock_client.edit_campaigns.assert_called_once()
        call_body = mock_client.edit_campaigns.call_args[1]["body"]
        dynamic_bidding = call_body["campaigns"][0]["dynamicBidding"]
        assert dynamic_bidding["placementBidding"] == [
            {"placement": "PLACEMENT_REST_OF_SEARCH", "percentage": 15.0},
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

        result = runner.invoke(cli, ["campaigns", "camp-123", "placement"])
        assert result.exit_code != 0
        mock_client.edit_campaigns.assert_not_called()

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_create_campaign(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.create_campaigns.return_value = Mock(
            payload={"campaigns": {"success": [{"campaignId": "camp-123"}]}}
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            [
                "campaigns",
                "create",
                "--name",
                "Test Campaign",
                "--budget",
                "50.0",
                "--targeting-type",
                "MANUAL",
            ],
        )
        assert result.exit_code == 0
        assert "Created campaign" in result.output
        assert "camp-123" in result.output
        mock_client.create_campaigns.assert_called_once()
        call_body = mock_client.create_campaigns.call_args[1]["body"]
        campaign = call_body["campaigns"][0]
        assert campaign["name"] == "Test Campaign"
        assert campaign["budget"] == {"budgetType": "DAILY", "budget": 50.0}
        assert campaign["targetingType"] == "MANUAL"
        assert campaign["state"] == "ENABLED"

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_create_campaign_with_options(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.create_campaigns.return_value = Mock(
            payload={"campaigns": {"success": [{"campaignId": "camp-456"}]}}
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            [
                "campaigns",
                "create",
                "--name",
                "Auto Campaign",
                "--budget",
                "25.0",
                "--targeting-type",
                "AUTO",
                "--state",
                "PAUSED",
                "--start-date",
                "2026-08-01",
                "--end-date",
                "2026-08-31",
                "--bidding-strategy",
                "LEGACY_FOR_SALES",
                "--top-of-search",
                "25",
                "--product-page",
                "10",
                "--rest-of-search",
                "5",
                "--portfolio-id",
                "123",
            ],
        )
        assert result.exit_code == 0
        assert "camp-456" in result.output
        call_body = mock_client.create_campaigns.call_args[1]["body"]
        campaign = call_body["campaigns"][0]
        assert campaign["name"] == "Auto Campaign"
        assert campaign["state"] == "PAUSED"
        assert campaign["startDate"] == "2026-08-01"
        assert campaign["endDate"] == "2026-08-31"
        assert campaign["portfolioId"] == 123
        assert campaign["dynamicBidding"]["strategy"] == "LEGACY_FOR_SALES"
        assert campaign["dynamicBidding"]["placementBidding"] == [
            {"placement": "PLACEMENT_TOP", "percentage": 25.0},
            {"placement": "PLACEMENT_PRODUCT_PAGE", "percentage": 10.0},
            {"placement": "PLACEMENT_REST_OF_SEARCH", "percentage": 5.0},
        ]

    @pytest.mark.parametrize("placement_option", ["--top-of-search", "--product-page", "--rest-of-search"])
    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_create_campaign_requires_bidding_strategy_for_placement(
        self, mock_client_class, mock_auth_class, runner, placement_option
    ):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            [
                "campaigns",
                "create",
                "--name",
                "Test",
                "--budget",
                "10.0",
                "--targeting-type",
                "AUTO",
                placement_option,
                "20",
            ],
        )
        assert result.exit_code != 0
        mock_client.create_campaigns.assert_not_called()

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_create_campaign_reports_errors(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.create_campaigns.return_value = Mock(
            payload={"campaigns": {"error": [{"details": "Name is too long"}]}}
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            [
                "campaigns",
                "create",
                "--name",
                "A" * 200,
                "--budget",
                "10.0",
                "--targeting-type",
                "AUTO",
            ],
        )
        assert result.exit_code != 0
        assert "Name is too long" in result.output
