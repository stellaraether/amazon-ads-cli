# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a small Python CLI tool (`amazon-ads-cli`) for managing Amazon Advertising API v3 campaigns, keywords, negative keywords, ASIN targets, and reports. The entire CLI is implemented in a single file: `amazon_ads_cli/main.py`.

## Development Commands

- **Install locally**: `pip install -e .`
- **Run locally**: `python3 -m amazon_ads_cli.main <command>`
- **Console entry point**: `amz-ads` (after pip install)
- **Lint / format**: Pre-commit runs `black`, `isort --profile black`, and `flake8 --max-line-length=120`. Run manually with `pre-commit run --all-files`.
- **Build package**: `python -m build`
- **Tests**: `pytest` (no tests currently exist in the repo)
- **Check package**: `twine check dist/*`

## Architecture

- **Single-module CLI**: All commands are defined in `amazon_ads_cli/main.py` using `click` groups and subcommands.
- **API wrapper**: Uses the third-party `python-amazon-ad-api` library (`ad_api.api.sponsored_products`, `ad_api.api.reports`).
- **Hardcoded marketplace**: All API calls use `Marketplaces.NA` (North America). There is no multi-marketplace support yet.
- **Credential storage**: Credentials are read from `~/.config/python-ad-api/credentials.yml` (YAML format with named profiles). The `auth setup` command interactively creates this file.
- **Command groups**: `auth`, `campaigns`, `adgroups`, `keywords`, `negatives`, `targets`, `asin-targets`, `report`.
- **Entry points**: `setup.py` registers the console script `amz-ads=amazon_ads_cli.main:cli`. `__main__.py` allows `python -m amazon_ads_cli`.

## Release Process

The project uses an **auto-release** workflow modeled on `amazon-sp-cli`:

- **Version source of truth**: `amazon_ads_cli/__init__.py` contains `__version__`. `setup.py` reads it dynamically.
- **Auto-release workflow** (`.github/workflows/auto-release.yml`): On every push to `main`, it runs pre-commit, a Python 3.8–3.12 test matrix with coverage, and a `twine check` build. If all pass and the repo is `stellaraether/amazon-ads-cli`, it extracts `__version__`, creates a git tag `v{version}` if it does not already exist, creates a GitHub Release with auto-generated notes, and publishes to PyPI.
- **To release**: bump `__version__` in `amazon_ads_cli/__init__.py`, open a PR, and merge. The workflow handles tagging and publishing.
- **Version bump isolation** (`.github/workflows/check-version-bump.yml`): PRs that touch `__init__.py` are required to change *only* that file (and workflow files). This prevents accidental code changes sneaking into version bumps.

## Merge Queue

The `test.yml` and `codeql.yml` workflows both trigger on `merge_group`, so the repository can be used with GitHub merge queues.

## Important Notes

- There are no unit tests yet. The CI still runs `pytest --cov=amazon_ads_cli --cov-report=xml` and uploads to Codecov.
- The CLI imports `yaml` directly in `main.py` but `pyyaml` is not explicitly listed in `setup.py` install_requires; it is pulled in transitively via `python-amazon-ad-api`.
