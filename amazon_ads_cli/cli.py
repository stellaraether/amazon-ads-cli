"""Core CLI infrastructure and shared utilities."""

import functools
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

from . import __version__
from .auth import AdsAuth
from .client import AdsAPIClient

DEFAULT_CREDENTIALS_PATH = os.path.expanduser("~/.config/python-ad-api/credentials.yml")


def _check_path():
    """Check if the CLI is accessible in PATH and warn once per day."""
    import shutil

    if shutil.which("amz-ads"):
        return

    # Only warn once per day
    flag_file = Path.home() / ".config" / "amazon-ads-cli" / ".path-warned"
    flag_file.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    if flag_file.exists():
        last_warned = flag_file.read_text().strip()
        if last_warned == today:
            return

    flag_file.write_text(today)

    print(
        "\n⚠️  Note: 'amz-ads' is not in your PATH.",
        file=sys.stderr,
    )
    print(
        "   You can still use: python3 -m amazon_ads_cli",
        file=sys.stderr,
    )
    print(
        "   To add to PATH, add this to your shell config:",
        file=sys.stderr,
    )
    print(
        f'   export PATH="{sys.prefix}/bin:$PATH"',
        file=sys.stderr,
    )
    print("", file=sys.stderr)


def _ensure_auth_client(ctx):
    """Lazily create auth and client if not already present."""
    if "client" not in ctx.obj:
        auth = AdsAuth(
            ctx.obj.get("credentials_path"),
            profile=ctx.obj.get("profile", "default"),
        )
        if auth.credentials is None:
            click.echo("Error: No credentials found. Run 'amz-ads auth setup' first.", err=True)
            raise click.Abort()
        credentials = auth.get_profile_credentials()
        if credentials is None:
            click.echo(
                f"Error: Profile '{auth.profile}' not found in credentials file.",
                err=True,
            )
            raise click.Abort()
        ctx.obj["auth"] = auth
        ctx.obj["client"] = AdsAPIClient(credentials)
    return ctx.obj["auth"], ctx.obj["client"]


def handle_errors(f):
    """Decorator to catch exceptions and emit consistent error messages."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except click.ClickException:
            raise
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

    return wrapper


@click.version_option(version=__version__, prog_name="amz-ads")
@click.group()
@click.option("--credentials", "-c", help="Path to credentials YAML file")
@click.option("--profile", "-p", default="default", help="Credential profile name")
@click.pass_context
def cli(ctx, credentials, profile):
    """Amazon Ads CLI - Manage campaigns, keywords, and reports."""
    _check_path()
    ctx.ensure_object(dict)
    ctx.obj["credentials_path"] = credentials
    ctx.obj["profile"] = profile
