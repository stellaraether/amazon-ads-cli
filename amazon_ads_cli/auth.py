"""Amazon Ads API authentication handler."""

from pathlib import Path
from typing import Optional

import yaml


class AdsAuth:
    """Handles Ads API credential loading."""

    DEFAULT_CREDENTIALS_PATH = Path.home() / ".config" / "python-ad-api" / "credentials.yml"

    def __init__(self, credentials_path: str = None, profile: str = "default"):
        self.credentials_path = Path(credentials_path or self.DEFAULT_CREDENTIALS_PATH)
        self.profile = profile
        self.credentials = self._load_credentials()

    def _load_credentials(self) -> Optional[dict]:
        """Load credentials from YAML file."""
        if not self.credentials_path.exists():
            return None

        with open(self.credentials_path, "r") as f:
            return yaml.safe_load(f)

    def get_profile_credentials(self) -> Optional[dict]:
        """Return flat credentials dict for the configured profile."""
        if self.credentials is None:
            return None
        profile_creds = self.credentials.get(self.profile)
        if not isinstance(profile_creds, dict):
            return None
        return {
            "refresh_token": profile_creds.get("refresh_token"),
            "client_id": profile_creds.get("client_id"),
            "client_secret": profile_creds.get("client_secret"),
            "profile_id": profile_creds.get("profile_id"),
        }
