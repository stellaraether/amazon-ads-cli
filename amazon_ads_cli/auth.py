"""Amazon Ads API authentication handler."""

from pathlib import Path
from typing import Optional

import yaml


class AdsAuth:
    """Handles Ads API credential loading."""

    DEFAULT_CREDENTIALS_PATH = Path.home() / ".config" / "amazon-ads-cli" / "credentials.yml"

    def __init__(self, credentials_path: str = None, profile: str = "default"):
        self.credentials_path = Path(credentials_path or self.DEFAULT_CREDENTIALS_PATH)
        self.profile = profile
        self.credentials = self._load_credentials()

    def _load_credentials(self) -> Optional[dict]:
        """Load credentials from YAML file."""
        if not self.credentials_path.exists():
            return None

        with open(self.credentials_path, "r") as f:
            config = yaml.safe_load(f)
        if config is None:
            return None
        return config.get(self.profile, config)

    def invalidate(self):
        """Invalidate cached access tokens."""
        from ad_api.auth.access_token_client import cache, grantless_cache

        cache.clear()
        grantless_cache.clear()
        print("Token cache invalidated.")
