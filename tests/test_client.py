"""Tests for Ads API client."""

from unittest.mock import Mock

import pytest

from amazon_ads_cli.auth import AdsAuth
from amazon_ads_cli.client import AdsAPIClient


class TestAdsAPIClient:
    """Test AdsAPIClient class."""

    @pytest.fixture
    def mock_auth(self):
        """Create mock auth object."""
        auth = Mock(spec=AdsAuth)
        auth.credentials = {
            "default": {
                "refresh_token": "test-refresh-token",
                "client_id": "test-client-id",
                "client_secret": "test-secret",
                "profile_id": "123456789",
            }
        }
        return auth

    @pytest.fixture
    def client(self, mock_auth):
        """Create AdsAPIClient instance."""
        return AdsAPIClient(mock_auth)

    def test_init(self, client, mock_auth):
        """Test client initialization."""
        assert client.auth == mock_auth
        assert client.marketplace is not None
