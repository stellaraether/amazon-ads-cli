"""Campaign management commands."""

import click

from ..cli import handle_errors


def register_campaigns_commands(cli_group, ensure_auth_client):
    """Register campaign management CLI commands."""

    @cli_group.group()
    def campaigns():
        """Campaign management commands."""
        pass

    @campaigns.command("list")
    @click.pass_context
    @handle_errors
    def list_campaigns(ctx):
        """List all campaigns."""
        _, client = ensure_auth_client(ctx)
        result = client.list_campaigns(body={})
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
    @handle_errors
    def show_campaign(ctx, campaign_id):
        """Show full details for a campaign."""
        _, client = ensure_auth_client(ctx)
        result = client.list_campaigns(body={"campaignIdFilter": {"include": [campaign_id]}})
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
    @handle_errors
    def pause_campaign(ctx, campaign_id):
        """Pause a campaign."""
        _, client = ensure_auth_client(ctx)
        client.edit_campaigns(body={"campaigns": [{"campaignId": campaign_id, "state": "PAUSED"}]})
        click.echo(f"✅ Campaign {campaign_id} paused")

    @campaigns.command("enable")
    @click.argument("campaign-id")
    @click.pass_context
    @handle_errors
    def enable_campaign(ctx, campaign_id):
        """Enable a campaign."""
        _, client = ensure_auth_client(ctx)
        client.edit_campaigns(body={"campaigns": [{"campaignId": campaign_id, "state": "ENABLED"}]})
        click.echo(f"✅ Campaign {campaign_id} enabled")

    @campaigns.command("budget")
    @click.argument("campaign-id")
    @click.argument("amount", type=float)
    @click.pass_context
    @handle_errors
    def set_budget(ctx, campaign_id, amount):
        """Set campaign daily budget."""
        _, client = ensure_auth_client(ctx)
        client.edit_campaigns(
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
