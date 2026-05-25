"""Tests for Ads API authentication."""

import os
import tempfile
from pathlib import Path

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
"""
            )
            path = f.name
        yield path
        os.unlink(path)

    def test_load_credentials(self, temp_credentials):
        """Test credentials loading."""
        auth = AdsAuth(temp_credentials)
        assert auth.credentials["default"]["refresh_token"] == "test-refresh-token"
        assert auth.credentials["default"]["client_id"] == "test-client-id"
        assert auth.credentials["default"]["profile_id"] == "123456789"

    def test_missing_credentials(self):
        """Test missing credentials file."""
        auth = AdsAuth("/nonexistent/path/credentials.yml")
        assert auth.credentials is None

    def test_default_path(self):
        """Test default credentials path."""
        auth = AdsAuth()
        assert auth.credentials_path == Path.home() / ".config" / "python-ad-api" / "credentials.yml"
