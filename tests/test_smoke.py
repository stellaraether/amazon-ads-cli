"""Smoke tests for amazon_ads_cli."""

import amazon_ads_cli


def test_version():
    """Package has a version."""
    assert amazon_ads_cli.__version__
