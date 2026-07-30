"""Tests for campaign-scoped entity commands."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from amazon_ads_cli.main import cli


class TestCampaignEntities:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_campaign_negatives_list(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_negative_keywords.return_value = Mock(
            payload={"negativeKeywords": [{"keywordText": "bad word", "matchType": "NEGATIVE_EXACT"}]}
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["campaigns", "camp-123", "negatives", "list"])
        assert result.exit_code == 0
        assert "bad word" in result.output
        mock_client.list_negative_keywords.assert_called_once()

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_campaign_negatives_list_with_asin_warning(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_negative_keywords.return_value = Mock(
            payload={
                "negativeKeywords": [
                    {"keywordText": "B0CGJR1H72", "matchType": "NEGATIVE_EXACT", "campaignId": "camp-123"},
                    {"keywordText": "normal keyword", "matchType": "NEGATIVE_PHRASE", "campaignId": "camp-123"},
                ]
            }
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["campaigns", "camp-123", "negatives", "list"])
        assert result.exit_code == 0
        assert "B0CGJR1H72" in result.output
        assert "Warning" in result.output
        assert "negative-asin-targets" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_campaign_negatives_list_show_ids(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_negative_keywords.return_value = Mock(
            payload={
                "negativeKeywords": [
                    {
                        "keywordId": "nk-1",
                        "keywordText": "some keyword",
                        "matchType": "NEGATIVE_EXACT",
                        "campaignId": "camp-123",
                    }
                ]
            }
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["campaigns", "camp-123", "negatives", "list", "--show-ids"])
        assert result.exit_code == 0
        assert "nk-1" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_campaign_negative_asin_targets_list(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_negative_product_targets.return_value = Mock(
            payload={
                "negativeTargetingClauses": [
                    {
                        "targetId": "ntgt-1",
                        "adGroupId": "ag-1",
                        "expression": [{"value": "B0CGJR1H72", "type": "ASIN_SAME_AS"}],
                        "state": "ENABLED",
                    }
                ]
            }
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["campaigns", "camp-123", "negative-asin-targets", "list"])
        assert result.exit_code == 0
        assert "B0CGJR1H72" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_campaign_negative_asin_targets_list_all(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_negative_product_targets.return_value = Mock(payload={"negativeTargetingClauses": []})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["campaigns", "camp-123", "negative-asin-targets", "list-all"])
        assert result.exit_code == 0

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_campaign_asin_targets_list(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_product_targets.return_value = Mock(
            payload={
                "productTargets": [
                    {
                        "targetId": "tgt-1",
                        "adGroupId": "ag-1",
                        "campaignId": "camp-123",
                        "expression": [{"value": "B09BBL8T4Z", "type": "ASIN_SAME_AS"}],
                        "bid": 1.5,
                        "state": "ENABLED",
                    }
                ]
            }
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["campaigns", "camp-123", "asin-targets", "list"])
        assert result.exit_code == 0
        assert "B09BBL8T4Z" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_campaign_keywords_bid(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.edit_keyword.return_value = Mock(payload={})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["campaigns", "camp-123", "keywords", "bid", "kw-1", "2.5"])
        assert result.exit_code == 0
        assert "bid updated" in result.output
        mock_client.edit_keyword.assert_called_once_with("kw-1", body={"keywords": [{"keywordId": "kw-1", "bid": 2.5}]})

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_campaign_adgroups_list(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_ad_groups.return_value = Mock(
            payload={"adGroups": [{"adGroupId": "ag-1", "campaignId": "camp-123", "name": "Test", "state": "ENABLED"}]}
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["campaigns", "camp-123", "adgroups", "list"])
        assert result.exit_code == 0
        assert "Test" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_campaign_adgroups_create(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.create_ad_groups.return_value = Mock(
            payload={"adGroups": {"success": [{"adGroupId": "ag-1", "campaignId": "camp-123"}]}}
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            ["campaigns", "camp-123", "adgroups", "create", "--name", "Catnip", "--default-bid", "0.86"],
        )
        assert result.exit_code == 0
        assert "ag-1" in result.output
        mock_client.create_ad_groups.assert_called_once_with(
            body={"adGroups": [{"name": "Catnip", "campaignId": "camp-123", "defaultBid": 0.86, "state": "ENABLED"}]}
        )

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_campaign_adgroups_create_api_error(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.create_ad_groups.return_value = Mock(
            payload={"adGroups": {"error": [{"details": "duplicate name"}]}}
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli,
            ["campaigns", "camp-123", "adgroups", "create", "--name", "Catnip", "--default-bid", "0.86"],
        )
        assert result.exit_code != 0
        assert "duplicate name" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_campaign_product_ads_list(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_product_ads.return_value = Mock(
            payload={
                "productAds": [
                    {"adId": "ad-1", "adGroupId": "ag-1", "sku": "SKU-1", "asin": "B0ABCDEF12", "state": "ENABLED"}
                ]
            }
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["campaigns", "camp-123", "product-ads", "list"])
        assert result.exit_code == 0
        assert "SKU-1" in result.output
        mock_client.list_product_ads.assert_called_once_with(
            body={
                "campaignIdFilter": {"include": ["camp-123"]},
                "stateFilter": {"include": ["ENABLED", "PAUSED"]},
            }
        )

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_campaign_product_ads_list_all(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_product_ads.return_value = Mock(
            payload={
                "productAds": [
                    {
                        "adId": "ad-1",
                        "campaignId": "camp-123",
                        "adGroupId": "ag-1",
                        "sku": "SKU-1",
                        "state": "ENABLED",
                    }
                ]
            }
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["campaigns", "camp-123", "product-ads", "list-all"])
        assert result.exit_code == 0
        assert "camp-123" in result.output
        mock_client.list_product_ads.assert_called_once_with(body={"stateFilter": {"include": ["ENABLED", "PAUSED"]}})

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_campaign_auto_targets_list(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_product_targets.return_value = Mock(
            payload={
                "targetingClauses": [
                    {
                        "targetId": "tgt-close",
                        "adGroupId": "ag-1",
                        "campaignId": "camp-123",
                        "expression": [{"type": "QUERY_HIGH_REL_MATCHES"}],
                        "expressionType": "AUTO",
                        "state": "ENABLED",
                        "bid": 0.8,
                    },
                    {
                        "targetId": "tgt-loose",
                        "adGroupId": "ag-1",
                        "campaignId": "camp-123",
                        "expression": [{"type": "QUERY_BROAD_REL_MATCHES"}],
                        "expressionType": "AUTO",
                        "state": "ENABLED",
                        "bid": 0.4,
                    },
                ]
            }
        )
        mock_client.list_ad_groups.return_value = Mock(payload={"adGroups": [{"adGroupId": "ag-1", "defaultBid": 0.3}]})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["campaigns", "camp-123", "auto-targets", "list"])
        assert result.exit_code == 0
        assert "close-match" in result.output
        assert "loose-match" in result.output
        assert "+167%" in result.output
        assert "+33%" in result.output
        mock_client.list_product_targets.assert_called_once_with(body={"campaignIdFilter": {"include": ["camp-123"]}})

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_campaign_auto_targets_set_state(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_product_targets.return_value = Mock(
            payload={
                "targetingClauses": [
                    {
                        "targetId": "tgt-close",
                        "adGroupId": "ag-1",
                        "campaignId": "camp-123",
                        "expression": [{"type": "QUERY_HIGH_REL_MATCHES"}],
                        "expressionType": "AUTO",
                        "state": "ENABLED",
                    }
                ]
            }
        )
        mock_client.edit_product_targets.return_value = Mock(payload={})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli, ["campaigns", "camp-123", "auto-targets", "set", "close-match", "--state", "disabled"]
        )
        assert result.exit_code == 0
        assert "Updated close-match" in result.output
        mock_client.edit_product_targets.assert_called_once_with(
            body={"targetingClauses": [{"targetId": "tgt-close", "state": "DISABLED"}]}
        )

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_campaign_auto_targets_set_bid_adjustment(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_product_targets.return_value = Mock(
            payload={
                "targetingClauses": [
                    {
                        "targetId": "tgt-close",
                        "adGroupId": "ag-1",
                        "campaignId": "camp-123",
                        "expression": [{"type": "QUERY_HIGH_REL_MATCHES"}],
                        "expressionType": "AUTO",
                        "state": "ENABLED",
                    }
                ]
            }
        )
        mock_client.list_ad_groups.return_value = Mock(payload={"adGroups": [{"adGroupId": "ag-1", "defaultBid": 0.3}]})
        mock_client.edit_product_targets.return_value = Mock(payload={})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli, ["campaigns", "camp-123", "auto-targets", "set", "close-match", "--bid-adjustment", "20"]
        )
        assert result.exit_code == 0
        assert "Updated close-match" in result.output
        mock_client.edit_product_targets.assert_called_once_with(
            body={"targetingClauses": [{"targetId": "tgt-close", "bid": 0.36}]}
        )
