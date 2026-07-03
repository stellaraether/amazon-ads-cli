"""Campaign management commands."""

import click

from ..cli import handle_errors
from .campaign_entities import (
    register_adgroups_campaign_commands,
    register_asin_targets_campaign_commands,
    register_keywords_campaign_commands,
    register_negative_asin_targets_campaign_commands,
    register_negatives_campaign_commands,
    register_targets_campaign_commands,
)

#: Valid Sponsored Products dynamic bidding strategies mapped to Seller Central UI labels.
BIDDING_STRATEGIES = {
    "LEGACY_FOR_SALES": "Down only",
    "AUTO_FOR_SALES": "Up and down",
    "MANUAL": "Fixed bid",
    "RULE_BASED": "Rule-based",
}

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


def _register_campaign_management_commands(group, ensure_auth_client):
    """Register show/pause/enable/budget/bidding/placement on a campaign-scoped group."""

    @group.command("show")
    @click.pass_context
    @handle_errors
    def show_campaign(ctx):
        """Show full details for this campaign."""
        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
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

    @group.command("pause")
    @click.pass_context
    @handle_errors
    def pause_campaign(ctx):
        """Pause this campaign."""
        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
        client.edit_campaigns(body={"campaigns": [{"campaignId": campaign_id, "state": "PAUSED"}]})
        click.echo(f"✅ Campaign {campaign_id} paused")

    @group.command("enable")
    @click.pass_context
    @handle_errors
    def enable_campaign(ctx):
        """Enable this campaign."""
        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
        client.edit_campaigns(body={"campaigns": [{"campaignId": campaign_id, "state": "ENABLED"}]})
        click.echo(f"✅ Campaign {campaign_id} enabled")

    @group.command("budget")
    @click.argument("amount", type=float)
    @click.pass_context
    @handle_errors
    def set_budget(ctx, amount):
        """Set daily budget for this campaign."""
        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
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

    @group.command("bidding")
    @click.option(
        "--strategy",
        required=True,
        type=click.Choice(list(BIDDING_STRATEGIES.keys()), case_sensitive=False),
        help="Dynamic bidding strategy. " + ", ".join(f"{k} ({v})" for k, v in BIDDING_STRATEGIES.items()),
    )
    @click.pass_context
    @handle_errors
    def set_bidding(ctx, strategy):
        """Set dynamic bidding strategy for this campaign."""
        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
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

    @group.command("placement")
    @click.option("--top-of-search", type=float, help="Top of search bid adjustment percentage")
    @click.option("--product-page", type=float, help="Product page bid adjustment percentage")
    @click.pass_context
    @handle_errors
    def set_placement(ctx, top_of_search, product_page):
        """Set placement bid adjustments for this campaign."""
        if top_of_search is None and product_page is None:
            raise click.UsageError("At least one placement adjustment is required.")

        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
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


class _CampaignEntityGroup(click.Group):
    """Group that stores the resolved campaign ID in context."""

    def __init__(self, ensure_auth_client, **kwargs):
        super().__init__(**kwargs)
        self.ensure_auth_client = ensure_auth_client
        _register_campaign_management_commands(self, ensure_auth_client)
        register_negatives_campaign_commands(self, ensure_auth_client)
        register_asin_targets_campaign_commands(self, ensure_auth_client)
        register_negative_asin_targets_campaign_commands(self, ensure_auth_client)
        register_keywords_campaign_commands(self, ensure_auth_client)
        register_targets_campaign_commands(self, ensure_auth_client)
        register_adgroups_campaign_commands(self, ensure_auth_client)


class CampaignGroup(click.Group):
    """Campaign group that dispatches 'list' to a command and IDs to entity groups."""

    def __init__(self, ensure_auth_client, **kwargs):
        super().__init__(**kwargs)
        self.ensure_auth_client = ensure_auth_client
        self._entity_group = _CampaignEntityGroup(ensure_auth_client, name="<campaign-id>")

    def get_command(self, ctx, cmd_name):
        known = super().get_command(ctx, cmd_name)
        if known is not None:
            return known
        ctx.ensure_object(dict)
        ctx.obj["campaign_id"] = cmd_name
        return self._entity_group

    def format_commands(self, ctx, formatter):
        rows = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None:
                continue
            help_text = cmd.get_short_help_str(limit=80)
            rows.append((subcommand, help_text))
        rows.append(("<campaign-id>", "Campaign-scoped entity commands (show, pause, negatives, targets, etc.)."))
        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)


def register_campaigns_commands(cli_group, ensure_auth_client):
    """Register campaign management CLI commands."""

    @cli_group.group(cls=CampaignGroup, ensure_auth_client=ensure_auth_client)
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
