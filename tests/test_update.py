"""Tests for update command."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from amazon_ads_cli.main import cli


class TestUpdate:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch("amazon_ads_cli.commands.update.subprocess.run")
    def test_update_dry_run(self, mock_run, runner):
        result = runner.invoke(cli, ["update", "--dry-run"])
        assert result.exit_code == 0
        assert "Would run" in result.output
        mock_run.assert_not_called()
