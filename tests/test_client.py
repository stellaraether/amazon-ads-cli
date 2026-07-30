"""Tests for Ads API client."""

from unittest.mock import Mock, patch

import pytest

from amazon_ads_cli.client import AdsAPIClient


class TestAdsAPIClient:
    """Test AdsAPIClient class."""

    @pytest.fixture
    def credentials(self):
        """Create test credentials dict."""
        return {
            "refresh_token": "test-refresh-token",
            "client_id": "test-client-id",
            "client_secret": "test-secret",
            "profile_id": "123456789",
        }

    @pytest.fixture
    def client(self, credentials):
        """Create AdsAPIClient instance."""
        return AdsAPIClient(credentials)

    def test_init(self, client, credentials):
        """Test client initialization."""
        assert client.credentials == credentials
        assert client.marketplace is not None

    @patch("amazon_ads_cli.client.sponsored_products")
    def test_list_negative_product_targets(self, mock_sp, client):
        """Test list_negative_product_targets delegates to NegativeTargetsV3."""
        mock_instance = Mock()
        mock_instance.list_negative_product_targets.return_value = Mock(payload={"negativeTargets": []})
        mock_sp.NegativeTargetsV3.return_value = mock_instance

        result = client.list_negative_product_targets(body={"stateFilter": {"include": ["ENABLED"]}})

        mock_sp.NegativeTargetsV3.assert_called_once()
        mock_instance.list_negative_product_targets.assert_called_once_with(
            body={"stateFilter": {"include": ["ENABLED"]}}
        )
        assert result.payload == {"negativeTargets": []}

    @patch("amazon_ads_cli.client.sponsored_products")
    def test_create_negative_product_targets(self, mock_sp, client):
        """Test create_negative_product_targets delegates to NegativeTargetsV3."""
        mock_instance = Mock()
        mock_instance.create_negative_product_targets.return_value = Mock(payload={})
        mock_sp.NegativeTargetsV3.return_value = mock_instance

        body = {"negativeTargets": [{"campaignId": "camp-123", "expression": []}]}
        client.create_negative_product_targets(body=body)

        mock_instance.create_negative_product_targets.assert_called_once_with(body=body)

    @patch("amazon_ads_cli.client.sponsored_products")
    def test_create_campaigns(self, mock_sp, client):
        """Test create_campaigns delegates to CampaignsV3."""
        mock_instance = Mock()
        mock_instance.create_campaigns.return_value = Mock(
            payload={"campaigns": {"success": [{"campaignId": "camp-123"}]}}
        )
        mock_sp.CampaignsV3.return_value = mock_instance

        body = {"campaigns": [{"name": "Test", "budget": {"budgetType": "DAILY", "budget": 50.0}}]}
        result = client.create_campaigns(body=body)

        mock_sp.CampaignsV3.assert_called_once()
        mock_instance.create_campaigns.assert_called_once_with(body=body)
        assert result.payload["campaigns"]["success"][0]["campaignId"] == "camp-123"

    @patch("amazon_ads_cli.client.sponsored_products")
    def test_create_ad_groups(self, mock_sp, client):
        """Test create_ad_groups delegates to AdGroupsV3 with prefer=True."""
        mock_instance = Mock()
        mock_instance.create_ad_groups.return_value = Mock(payload={"adGroups": {"success": [{"adGroupId": "ag-1"}]}})
        mock_sp.AdGroupsV3.return_value = mock_instance

        body = {"adGroups": [{"name": "Test", "campaignId": "camp-123", "defaultBid": 0.5}]}
        result = client.create_ad_groups(body=body)

        mock_sp.AdGroupsV3.assert_called_once()
        mock_instance.create_ad_groups.assert_called_once_with(body=body, prefer=True)
        assert result.payload["adGroups"]["success"][0]["adGroupId"] == "ag-1"

    @patch("amazon_ads_cli.client.sponsored_products")
    def test_edit_ad_groups(self, mock_sp, client):
        """Test edit_ad_groups delegates to AdGroupsV3 with prefer=True."""
        mock_instance = Mock()
        mock_instance.edit_ad_groups.return_value = Mock(payload={})
        mock_sp.AdGroupsV3.return_value = mock_instance

        body = {"adGroups": [{"adGroupId": "ag-1", "state": "PAUSED"}]}
        client.edit_ad_groups(body=body)

        mock_instance.edit_ad_groups.assert_called_once_with(body=body, prefer=True)

    @patch("amazon_ads_cli.client.sponsored_products")
    def test_delete_ad_groups(self, mock_sp, client):
        """Test delete_ad_groups delegates to AdGroupsV3."""
        mock_instance = Mock()
        mock_instance.delete_ad_groups.return_value = Mock(payload={})
        mock_sp.AdGroupsV3.return_value = mock_instance

        body = {"adGroupIdFilter": {"include": ["ag-1"]}}
        client.delete_ad_groups(body=body)

        mock_instance.delete_ad_groups.assert_called_once_with(body=body)

    @patch("amazon_ads_cli.client.sponsored_products")
    def test_list_product_ads(self, mock_sp, client):
        """Test list_product_ads delegates to ProductAdsV3."""
        mock_instance = Mock()
        mock_instance.list_product_ads.return_value = Mock(payload={"productAds": []})
        mock_sp.ProductAdsV3.return_value = mock_instance

        result = client.list_product_ads(body={"adGroupIdFilter": {"include": ["ag-1"]}})

        mock_sp.ProductAdsV3.assert_called_once()
        mock_instance.list_product_ads.assert_called_once_with(body={"adGroupIdFilter": {"include": ["ag-1"]}})
        assert result.payload == {"productAds": []}

    @patch("amazon_ads_cli.client.sponsored_products")
    def test_list_product_ads_default_body(self, mock_sp, client):
        """Test list_product_ads defaults to an empty body."""
        mock_instance = Mock()
        mock_instance.list_product_ads.return_value = Mock(payload={"productAds": []})
        mock_sp.ProductAdsV3.return_value = mock_instance

        client.list_product_ads()

        mock_instance.list_product_ads.assert_called_once_with(body={})

    @patch("amazon_ads_cli.client.sponsored_products")
    def test_create_product_ads(self, mock_sp, client):
        """Test create_product_ads delegates to ProductAdsV3 with prefer=True."""
        mock_instance = Mock()
        mock_instance.create_product_ads.return_value = Mock(payload={"productAds": {"success": [{"adId": "ad-1"}]}})
        mock_sp.ProductAdsV3.return_value = mock_instance

        body = {"productAds": [{"campaignId": "camp-123", "adGroupId": "ag-1", "sku": "SKU-1"}]}
        result = client.create_product_ads(body=body)

        mock_sp.ProductAdsV3.assert_called_once()
        mock_instance.create_product_ads.assert_called_once_with(body=body, prefer=True)
        assert result.payload["productAds"]["success"][0]["adId"] == "ad-1"

    @patch("amazon_ads_cli.client.sponsored_products")
    def test_edit_product_ads(self, mock_sp, client):
        """Test edit_product_ads delegates to ProductAdsV3 with prefer=True."""
        mock_instance = Mock()
        mock_instance.edit_product_ads.return_value = Mock(payload={})
        mock_sp.ProductAdsV3.return_value = mock_instance

        body = {"productAds": [{"adId": "ad-1", "state": "PAUSED"}]}
        client.edit_product_ads(body=body)

        mock_instance.edit_product_ads.assert_called_once_with(body=body, prefer=True)

    @patch("amazon_ads_cli.client.sponsored_products")
    def test_delete_product_ads(self, mock_sp, client):
        """Test delete_product_ads delegates to ProductAdsV3."""
        mock_instance = Mock()
        mock_instance.delete_product_ads.return_value = Mock(payload={})
        mock_sp.ProductAdsV3.return_value = mock_instance

        body = {"adIdFilter": {"include": ["ad-1"]}}
        client.delete_product_ads(body=body)

        mock_instance.delete_product_ads.assert_called_once_with(body=body)
