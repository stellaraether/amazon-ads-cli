#!/usr/bin/env python3
"""Amazon Ads CLI - Command line interface for Amazon Advertising API v3."""

import json
import os
from datetime import datetime, timedelta

import click
import yaml
from ad_api.api import reports, sponsored_products
from ad_api.base import Marketplaces

DEFAULT_CREDENTIALS_PATH = os.path.expanduser("~/.config/python-ad-api/credentials.yml")


def _check_path():
    """Check if the CLI is accessible in PATH and warn if not."""
    import shutil
    import sys

    if not shutil.which("amz-ads"):
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


@click.group()
@click.option("--profile", "-p", default="default", help="Credential profile")
@click.pass_context
def cli(ctx, profile):
    """Amazon Ads CLI - Manage campaigns, keywords, and reports."""
    _check_path()
    ctx.ensure_object(dict)
    ctx.obj["profile"] = profile


@cli.group()
def auth():
    """Authentication commands."""
    pass


@auth.command("setup")
@click.option(
    "--path", default=DEFAULT_CREDENTIALS_PATH, help="Path to save credentials"
)
@click.pass_context
def auth_setup(ctx, path):
    """Interactive setup for Amazon Ads API credentials."""
    click.echo("🔐 Amazon Ads API Credential Setup")
    click.echo("=" * 50)
    click.echo()
    click.echo("You'll need the following from your Amazon Developer account:")
    click.echo("  1. Refresh Token (from LWA authorization)")
    click.echo("  2. Client ID (from your app registration)")
    click.echo("  3. Client Secret (from your app registration)")
    click.echo("  4. Profile ID (your Amazon Ads account ID)")
    click.echo()

    profile = click.prompt("Profile name", default="default")
    refresh_token = click.prompt("Refresh token", hide_input=True)
    client_id = click.prompt("Client ID")
    client_secret = click.prompt("Client secret", hide_input=True)
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
    click.echo(
        "You can now use: python -m amazon_ads_cli.main --profile {profile} campaigns list"
    )


@auth.command("show")
@click.option(
    "--path", default=DEFAULT_CREDENTIALS_PATH, help="Path to credentials file"
)
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


@cli.group()
def campaigns():
    """Campaign management commands."""
    pass


@campaigns.command("list")
@click.pass_context
def list_campaigns(ctx):
    """List all campaigns."""
    result = sponsored_products.CampaignsV3(marketplace=Marketplaces.NA).list_campaigns(
        body={}
    )
    campaigns = result.payload.get("campaigns", [])

    click.echo(f"\n{'Campaign':<30} {'State':<10} {'Budget':<10} {'Type'}")
    click.echo("-" * 65)
    for camp in campaigns:
        name = camp["name"][:28]
        state = camp["state"]
        budget = f"${camp['budget']['budget']}"
        ctype = camp.get("targetingType", "N/A")
        click.echo(f"{name:<30} {state:<10} {budget:<10} {ctype}")


@campaigns.command("pause")
@click.argument("campaign-id")
@click.pass_context
def pause_campaign(ctx, campaign_id):
    """Pause a campaign."""
    try:
        sponsored_products.CampaignsV3(marketplace=Marketplaces.NA).edit_campaigns(
            body={"campaigns": [{"campaignId": campaign_id, "state": "PAUSED"}]}
        )
        click.echo(f"✅ Campaign {campaign_id} paused")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@campaigns.command("enable")
@click.argument("campaign-id")
@click.pass_context
def enable_campaign(ctx, campaign_id):
    """Enable a campaign."""
    try:
        sponsored_products.CampaignsV3(marketplace=Marketplaces.NA).edit_campaigns(
            body={"campaigns": [{"campaignId": campaign_id, "state": "ENABLED"}]}
        )
        click.echo(f"✅ Campaign {campaign_id} enabled")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@campaigns.command("budget")
@click.argument("campaign-id")
@click.argument("amount", type=float)
@click.pass_context
def set_budget(ctx, campaign_id, amount):
    """Set campaign daily budget."""
    try:
        sponsored_products.CampaignsV3(marketplace=Marketplaces.NA).edit_campaigns(
            body={
                "campaigns": [
                    {
                        "campaignId": campaign_id,
                        "budget": {"budget": amount, "budgetType": "DAILY"},
                    }
                ]
            }
        )
        click.echo(f"✅ Campaign {campaign_id} budget set to ${amount}/day")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.group()
def keywords():
    """Keyword management commands."""
    pass


@keywords.command("list")
@click.argument("campaign-id")
@click.pass_context
def list_keywords(ctx, campaign_id):
    """List keywords for a campaign."""
    result = sponsored_products.KeywordsV3(marketplace=Marketplaces.NA).list_keywords(
        body={}
    )
    keywords = [
        k
        for k in result.payload.get("keywords", [])
        if k.get("campaignId") == campaign_id
    ]

    click.echo(f"\n{'Keyword':<35} {'Match':<10} {'Bid':<8} {'State'}")
    click.echo("-" * 70)
    for kw in keywords:
        text = kw["keywordText"][:33]
        match = kw["matchType"]
        bid = f"${kw['bid']}"
        state = kw["state"]
        click.echo(f"{text:<35} {match:<10} {bid:<8} {state}")


@keywords.command("add")
@click.argument("campaign-id")
@click.argument("ad-group-id")
@click.argument("keyword-text")
@click.option("--match-type", default="EXACT", help="Match type: EXACT, PHRASE, BROAD")
@click.option("--bid", default=1.0, help="Bid amount")
@click.pass_context
def add_keyword(ctx, campaign_id, ad_group_id, keyword_text, match_type, bid):
    """Add a keyword to a campaign."""
    try:
        sponsored_products.KeywordsV3(marketplace=Marketplaces.NA).create_keyword(
            body={
                "keywords": [
                    {
                        "campaignId": campaign_id,
                        "adGroupId": ad_group_id,
                        "keywordText": keyword_text,
                        "matchType": match_type,
                        "bid": bid,
                        "state": "ENABLED",
                    }
                ]
            }
        )
        click.echo(f"✅ Added keyword: {keyword_text} ({match_type}) - ${bid}")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@keywords.command("bid")
@click.argument("keyword-id")
@click.argument("amount", type=float)
@click.pass_context
def set_bid(ctx, keyword_id, amount):
    """Update keyword bid."""
    try:
        sponsored_products.KeywordsV3(marketplace=Marketplaces.NA).edit_keyword(
            keywordId=keyword_id,
            body={"keywords": [{"keywordId": keyword_id, "bid": amount}]},
        )
        click.echo(f"✅ Keyword {keyword_id} bid updated to ${amount}")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.group()
def negatives():
    """Negative keyword management commands."""
    pass


@negatives.command("list")
@click.argument("campaign-id")
@click.pass_context
def list_negatives(ctx, campaign_id):
    """List negative keywords for a campaign."""
    result = sponsored_products.NegativeKeywordsV3(
        marketplace=Marketplaces.NA
    ).list_negative_keywords(body={"campaignIdFilter": {"include": [campaign_id]}})
    negatives = result.payload.get("negativeKeywords", [])

    click.echo(f"\n{'Negative Keyword':<35} {'Match':<15}")
    click.echo("-" * 55)
    for neg in negatives:
        text = neg["keywordText"][:33]
        match = neg["matchType"]
        click.echo(f"{text:<35} {match:<15}")


@negatives.command("add")
@click.argument("campaign-id")
@click.argument("keyword-text")
@click.option(
    "--match-type",
    default="NEGATIVE_PHRASE",
    help="Match type: NEGATIVE_EXACT, NEGATIVE_PHRASE",
)
@click.pass_context
def add_negative(ctx, campaign_id, keyword_text, match_type):
    """Add a negative keyword to a campaign."""
    try:
        sponsored_products.NegativeKeywordsV3(
            marketplace=Marketplaces.NA
        ).create_negative_keywords(
            body={
                "negativeKeywords": [
                    {
                        "campaignId": campaign_id,
                        "keywordText": keyword_text,
                        "matchType": match_type,
                        "state": "ENABLED",
                    }
                ]
            }
        )
        click.echo(f"✅ Added negative keyword: {keyword_text} ({match_type})")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.group()
def report():
    """Report commands."""
    pass


@report.command("today")
@click.pass_context
def report_today(ctx):
    """Get today's performance report."""
    today = datetime.now().strftime("%Y-%m-%d")

    click.echo(f"Requesting report for {today}...")

    report_body = {
        "name": f"SP_Today_{today}",
        "startDate": today,
        "endDate": today,
        "configuration": {
            "adProduct": "SPONSORED_PRODUCTS",
            "columns": [
                "impressions",
                "clicks",
                "cost",
                "purchases14d",
                "sales14d",
                "campaignName",
                "campaignId",
            ],
            "reportTypeId": "spCampaigns",
            "format": "GZIP_JSON",
            "groupBy": ["campaign"],
            "timeUnit": "SUMMARY",
        },
    }

    try:
        # Submit report
        result = reports.Reports(marketplace=Marketplaces.NA).post_report(
            body=report_body
        )
        report_id = result.payload["reportId"]

        click.echo(f"Report submitted: {report_id}")
        click.echo("Polling for completion...")

        # Poll
        import time

        for i in range(20):
            result = reports.Reports(marketplace=Marketplaces.NA).get_report(
                reportId=report_id
            )
            status = result.payload.get("status")

            if status == "COMPLETED":
                # Download
                import gzip

                import requests

                url = result.payload.get("url")
                response = requests.get(url)
                data = gzip.decompress(response.content)
                report_data = json.loads(data)

                click.echo(
                    f"\n{'Campaign':<30} {'Impr':>8} {'Clicks':>7} {'Spend':>8} {'Sales':>8} {'ACOS'}"
                )
                click.echo("-" * 75)

                for row in report_data:
                    camp_name = row.get("campaignName", "N/A")[:28]
                    impr = int(row.get("impressions", 0) or 0)
                    clicks = int(row.get("clicks", 0) or 0)
                    cost = float(row.get("cost", 0) or 0)
                    sales = float(row.get("sales14d", 0) or 0)
                    acos = (cost / sales * 100) if sales > 0 else 0

                    click.echo(
                        f"{camp_name:<30} {impr:>8} {clicks:>7} ${cost:>7.2f} ${sales:>7.2f} {acos:>5.1f}%"
                    )

                return

            elif status == "FAILED":
                click.echo(f"❌ Report failed: {result.payload.get('failureReason')}")
                return

            time.sleep(3)

        click.echo("⏳ Report still processing...")

    except Exception as e:
        click.echo(f"❌ Error: {e}")


@report.command("search-terms")
@click.option("--days", default=7, help="Number of days to look back")
@click.pass_context
def search_terms_report(ctx, days):
    """Get search term report."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    click.echo(f"Requesting search term report: {start_date} to {end_date}...")

    report_body = {
        "name": f"SP_SearchTerms_{start_date}_{end_date}",
        "startDate": start_date,
        "endDate": end_date,
        "configuration": {
            "adProduct": "SPONSORED_PRODUCTS",
            "columns": [
                "impressions",
                "clicks",
                "cost",
                "purchases14d",
                "sales14d",
                "searchTerm",
                "matchType",
                "campaignName",
                "keyword",
            ],
            "reportTypeId": "spSearchTerm",
            "format": "GZIP_JSON",
            "groupBy": ["searchTerm"],
            "timeUnit": "SUMMARY",
        },
    }

    try:
        result = reports.Reports(marketplace=Marketplaces.NA).post_report(
            body=report_body
        )
        report_id = result.payload["reportId"]

        click.echo(f"Report submitted: {report_id}")
        click.echo("Polling for completion...")

        import time

        for i in range(30):
            result = reports.Reports(marketplace=Marketplaces.NA).get_report(
                reportId=report_id
            )
            status = result.payload.get("status")

            if status == "COMPLETED":
                import gzip

                import requests

                url = result.payload.get("url")
                response = requests.get(url)
                data = gzip.decompress(response.content)
                report_data = json.loads(data)

                # Sort by cost (highest first)
                report_data.sort(
                    key=lambda x: float(x.get("cost", 0) or 0), reverse=True
                )

                click.echo(
                    f"\n{'Search Term':<40} {'Campaign':<20} {'Spend':>8} {'Sales':>8} {'ACOS'}"
                )
                click.echo("-" * 90)

                for row in report_data[:20]:
                    term = row.get("searchTerm", "N/A")[:38]
                    camp = row.get("campaignName", "N/A")[:18]
                    cost = float(row.get("cost", 0) or 0)
                    sales = float(row.get("sales14d", 0) or 0)
                    acos = (cost / sales * 100) if sales > 0 else 0

                    click.echo(
                        f"{term:<40} {camp:<20} ${cost:>7.2f} ${sales:>7.2f} {acos:>5.1f}%"
                    )

                return

            elif status == "FAILED":
                click.echo(f"❌ Report failed: {result.payload.get('failureReason')}")
                return

            time.sleep(5)

        click.echo("⏳ Report still processing...")

    except Exception as e:
        click.echo(f"❌ Error: {e}")


if __name__ == "__main__":
    cli()
