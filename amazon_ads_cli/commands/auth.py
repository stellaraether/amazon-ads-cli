"""Authentication commands."""

import os

import click
import yaml

from ..cli import DEFAULT_CREDENTIALS_PATH


def register_auth_commands(cli_group):
    """Register authentication CLI commands."""

    @cli_group.group()
    def auth():
        """Authentication commands."""
        pass

    @auth.command("setup")
    @click.option("--path", default=DEFAULT_CREDENTIALS_PATH, help="Path to save credentials")
    @click.option("--profile", default="default", help="Credential profile name")
    @click.option("--refresh-token", help="Refresh token")
    @click.option("--client-id", help="Client ID")
    @click.option("--client-secret", help="Client secret")
    @click.option("--profile-id", help="Profile ID (numeric)")
    @click.pass_context
    def auth_setup(ctx, path, profile, refresh_token, client_id, client_secret, profile_id):
        """Set up Amazon Ads API credentials.

        When flags are omitted, falls back to interactive prompts.
        """
        click.echo("🔐 Amazon Ads API Credential Setup")
        click.echo("=" * 50)
        click.echo()

        interactive = not all([refresh_token, client_id, client_secret, profile_id is not None])
        if interactive:
            click.echo("You'll need the following from your Amazon Developer account:")
            click.echo("  1. Refresh Token (from LWA authorization)")
            click.echo("  2. Client ID (from your app registration)")
            click.echo("  3. Client Secret (from your app registration)")
            click.echo("  4. Profile ID (your Amazon Ads account ID)")
            click.echo()

        profile = profile or click.prompt("Profile name", default="default")
        refresh_token = refresh_token or click.prompt("Refresh token", hide_input=True)
        client_id = client_id or click.prompt("Client ID")
        client_secret = client_secret or click.prompt("Client secret", hide_input=True)
        if profile_id is None:
            profile_id = click.prompt("Profile ID (numeric)")

        credentials = {
            "version": "1.0",
            profile: {
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
                "profile_id": profile_id,
            },
        }

        # Merge with existing if present
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    existing = yaml.safe_load(f) or {}
                existing[profile] = credentials[profile]
                credentials = existing
                click.echo(f"\n📝 Merged with existing credentials at {path}")
            except Exception as e:
                click.echo(f"⚠️  Could not read existing file: {e}")

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(credentials, f, default_flow_style=False, sort_keys=False)

        click.echo(f"✅ Credentials saved to {path}")
        click.echo(f"   Profile: {profile}")
        click.echo(f"   Profile ID: {profile_id}")
        click.echo()
        click.echo("You can now use: python -m amazon_ads_cli.main --profile {profile} campaigns list")

    @auth.command("show")
    @click.option("--path", default=DEFAULT_CREDENTIALS_PATH, help="Path to credentials file")
    @click.pass_context
    def auth_show(ctx, path):
        """Show configured profiles (without secrets)."""
        if not os.path.exists(path):
            click.echo(f"❌ No credentials file found at {path}")
            click.echo("Run: python -m amazon_ads_cli.main auth setup")
            return

        with open(path, "r") as f:
            creds = yaml.safe_load(f) or {}

        click.echo(f"\n📄 Credentials file: {path}")
        click.echo("-" * 40)

        for profile, data in creds.items():
            if profile == "version":
                continue
            click.echo(f"Profile: {profile}")
            click.echo(f"  Client ID: {data.get('client_id', 'N/A')[:20]}...")
            click.echo(f"  Profile ID: {data.get('profile_id', 'N/A')}")
            click.echo()
