#!/usr/bin/env python3
"""Amazon Ads CLI - Command line interface for Amazon Advertising API v3."""

import click
import json
from datetime import datetime, timedelta
from ad_api.api import sponsored_products, reports
from ad_api.base import Marketplaces


@click.group()
@click.option('--profile', '-p', default='default', help='Credential profile')
@click.pass_context
def cli(ctx, profile):
    """Amazon Ads CLI - Manage campaigns, keywords, and reports."""
    ctx.ensure_object(dict)
    ctx.obj['profile'] = profile


@cli.group()
def campaigns():
    """Campaign management commands."""
    pass


@campaigns.command('list')
@click.pass_context
def list_campaigns(ctx):
    """List all campaigns."""
    result = sponsored_products.CampaignsV3(marketplace=Marketplaces.NA).list_campaigns(body={})
    campaigns = result.payload.get('campaigns', [])
    
    click.echo(f"\n{'Campaign':<30} {'State':<10} {'Budget':<10} {'Type'}")
    click.echo("-" * 65)
    for camp in campaigns:
        name = camp['name'][:28]
        state = camp['state']
        budget = f"${camp['budget']['budget']}"
        ctype = camp.get('targetingType', 'N/A')
        click.echo(f"{name:<30} {state:<10} {budget:<10} {ctype}")


@campaigns.command('pause')
@click.argument('campaign-id')
@click.pass_context
def pause_campaign(ctx, campaign_id):
    """Pause a campaign."""
    try:
        result = sponsored_products.CampaignsV3(marketplace=Marketplaces.NA).edit_campaigns(
            body={"campaigns": [{"campaignId": campaign_id, "state": "PAUSED"}]}
        )
        click.echo(f"✅ Campaign {campaign_id} paused")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@campaigns.command('enable')
@click.argument('campaign-id')
@click.pass_context
def enable_campaign(ctx, campaign_id):
    """Enable a campaign."""
    try:
        result = sponsored_products.CampaignsV3(marketplace=Marketplaces.NA).edit_campaigns(
            body={"campaigns": [{"campaignId": campaign_id, "state": "ENABLED"}]}
        )
        click.echo(f"✅ Campaign {campaign_id} enabled")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.group()
def keywords():
    """Keyword management commands."""
    pass


@keywords.command('list')
@click.argument('campaign-id')
@click.pass_context
def list_keywords(ctx, campaign_id):
    """List keywords for a campaign."""
    result = sponsored_products.KeywordsV3(marketplace=Marketplaces.NA).list_keywords(body={})
    keywords = [k for k in result.payload.get('keywords', []) if k.get('campaignId') == campaign_id]
    
    click.echo(f"\n{'Keyword':<35} {'Match':<10} {'Bid':<8} {'State'}")
    click.echo("-" * 70)
    for kw in keywords:
        text = kw['keywordText'][:33]
        match = kw['matchType']
        bid = f"${kw['bid']}"
        state = kw['state']
        click.echo(f"{text:<35} {match:<10} {bid:<8} {state}")


@cli.group()
def report():
    """Report commands."""
    pass


@report.command('today')
@click.pass_context
def report_today(ctx):
    """Get today's performance report."""
    today = datetime.now().strftime('%Y-%m-%d')
    
    click.echo(f"Requesting report for {today}...")
    
    report_body = {
        "name": f"SP_Today_{today}",
        "startDate": today,
        "endDate": today,
        "configuration": {
            "adProduct": "SPONSORED_PRODUCTS",
            "columns": [
                "impressions", "clicks", "cost",
                "purchases14d", "sales14d",
                "campaignName", "campaignId"
            ],
            "reportTypeId": "spCampaigns",
            "format": "GZIP_JSON",
            "groupBy": ["campaign"],
            "timeUnit": "SUMMARY"
        }
    }
    
    try:
        # Submit report
        result = reports.Reports(marketplace=Marketplaces.NA).post_report(body=report_body)
        report_id = result.payload['reportId']
        
        click.echo(f"Report submitted: {report_id}")
        click.echo("Polling for completion...")
        
        # Poll
        import time
        for i in range(20):
            result = reports.Reports(marketplace=Marketplaces.NA).get_report(reportId=report_id)
            status = result.payload.get('status')
            
            if status == 'COMPLETED':
                # Download
                import requests
                import gzip
                
                url = result.payload.get('url')
                response = requests.get(url)
                data = gzip.decompress(response.content)
                report_data = json.loads(data)
                
                click.echo(f"\n{'Campaign':<30} {'Impr':>8} {'Clicks':>7} {'Spend':>8} {'Sales':>8} {'ACOS'}")
                click.echo("-" * 75)
                
                for row in report_data:
                    camp_name = row.get('campaignName', 'N/A')[:28]
                    impr = int(row.get('impressions', 0) or 0)
                    clicks = int(row.get('clicks', 0) or 0)
                    cost = float(row.get('cost', 0) or 0)
                    sales = float(row.get('sales14d', 0) or 0)
                    acos = (cost / sales * 100) if sales > 0 else 0
                    
                    click.echo(f"{camp_name:<30} {impr:>8} {clicks:>7} ${cost:>7.2f} ${sales:>7.2f} {acos:>5.1f}%")
                
                return
            
            elif status == 'FAILED':
                click.echo(f"❌ Report failed: {result.payload.get('failureReason')}")
                return
            
            time.sleep(3)
        
        click.echo("⏳ Report still processing...")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")


if __name__ == '__main__':
    cli()
