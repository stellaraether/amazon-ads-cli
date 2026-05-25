"""Report commands."""

import csv
import gzip
import io
import json
from datetime import datetime, timedelta

import click
import requests

from ..cli import handle_errors


def register_report_commands(cli_group, ensure_auth_client):
    """Register report CLI commands."""

    @cli_group.group()
    def report():
        """Report commands."""
        pass

    @report.command("today")
    @click.pass_context
    @handle_errors
    def report_today(ctx):
        """Get today's performance report."""
        _, client = ensure_auth_client(ctx)
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

        # Submit report
        result = client.post_report(body=report_body)
        report_id = result.payload["reportId"]

        click.echo(f"Report submitted: {report_id}")
        click.echo("Polling for completion...")

        for i in range(20):
            result = client.get_report(report_id)
            status = result.payload.get("status")

            if status == "COMPLETED":
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

            import time

            time.sleep(3)

        click.echo("⏳ Report still processing...")

    @report.command("status")
    @click.argument("report-id")
    @click.pass_context
    @handle_errors
    def report_status(ctx, report_id):
        """Check status of an existing report."""
        _, client = ensure_auth_client(ctx)
        result = client.get_report(report_id)
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
    @handle_errors
    def report_download(ctx, report_id, fmt, output):
        """Download a completed report by ID."""
        _, client = ensure_auth_client(ctx)
        result = client.get_report(report_id)
        status = result.payload.get("status")

        if status != "COMPLETED":
            click.echo(f"❌ Report is not ready (status: {status})")
            click.echo(f"   Check status: amz-ads report status {report_id}")
            return

        url = result.payload.get("url")
        if not url:
            click.echo("❌ No download URL available")
            return

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
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=report_data[0].keys())
            writer.writeheader()
            writer.writerows(report_data)
            output_text = buf.getvalue()
        else:
            if not report_data:
                click.echo("❌ Report is empty")
                return

            columns = report_data[0].keys()

            if "searchTerm" in columns:
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

    @report.command("search-terms")
    @click.option("--days", default=7, help="Number of days to look back")
    @click.pass_context
    @handle_errors
    def search_terms_report(ctx, days):
        """Get search term report."""
        _, client = ensure_auth_client(ctx)
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

        result = client.post_report(body=report_body)
        report_id = result.payload["reportId"]

        click.echo(f"Report submitted: {report_id}")
        click.echo("Polling for completion...")

        for i in range(30):
            result = client.get_report(report_id)
            status = result.payload.get("status")

            if status == "COMPLETED":
                url = result.payload.get("url")
                response = requests.get(url)
                data = gzip.decompress(response.content)
                report_data = json.loads(data)

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

            import time

            time.sleep(5)

        click.echo("⏳ Report still processing...")
