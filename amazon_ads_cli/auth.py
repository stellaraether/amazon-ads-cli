"""Amazon Ads API authentication handler."""

from pathlib import Path
from typing import Optional

import yaml


class AdsAuth:
    """Handles Ads API credential loading."""

    DEFAULT_CREDENTIALS_PATH = Path.home() / ".config" / "python-ad-api" / "credentials.yml"

    def __init__(self, credentials_path: str = None):
        self.credentials_path = Path(credentials_path or self.DEFAULT_CREDENTIALS_PATH)
        self.credentials = self._load_credentials()

    def _load_credentials(self) -> Optional[dict]:
        """Load credentials from YAML file."""
        if not self.credentials_path.exists():
            return None

        with open(self.credentials_path, "r") as f:
            return yaml.safe_load(f)
