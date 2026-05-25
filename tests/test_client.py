"""Tests for Ads API client."""

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
