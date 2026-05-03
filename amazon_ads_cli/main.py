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


@cli.group()
def campaigns():
    """Campaign management commands."""
    pass


@campaigns.command("list")
@click.pass_context
def list_campaigns(ctx):
    """List all campaigns."""
    result = sponsored_products.CampaignsV3(marketplace=Marketplaces.NA).list_campaigns(body={})
    campaigns = result.payload.get("campaigns", [])

    click.echo(f"\n{'ID':<20} {'Campaign':<28} {'State':<10} {'Budget':<10} {'Type'}")
    click.echo("-" * 85)
    for camp in campaigns:
        cid = camp["campaignId"][:18]
        name = camp["name"][:26]
        state = camp["state"]
        budget = f"${camp['budget']['budget']}"
        ctype = camp.get("targetingType", "N/A")
        click.echo(f"{cid:<20} {name:<28} {state:<10} {budget:<10} {ctype}")


@campaigns.command("show")
@click.argument("campaign-id")
@click.pass_context
def show_campaign(ctx, campaign_id):
    """Show full details for a campaign."""
    result = sponsored_products.CampaignsV3(marketplace=Marketplaces.NA).list_campaigns(
        body={"campaignIdFilter": {"include": [campaign_id]}}
    )
    campaigns = result.payload.get("campaigns", [])
    if not campaigns:
        click.echo(f"❌ Campaign {campaign_id} not found")
        return

    camp = campaigns[0]
    click.echo(f"\n📋 Campaign: {camp['name']}")
    click.echo(f"   ID: {camp['campaignId']}")
    click.echo(f"   State: {camp['state']}")
    click.echo(f"   Budget: ${camp['budget']['budget']}/{camp['budget']['budgetType'].lower()}")
    click.echo(f"   Type: {camp.get('targetingType', 'N/A')}")
    click.echo(f"   Start: {camp.get('startDate', 'N/A')}")
    click.echo(f"   End: {camp.get('endDate', 'N/A') or 'No end date'}")


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
def adgroups():
    """Ad group management commands."""
    pass


@adgroups.command("list")
@click.option("--campaign-id", help="Filter by campaign ID")
@click.pass_context
def list_adgroups(ctx, campaign_id):
    """List all ad groups."""
    body = {}
    if campaign_id:
        body["campaignIdFilter"] = {"include": [campaign_id]}

    result = sponsored_products.AdGroupsV3(marketplace=Marketplaces.NA).list_ad_groups(body=body)
    ad_groups = result.payload.get("adGroups", [])

    click.echo(f"\n{'ID':<20} {'Campaign ID':<20} {'Name':<30} {'State'}")
    click.echo("-" * 85)
    for ag in ad_groups:
        ag_id = ag["adGroupId"][:18]
        camp_id = ag["campaignId"][:18]
        name = ag["name"][:28]
        state = ag["state"]
        click.echo(f"{ag_id:<20} {camp_id:<20} {name:<30} {state}")


@cli.group()
def keywords():
    """Keyword management commands."""
    pass


@keywords.command("list")
@click.argument("campaign-id")
@click.pass_context
def list_keywords(ctx, campaign_id):
    """List keywords for a campaign."""
    result = sponsored_products.KeywordsV3(marketplace=Marketplaces.NA).list_keywords(body={})
    keywords = [k for k in result.payload.get("keywords", []) if k.get("campaignId") == campaign_id]

    click.echo(f"\n{'Keyword':<35} {'Match':<10} {'Bid':<8} {'State'}")
    click.echo("-" * 70)
    for kw in keywords:
        text = kw["keywordText"][:33]
        match = kw["matchType"]
        bid = f"${kw['bid']}"
        state = kw["state"]
        click.echo(f"{text:<35} {match:<10} {bid:<8} {state}")


@keywords.command("list-all")
@click.pass_context
def list_all_keywords(ctx):
    """List all keywords across all campaigns."""
    result = sponsored_products.KeywordsV3(marketplace=Marketplaces.NA).list_keywords(body={})
    keywords = result.payload.get("keywords", [])

    click.echo(f"\n{'Campaign ID':<20} {'Keyword':<35} {'Match':<10} {'Bid':<8} {'State'}")
    click.echo("-" * 90)
    for kw in keywords:
        camp_id = kw.get("campaignId", "N/A")[:18]
        text = kw["keywordText"][:33]
        match = kw["matchType"]
        bid = f"${kw['bid']}"
        state = kw["state"]
        click.echo(f"{camp_id:<20} {text:<35} {match:<10} {bid:<8} {state}")


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
    result = sponsored_products.NegativeKeywordsV3(marketplace=Marketplaces.NA).list_negative_keywords(
        body={
            "campaignIdFilter": {"include": [campaign_id]},
            "stateFilter": {"include": ["ENABLED"]},
        }
    )
    negatives = result.payload.get("negativeKeywords", [])

    click.echo(f"\n{'Negative Keyword':<35} {'Match':<15}")
    click.echo("-" * 55)
    for neg in negatives:
        text = neg["keywordText"][:33]
        match = neg["matchType"]
        click.echo(f"{text:<35} {match:<15}")


@negatives.command("list-all")
@click.pass_context
def list_all_negatives(ctx):
    """List all negative keywords across all campaigns."""
    result = sponsored_products.NegativeKeywordsV3(marketplace=Marketplaces.NA).list_negative_keywords(
        body={"stateFilter": {"include": ["ENABLED"]}}
    )
    negatives = result.payload.get("negativeKeywords", [])

    click.echo(f"\n{'Campaign ID':<20} {'Negative Keyword':<35} {'Match':<15}")
    click.echo("-" * 80)
    for neg in negatives:
        camp_id = neg.get("campaignId", "N/A")[:18]
        text = neg["keywordText"][:33]
        match = neg["matchType"]
        click.echo(f"{camp_id:<20} {text:<35} {match:<15}")


@negatives.command("add")
@click.argument("campaign-id")
@click.argument("ad-group-id")
@click.argument("keyword-text")
@click.option(
    "--match-type",
    default="NEGATIVE_PHRASE",
    help="Match type: NEGATIVE_EXACT, NEGATIVE_PHRASE",
)
@click.pass_context
def add_negative(ctx, campaign_id, ad_group_id, keyword_text, match_type):
    """Add a negative keyword to a campaign."""
    try:
        sponsored_products.NegativeKeywordsV3(marketplace=Marketplaces.NA).create_negative_keyword(
            body={
                "negativeKeywords": [
                    {
                        "campaignId": campaign_id,
                        "adGroupId": ad_group_id,
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


@negatives.command("remove")
@click.argument("negative-keyword-id")
@click.pass_context
def remove_negative(ctx, negative_keyword_id):
    """Remove a negative keyword by ID."""
    try:
        sponsored_products.NegativeKeywordsV3(marketplace=Marketplaces.NA).delete_negative_keywords(
            body={"negativeKeywordIdFilter": {"include": [negative_keyword_id]}}
        )
        click.echo(f"✅ Removed negative keyword: {negative_keyword_id}")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.group()
def targets():
    """Product target management commands."""
    pass


@targets.command("list-all")
@click.pass_context
def list_all_targets(ctx):
    """List all product targets across all campaigns."""
    result = sponsored_products.TargetsV3(marketplace=Marketplaces.NA).list_product_targets(body={})
    targets_list = result.payload.get("productTargets", [])

    click.echo(f"\n{'Campaign ID':<20} {'Ad Group ID':<20} {'Expression':<40} {'State'}")
    click.echo("-" * 95)
    for t in targets_list:
        camp_id = t.get("campaignId", "N/A")[:18]
        ag_id = t.get("adGroupId", "N/A")[:18]
        expr = str(t.get("expression", []))[:38]
        state = t.get("state", "N/A")
        click.echo(f"{camp_id:<20} {ag_id:<20} {expr:<40} {state}")


@targets.command("delete")
@click.argument("target-id")
@click.pass_context
def delete_target(ctx, target_id):
    """Delete a product target by ID."""
    try:
        sponsored_products.TargetsV3(marketplace=Marketplaces.NA).delete_product_targets(
            body={"targetIdFilter": {"include": [target_id]}}
        )
        click.echo(f"✅ Deleted target: {target_id}")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.group("asin-targets")
def asin_targets():
    """ASIN target management commands."""
    pass


@asin_targets.command("add")
@click.argument("campaign-id")
@click.argument("ad-group-id")
@click.argument("asin")
@click.option("--bid", default=1.0, help="Bid amount")
@click.pass_context
def add_asin_target(ctx, campaign_id, ad_group_id, asin, bid):
    """Add an ASIN target to a campaign ad group."""
    try:
        result = sponsored_products.TargetsV3(marketplace=Marketplaces.NA).create_product_targets(
            body={
                "targetingClauses": [
                    {
                        "campaignId": campaign_id,
                        "adGroupId": ad_group_id,
                        "expression": [{"value": asin, "type": "ASIN_SAME_AS"}],
                        "expressionType": "MANUAL",
                        "state": "ENABLED",
                        "bid": bid,
                    }
                ]
            }
        )
        success = result.payload.get("targetingClauses", {}).get("success", [])
        errors = result.payload.get("targetingClauses", {}).get("error", [])
        if success:
            target_id = success[0].get("targetId")
            click.echo(f"✅ Added ASIN target: {asin} (ID: {target_id}) - ${bid}")
        elif errors:
            msg = (
                errors[0]
                .get("errors", [{}])[0]
                .get("errorValue", {})
                .get("otherError", {})
                .get("message", "Unknown error")
            )
            click.echo(f"❌ Error: {msg}")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@asin_targets.command("remove")
@click.argument("target-id")
@click.pass_context
def remove_asin_target(ctx, target_id):
    """Remove an ASIN target by ID."""
    try:
        sponsored_products.TargetsV3(marketplace=Marketplaces.NA).delete_product_targets(
            body={"targetIdFilter": {"include": [target_id]}}
        )
        click.echo(f"✅ Removed ASIN target: {target_id}")
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
        result = reports.Reports(marketplace=Marketplaces.NA).post_report(body=report_body)
        report_id = result.payload["reportId"]

        click.echo(f"Report submitted: {report_id}")
        click.echo("Polling for completion...")

        # Poll
        import time

        for i in range(20):
            result = reports.Reports(marketplace=Marketplaces.NA).get_report(reportId=report_id)
            status = result.payload.get("status")

            if status == "COMPLETED":
                # Download
                import gzip

                import requests

                url = result.payload.get("url")
                response = requests.get(url)
                data = gzip.decompress(response.content)
                report_data = json.loads(data)

                click.echo(f"\n{'Campaign':<30} {'Impr':>8} {'Clicks':>7} {'Spend':>8} {'Sales':>8} {'ACOS'}")
                click.echo("-" * 75)

                for row in report_data:
                    camp_name = row.get("campaignName", "N/A")[:28]
                    impr = int(row.get("impressions", 0) or 0)
                    clicks = int(row.get("clicks", 0) or 0)
                    cost = float(row.get("cost", 0) or 0)
                    sales = float(row.get("sales14d", 0) or 0)
                    acos = (cost / sales * 100) if sales > 0 else 0

                    click.echo(f"{camp_name:<30} {impr:>8} {clicks:>7} ${cost:>7.2f} ${sales:>7.2f} {acos:>5.1f}%")

                return

            elif status == "FAILED":
                click.echo(f"❌ Report failed: {result.payload.get('failureReason')}")
                return

            time.sleep(3)

        click.echo("⏳ Report still processing...")

    except Exception as e:
        click.echo(f"❌ Error: {e}")


@report.command("status")
@click.argument("report-id")
@click.pass_context
def report_status(ctx, report_id):
    """Check status of an existing report."""
    try:
        result = reports.Reports(marketplace=Marketplaces.NA).get_report(reportId=report_id)
        payload = result.payload

        status = payload.get("status")
        name = payload.get("name", "N/A")
        start = payload.get("startDate", "N/A")
        end = payload.get("endDate", "N/A")
        created = payload.get("createdAt", "N/A")
        updated = payload.get("updatedAt", "N/A")

        click.echo(f"\n📊 Report: {name}")
        click.echo(f"   ID: {report_id}")
        click.echo(f"   Status: {status}")
        click.echo(f"   Date Range: {start} to {end}")
        click.echo(f"   Created: {created}")
        click.echo(f"   Updated: {updated}")

        if status == "COMPLETED":
            size = payload.get("fileSize", "N/A")
            click.echo(f"   File Size: {size}")
            click.echo("\n✅ Report is ready. Download with:")
            click.echo(f"   amz-ads report download {report_id}")
        elif status == "FAILED":
            reason = payload.get("failureReason", "Unknown")
            click.echo(f"\n❌ Failed: {reason}")
        else:
            click.echo("\n⏳ Still processing. Check again later.")

    except Exception as e:
        click.echo(f"❌ Error: {e}")


@report.command("download")
@click.argument("report-id")
@click.option(
    "--format",
    "fmt",
    default="table",
    type=click.Choice(["table", "json", "csv"]),
    help="Output format",
)
@click.option("--output", "-o", help="Save to file instead of stdout")
@click.pass_context
def report_download(ctx, report_id, fmt, output):
    """Download a completed report by ID."""
    try:
        result = reports.Reports(marketplace=Marketplaces.NA).get_report(reportId=report_id)
        status = result.payload.get("status")

        if status != "COMPLETED":
            click.echo(f"❌ Report is not ready (status: {status})")
            click.echo(f"   Check status: amz-ads report status {report_id}")
            return

        url = result.payload.get("url")
        if not url:
            click.echo("❌ No download URL available")
            return

        import gzip

        import requests

        click.echo("Downloading report...")
        response = requests.get(url)
        data = gzip.decompress(response.content)
        report_data = json.loads(data)

        if fmt == "json":
            output_text = json.dumps(report_data, indent=2)
        elif fmt == "csv":
            if not report_data:
                click.echo("❌ Report is empty")
                return
            import csv
            import io

            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=report_data[0].keys())
            writer.writeheader()
            writer.writerows(report_data)
            output_text = buf.getvalue()
        else:
            # Table format
            if not report_data:
                click.echo("❌ Report is empty")
                return

            # Detect report type by columns
            columns = report_data[0].keys()

            if "searchTerm" in columns:
                # Search terms report
                report_data.sort(key=lambda x: float(x.get("cost", 0) or 0), reverse=True)
                output_text = f"\n{'Search Term':<40} {'Campaign':<20} {'Spend':>8} {'Sales':>8} {'ACOS'}\n"
                output_text += "-" * 90 + "\n"
                for row in report_data[:50]:
                    term = row.get("searchTerm", "N/A")[:38]
                    camp = row.get("campaignName", "N/A")[:18]
                    cost = float(row.get("cost", 0) or 0)
                    sales = float(row.get("sales14d", 0) or 0)
                    acos = (cost / sales * 100) if sales > 0 else 0
                    output_text += f"{term:<40} {camp:<20} ${cost:>7.2f} ${sales:>7.2f} {acos:>5.1f}%\n"
            else:
                # Campaign report
                output_text = f"\n{'Campaign':<30} {'Impr':>8} {'Clicks':>7} {'Spend':>8} {'Sales':>8} {'ACOS'}\n"
                output_text += "-" * 75 + "\n"
                for row in report_data:
                    camp_name = row.get("campaignName", "N/A")[:28]
                    impr = int(row.get("impressions", 0) or 0)
                    clicks = int(row.get("clicks", 0) or 0)
                    cost = float(row.get("cost", 0) or 0)
                    sales = float(row.get("sales14d", 0) or 0)
                    acos = (cost / sales * 100) if sales > 0 else 0
                    output_text += f"{camp_name:<30} {impr:>8} {clicks:>7} ${cost:>7.2f} ${sales:>7.2f} {acos:>5.1f}%\n"

        if output:
            with open(output, "w") as f:
                f.write(output_text)
            click.echo(f"✅ Saved to {output}")
        else:
            click.echo(output_text)

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
        result = reports.Reports(marketplace=Marketplaces.NA).post_report(body=report_body)
        report_id = result.payload["reportId"]

        click.echo(f"Report submitted: {report_id}")
        click.echo("Polling for completion...")

        import time

        for i in range(30):
            result = reports.Reports(marketplace=Marketplaces.NA).get_report(reportId=report_id)
            status = result.payload.get("status")

            if status == "COMPLETED":
                import gzip

                import requests

                url = result.payload.get("url")
                response = requests.get(url)
                data = gzip.decompress(response.content)
                report_data = json.loads(data)

                # Sort by cost (highest first)
                report_data.sort(key=lambda x: float(x.get("cost", 0) or 0), reverse=True)

                click.echo(f"\n{'Search Term':<40} {'Campaign':<20} {'Spend':>8} {'Sales':>8} {'ACOS'}")
                click.echo("-" * 90)

                for row in report_data[:20]:
                    term = row.get("searchTerm", "N/A")[:38]
                    camp = row.get("campaignName", "N/A")[:18]
                    cost = float(row.get("cost", 0) or 0)
                    sales = float(row.get("sales14d", 0) or 0)
                    acos = (cost / sales * 100) if sales > 0 else 0

                    click.echo(f"{term:<40} {camp:<20} ${cost:>7.2f} ${sales:>7.2f} {acos:>5.1f}%")

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
