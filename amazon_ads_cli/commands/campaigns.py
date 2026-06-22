"""Campaign management commands."""

import click

from ..cli import handle_errors

#: Valid Sponsored Products dynamic bidding strategies.
BIDDING_STRATEGIES = ["LEGACY_FOR_SALES", "AUTO_FOR_SALES", "MANUAL", "RULE_BASED"]

#: Maps friendly option names to Amazon API placement values.
PLACEMENTS = {
    "top_of_search": "PLACEMENT_TOP",
    "product_page": "PLACEMENT_PRODUCT_PAGE",
}


def _format_bidding(camp):
    """Return a human-readable bidding strategy string."""
    dynamic_bidding = camp.get("dynamicBidding") or {}
    return dynamic_bidding.get("strategy", "N/A")


def _format_placement(camp):
    """Return placement adjustments as a compact string."""
    dynamic_bidding = camp.get("dynamicBidding") or {}
    placement_bidding = dynamic_bidding.get("placementBidding") or []
    if not placement_bidding:
        return "N/A"
    parts = []
    for adj in placement_bidding:
        placement = adj.get("placement", "")
        percentage = adj.get("percentage")
        label = {"PLACEMENT_TOP": "Top", "PLACEMENT_PRODUCT_PAGE": "Product"}.get(placement, placement)
        parts.append(f"{label} {percentage}%")
    return ", ".join(parts) if parts else "N/A"


def _fetch_campaign(client, campaign_id):
    """Fetch a single campaign by ID."""
    result = client.list_campaigns(body={"campaignIdFilter": {"include": [campaign_id]}})
    campaigns = result.payload.get("campaigns", [])
    if not campaigns:
        raise click.ClickException(f"Campaign {campaign_id} not found")
    return campaigns[0]


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

        click.echo(
            f"\n{'ID':<20} {'Campaign':<28} {'State':<10} {'Budget':<10} {'Type':<8} {'Bidding':<18} {'Placements'}"
        )
        click.echo("-" * 117)
        for camp in campaigns:
            cid = camp["campaignId"][:18]
            name = camp["name"][:26]
            state = camp["state"]
            budget = f"${camp['budget']['budget']}"
            ctype = camp.get("targetingType", "N/A")
            bidding = _format_bidding(camp)
            placement = _format_placement(camp)[:26]
            click.echo(f"{cid:<20} {name:<28} {state:<10} {budget:<10} {ctype:<8} {bidding:<18} {placement}")

    @campaigns.command("show")
    @click.argument("campaign-id")
    @click.pass_context
    @handle_errors
    def show_campaign(ctx, campaign_id):
        """Show full details for a campaign."""
        _, client = ensure_auth_client(ctx)
        camp = _fetch_campaign(client, campaign_id)
        click.echo(f"\n📋 Campaign: {camp['name']}")
        click.echo(f"   ID: {camp['campaignId']}")
        click.echo(f"   State: {camp['state']}")
        click.echo(f"   Budget: ${camp['budget']['budget']}/{camp['budget']['budgetType'].lower()}")
        click.echo(f"   Type: {camp.get('targetingType', 'N/A')}")
        click.echo(f"   Start: {camp.get('startDate', 'N/A')}")
        click.echo(f"   End: {camp.get('endDate', 'N/A') or 'No end date'}")
        click.echo(f"   Bidding strategy: {_format_bidding(camp)}")

        placement = _format_placement(camp)
        if placement != "N/A":
            click.echo(f"   Placement adjustments: {placement}")

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

    @campaigns.command("bidding")
    @click.argument("campaign-id")
    @click.option(
        "--strategy",
        required=True,
        type=click.Choice(BIDDING_STRATEGIES, case_sensitive=False),
        help="Dynamic bidding strategy",
    )
    @click.pass_context
    @handle_errors
    def set_bidding(ctx, campaign_id, strategy):
        """Set campaign dynamic bidding strategy."""
        _, client = ensure_auth_client(ctx)
        camp = _fetch_campaign(client, campaign_id)
        existing = camp.get("dynamicBidding") or {}
        strategy = strategy.upper()
        client.edit_campaigns(
            body={
                "campaigns": [
                    {
                        "campaignId": campaign_id,
                        "dynamicBidding": {
                            "strategy": strategy,
                            "placementBidding": existing.get("placementBidding") or [],
                        },
                    }
                ]
            }
        )
        click.echo(f"✅ Campaign {campaign_id} bidding strategy set to {strategy}")

    @campaigns.command("placement")
    @click.argument("campaign-id")
    @click.option("--top-of-search", type=float, help="Top of search bid adjustment percentage")
    @click.option("--product-page", type=float, help="Product page bid adjustment percentage")
    @click.pass_context
    @handle_errors
    def set_placement(ctx, campaign_id, top_of_search, product_page):
        """Set campaign placement bid adjustments."""
        if top_of_search is None and product_page is None:
            raise click.UsageError("At least one placement adjustment is required.")

        _, client = ensure_auth_client(ctx)
        camp = _fetch_campaign(client, campaign_id)
        existing = camp.get("dynamicBidding") or {}

        placement_bidding = []
        for option, placement in PLACEMENTS.items():
            value = locals()[option]
            if value is not None:
                placement_bidding.append({"placement": placement, "percentage": value})

        client.edit_campaigns(
            body={
                "campaigns": [
                    {
                        "campaignId": campaign_id,
                        "dynamicBidding": {
                            "strategy": existing.get("strategy", "AUTO_FOR_SALES"),
                            "placementBidding": placement_bidding,
                        },
                    }
                ]
            }
        )

        parts = [f"{adj['placement']} {adj['percentage']}%" for adj in placement_bidding]
        click.echo(f"✅ Campaign {campaign_id} placement adjustments set: {', '.join(parts)}")
