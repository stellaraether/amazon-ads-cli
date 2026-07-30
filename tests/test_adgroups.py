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

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_show_adgroup(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_ad_groups.return_value = Mock(
            payload={
                "adGroups": [
                    {
                        "adGroupId": "ag-1",
                        "campaignId": "camp-123",
                        "name": "Catnip",
                        "state": "ENABLED",
                        "defaultBid": 0.86,
                    }
                ]
            }
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-1", "show"])
        assert result.exit_code == 0
        assert "Catnip" in result.output
        assert "camp-123" in result.output
        assert "$0.86" in result.output
        mock_client.list_ad_groups.assert_called_once_with(
            body={
                "adGroupIdFilter": {"include": ["ag-1"]},
                "stateFilter": {"include": ["ENABLED", "PAUSED", "ARCHIVED"]},
            }
        )

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_show_adgroup_not_found(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_ad_groups.return_value = Mock(payload={"adGroups": []})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-missing", "show"])
        assert result.exit_code != 0
        assert "not found" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_set_bid(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.edit_ad_groups.return_value = Mock(payload={"adGroups": {"success": [{}]}})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-1", "bid", "1.5"])
        assert result.exit_code == 0
        assert "$1.5" in result.output
        mock_client.edit_ad_groups.assert_called_once_with(
            body={"adGroups": [{"adGroupId": "ag-1", "defaultBid": 1.5}]}
        )

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_set_bid_api_error(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.edit_ad_groups.return_value = Mock(
            payload={"adGroups": {"error": [{"details": "bid below minimum"}]}}
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-1", "bid", "0.01"])
        assert result.exit_code != 0
        assert "bid below minimum" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    @pytest.mark.parametrize("command,state", [("enable", "ENABLED"), ("pause", "PAUSED")])
    def test_set_state(self, mock_client_class, mock_auth_class, runner, command, state):
        mock_client = Mock()
        mock_client.edit_ad_groups.return_value = Mock(payload={"adGroups": {"success": [{}]}})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-1", command])
        assert result.exit_code == 0
        mock_client.edit_ad_groups.assert_called_once_with(body={"adGroups": [{"adGroupId": "ag-1", "state": state}]})

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_archive(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.delete_ad_groups.return_value = Mock(payload={})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-1", "archive"])
        assert result.exit_code == 0
        assert "archived" in result.output
        mock_client.delete_ad_groups.assert_called_once_with(body={"adGroupIdFilter": {"include": ["ag-1"]}})


class TestAdgroupProductAds:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_product_ads_list(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_product_ads.return_value = Mock(
            payload={"productAds": [{"adId": "ad-1", "sku": "SKU-1", "asin": "B0ABCDEF12", "state": "ENABLED"}]}
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-1", "product-ads", "list"])
        assert result.exit_code == 0
        assert "SKU-1" in result.output
        assert "B0ABCDEF12" in result.output
        mock_client.list_product_ads.assert_called_once_with(
            body={
                "adGroupIdFilter": {"include": ["ag-1"]},
                "stateFilter": {"include": ["ENABLED", "PAUSED"]},
            }
        )

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_product_ads_add_sku(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_ad_groups.return_value = Mock(
            payload={"adGroups": [{"adGroupId": "ag-1", "campaignId": "camp-123"}]}
        )
        mock_client.create_product_ads.return_value = Mock(
            payload={"productAds": {"success": [{"adId": "ad-1", "adGroupId": "ag-1"}]}}
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-1", "product-ads", "add", "--sku", "SKU-1"])
        assert result.exit_code == 0
        assert "ad-1" in result.output
        mock_client.create_product_ads.assert_called_once_with(
            body={"productAds": [{"campaignId": "camp-123", "adGroupId": "ag-1", "state": "ENABLED", "sku": "SKU-1"}]}
        )

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_product_ads_add_asin(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_ad_groups.return_value = Mock(
            payload={"adGroups": [{"adGroupId": "ag-1", "campaignId": "camp-123"}]}
        )
        mock_client.create_product_ads.return_value = Mock(
            payload={"productAds": {"success": [{"adId": "ad-2", "adGroupId": "ag-1"}]}}
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-1", "product-ads", "add", "--asin", "B0ABCDEF12"])
        assert result.exit_code == 0
        mock_client.create_product_ads.assert_called_once_with(
            body={
                "productAds": [
                    {"campaignId": "camp-123", "adGroupId": "ag-1", "state": "ENABLED", "asin": "B0ABCDEF12"}
                ]
            }
        )

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_product_ads_add_rejects_both_sku_and_asin(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            cli, ["adgroups", "ag-1", "product-ads", "add", "--sku", "SKU-1", "--asin", "B0ABCDEF12"]
        )
        assert result.exit_code != 0
        assert "Exactly one of --sku or --asin" in result.output
        mock_client.create_product_ads.assert_not_called()

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_product_ads_add_rejects_neither_sku_nor_asin(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-1", "product-ads", "add"])
        assert result.exit_code != 0
        assert "Exactly one of --sku or --asin" in result.output
        mock_client.create_product_ads.assert_not_called()

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_product_ads_add_api_error(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_ad_groups.return_value = Mock(
            payload={"adGroups": [{"adGroupId": "ag-1", "campaignId": "camp-123"}]}
        )
        mock_client.create_product_ads.return_value = Mock(
            payload={"productAds": {"error": [{"details": "SKU not in catalog"}]}}
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-1", "product-ads", "add", "--sku", "SKU-1"])
        assert result.exit_code != 0
        assert "SKU not in catalog" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_product_ads_add_nested_api_error(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_ad_groups.return_value = Mock(
            payload={"adGroups": [{"adGroupId": "ag-1", "campaignId": "camp-123"}]}
        )
        mock_client.create_product_ads.return_value = Mock(
            payload={
                "productAds": {
                    "error": [
                        {
                            "index": 0,
                            "errors": [
                                {
                                    "errorType": "adEligibilityError",
                                    "errorValue": {
                                        "adEligibilityError": {
                                            "message": "Product is ineligible for advertising",
                                            "reason": "AD_INELIGIBLE",
                                        }
                                    },
                                }
                            ],
                        }
                    ]
                }
            }
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-1", "product-ads", "add", "--sku", "SKU-1"])
        assert result.exit_code != 0
        assert "Product is ineligible for advertising" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_product_ads_remove(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.delete_product_ads.return_value = Mock(payload={})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-1", "product-ads", "remove", "ad-1"])
        assert result.exit_code == 0
        mock_client.delete_product_ads.assert_called_once_with(body={"adIdFilter": {"include": ["ad-1"]}})
