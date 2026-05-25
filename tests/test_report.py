"""Tests for report commands."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from amazon_ads_cli.main import cli


class TestReport:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch("amazon_ads_cli.cli.AdsAuth")
    @patch("amazon_ads_cli.cli.AdsAPIClient")
    def test_report_status(self, mock_client_class, mock_auth_class, runner):
        mock_client = Mock()
        mock_client.get_report.return_value = Mock(
            payload={
                "status": "COMPLETED",
                "name": "Test Report",
                "startDate": "2024-01-01",
                "endDate": "2024-01-01",
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:00:00Z",
                "fileSize": 1024,
            }
        )
        mock_client_class.return_value = mock_client

        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(cli, ["report", "status", "rep-123"])
        assert result.exit_code == 0
        assert "COMPLETED" in result.output
