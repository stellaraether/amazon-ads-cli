"""Tests for ad-group-scoped entity commands."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from amazon_ads_cli.main import cli


class TestAdgroupEntities:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_adgroup_negatives_list(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_negative_keywords.return_value = Mock(
            payload={"negativeKeywords": [{"keywordText": "bad word", "matchType": "NEGATIVE_EXACT"}]}
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-123", "negatives", "list"])
        assert result.exit_code == 0
        assert "bad word" in result.output
        mock_client.list_negative_keywords.assert_called_once()

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_adgroup_negatives_list_with_asin_warning(self, mock_client_class, mock_auth_class, runner):
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

        result = runner.invoke(cli, ["adgroups", "ag-123", "negatives", "list"])
        assert result.exit_code == 0
        assert "B0CGJR1H72" in result.output
        assert "Warning" in result.output
        assert "negative-asin-targets" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_adgroup_negatives_list_show_ids(self, mock_client_class, mock_auth_class, runner):
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

        result = runner.invoke(cli, ["adgroups", "ag-123", "negatives", "list", "--show-ids"])
        assert result.exit_code == 0
        assert "nk-1" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_adgroup_negative_asin_targets_list(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_negative_product_targets.return_value = Mock(
            payload={
                "negativeTargetingClauses": [
                    {
                        "targetId": "ntgt-1",
                        "expression": [{"value": "B0CGJR1H72", "type": "ASIN_SAME_AS"}],
                        "state": "ENABLED",
                    }
                ]
            }
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-123", "negative-asin-targets", "list"])
        assert result.exit_code == 0
        assert "B0CGJR1H72" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_adgroup_negative_asin_targets_list_all(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_negative_product_targets.return_value = Mock(payload={"negativeTargetingClauses": []})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-123", "negative-asin-targets", "list-all"])
        assert result.exit_code == 0

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_adgroup_asin_targets_list(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_product_targets.return_value = Mock(
            payload={
                "productTargets": [
                    {
                        "targetId": "tgt-1",
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

        result = runner.invoke(cli, ["adgroups", "ag-123", "asin-targets", "list"])
        assert result.exit_code == 0
        assert "B09BBL8T4Z" in result.output

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_adgroup_keywords_bid(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.edit_keyword.return_value = Mock(payload={})
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-123", "keywords", "bid", "kw-1", "2.5"])
        assert result.exit_code == 0
        assert "bid updated" in result.output
        mock_client.edit_keyword.assert_called_once_with("kw-1", body={"keywords": [{"keywordId": "kw-1", "bid": 2.5}]})

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_adgroup_auto_targets_list(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_product_targets.return_value = Mock(
            payload={
                "targetingClauses": [
                    {
                        "targetId": "tgt-substitutes",
                        "adGroupId": "ag-123",
                        "campaignId": "camp-123",
                        "expression": [{"type": "ASIN_SUBSTITUTE_RELATED"}],
                        "expressionType": "AUTO",
                        "state": "ENABLED",
                        "bid": 0.55,
                    },
                    {
                        "targetId": "tgt-complements",
                        "adGroupId": "ag-123",
                        "campaignId": "camp-123",
                        "expression": [{"type": "ASIN_ACCESSORY_RELATED"}],
                        "expressionType": "AUTO",
                        "state": "PAUSED",
                        "bid": 0.4,
                    },
                ]
            }
        )
        mock_client.list_ad_groups.return_value = Mock(
            payload={"adGroups": [{"adGroupId": "ag-123", "defaultBid": 0.3}]}
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["adgroups", "ag-123", "auto-targets", "list"])
        assert result.exit_code == 0
        assert "substitutes" in result.output
        assert "complements" in result.output
        assert "PAUSED" in result.output
        mock_client.list_product_targets.assert_called_once_with(body={"adGroupIdFilter": {"include": ["ag-123"]}})

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_adgroup_auto_targets_set_bid(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.list_product_targets.return_value = Mock(
            payload={
                "targetingClauses": [
                    {
                        "targetId": "tgt-substitutes",
                        "adGroupId": "ag-123",
                        "campaignId": "camp-123",
                        "expression": [{"type": "ASIN_SUBSTITUTE_RELATED"}],
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

        result = runner.invoke(cli, ["adgroups", "ag-123", "auto-targets", "set", "substitutes", "--bid", "1.25"])
        assert result.exit_code == 0
        assert "Updated substitutes" in result.output
        mock_client.edit_product_targets.assert_called_once_with(
            body={"targetingClauses": [{"targetId": "tgt-substitutes", "bid": 1.25}]}
        )
