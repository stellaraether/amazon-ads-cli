"""Tests for Ads API authentication."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from amazon_ads_cli.auth import AdsAuth


class TestAdsAuth:
    """Test AdsAuth class."""

    @pytest.fixture
    def temp_credentials(self):
        """Create temporary credentials file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(
                """
default:
  refresh_token: "test-refresh-token"
  client_id: "test-client-id"
  client_secret: "test-client-secret"
  profile_id: "123456789"
other:
  refresh_token: "other-refresh-token"
  client_id: "other-client-id"
  client_secret: "other-client-secret"
  profile_id: "987654321"
"""
            )
            path = f.name
        yield path
        os.unlink(path)

    def test_load_credentials_default(self, temp_credentials):
        """Test loading default profile credentials."""
        auth = AdsAuth(temp_credentials)
        assert auth.credentials["refresh_token"] == "test-refresh-token"
        assert auth.credentials["client_id"] == "test-client-id"
        assert auth.credentials["profile_id"] == "123456789"

    def test_load_credentials_other(self, temp_credentials):
        """Test loading non-default profile credentials."""
        auth = AdsAuth(temp_credentials, profile="other")
        assert auth.credentials["refresh_token"] == "other-refresh-token"
        assert auth.credentials["client_id"] == "other-client-id"
        assert auth.credentials["profile_id"] == "987654321"

    def test_missing_credentials(self):
        """Test missing credentials file."""
        auth = AdsAuth("/nonexistent/path/credentials.yml")
        assert auth.credentials is None

    def test_default_path(self):
        """Test default credentials path."""
        auth = AdsAuth()
        assert auth.credentials_path == Path.home() / ".config" / "amazon-ads-cli" / "credentials.yml"

    def test_invalidate(self, temp_credentials):
        """Test invalidate clears caches."""
        auth = AdsAuth(temp_credentials)
        with patch("ad_api.auth.access_token_client.cache") as mock_cache, patch(
            "ad_api.auth.access_token_client.grantless_cache"
        ) as mock_grantless_cache:
            auth.invalidate()
            mock_cache.clear.assert_called_once()
            mock_grantless_cache.clear.assert_called_once()
