"""Tests for auth commands."""

from click.testing import CliRunner

from amazon_ads_cli.main import cli


class TestAuthCommands:
    def test_auth_show_missing(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["auth", "show", "--path", "/nonexistent/creds.yml"])
        assert result.exit_code == 0
        assert "No credentials file found" in result.output
