"""Authentication commands."""

import os

import click
import yaml
from ad_api.api.profiles import Profiles
from ad_api.base import Marketplaces

from ..cli import DEFAULT_CREDENTIALS_PATH


def _resolve_profile(refresh_token, client_id, client_secret, country=None):
    """Call the Amazon Advertising API to list profiles and optionally map country."""
    try:
        profiles_client = Profiles(
            marketplace=Marketplaces.NA,
            credentials={
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            verify_additional_credentials=False,
        )
        result = profiles_client.list_profiles()
        available = result.payload or []

        if not available:
            return None, None, "No profiles found for these credentials."

        if country:
            country = country.upper()
            for profile in available:
                if profile.get("countryCode") == country:
                    return str(profile["profileId"]), country, None
            codes = ", ".join(p.get("countryCode", "N/A") for p in available)
            return None, None, f"Country '{country}' not found. Available: {codes}"

        return available, None, None

    except Exception as exc:
        return None, None, str(exc)


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
    @click.option("--country", help="Marketplace country code (e.g. US, CA, BR)")
    @click.pass_context
    def auth_setup(ctx, path, profile, refresh_token, client_id, client_secret, country):
        """Set up Amazon Ads API credentials.

        When flags are omitted, falls back to interactive prompts.
        """
        click.echo("🔐 Amazon Ads API Credential Setup")
        click.echo("=" * 50)
        click.echo()

        has_creds = all([refresh_token, client_id, client_secret])
        has_profile = country is not None
        interactive = not has_creds or not has_profile

        if interactive:
            click.echo("You'll need the following from your Amazon Developer account:")
            click.echo("  1. Refresh Token (from LWA authorization)")
            click.echo("  2. Client ID (from your app registration)")
            click.echo("  3. Client Secret (from your app registration)")
            click.echo()

        profile = profile or click.prompt("Profile name", default="default")
        refresh_token = refresh_token or click.prompt("Refresh token", hide_input=True)
        client_id = client_id or click.prompt("Client ID")
        client_secret = client_secret or click.prompt("Client secret", hide_input=True)

        profile_id = None
        resolved_country = None
        if interactive and country is None:
            click.echo("\n🌎 Looking up available marketplaces...")

        result, resolved_country, error = _resolve_profile(refresh_token, client_id, client_secret, country=country)

        if isinstance(result, list):
            if not result:
                error = "No profiles found."
            elif country is None:
                click.echo("\nAvailable marketplaces:")
                for i, p in enumerate(result, 1):
                    cc = p.get("countryCode", "N/A")
                    name = p.get("accountInfo", {}).get("name", "N/A")
                    click.echo(f"  {i}. {cc} — {name}")

                choice = click.prompt(
                    "Select marketplace by number",
                    type=click.IntRange(1, len(result)),
                )
                selected = result[choice - 1]
                profile_id = str(selected["profileId"])
                resolved_country = selected.get("countryCode")
                click.echo(f"✅ Selected {resolved_country} (Profile ID: {profile_id})")
            else:
                # Should not happen — country was provided but returned a list
                error = f"Unexpected response while resolving country {country}."
        elif isinstance(result, str):
            profile_id = result
            if resolved_country:
                click.echo(f"✅ Resolved {resolved_country} to Profile ID: {profile_id}")

        if profile_id is None:
            click.echo(f"⚠️  Could not resolve profile: {error}")
            if not interactive:
                raise click.Abort()
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
        if resolved_country:
            credentials[profile]["country"] = resolved_country

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
        if resolved_country:
            click.echo(f"   Country: {resolved_country}")
        click.echo()
        click.echo("You can now use: amz-ads --profile {profile} campaigns list")

    @auth.command("show")
    @click.option("--path", default=DEFAULT_CREDENTIALS_PATH, help="Path to credentials file")
    @click.pass_context
    def auth_show(ctx, path):
        """Show configured profiles (without secrets)."""
        if not os.path.exists(path):
            click.echo(f"❌ No credentials file found at {path}")
            click.echo("Run: amz-ads auth setup")
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
            if "country" in data:
                click.echo(f"  Country: {data['country']}")
            click.echo()
