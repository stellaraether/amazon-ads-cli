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
