"""Campaign management commands."""

import re

import click

from ..cli import handle_errors
from .campaign_entities import (
    register_adgroups_campaign_commands,
    register_asin_targets_campaign_commands,
    register_auto_targets_campaign_commands,
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
    "rest_of_search": "PLACEMENT_REST_OF_SEARCH",
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
        label = {
            "PLACEMENT_TOP": "Top",
            "PLACEMENT_PRODUCT_PAGE": "Product",
            "PLACEMENT_REST_OF_SEARCH": "Rest",
        }.get(placement, placement)
        parts.append(f"{label} {percentage}%")
    return ", ".join(parts) if parts else "N/A"


_ISO_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_COMPACT_DATE_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})$")


def _normalize_date(date_value):
    """Return YYYY-MM-DD, converting YYYYMMDD if necessary.

    The Amazon Advertising API v3 accepts ISO-style dates (YYYY-MM-DD) for
    campaign start/end dates even though the client library docstrings claim
    YYYYMMDD.
    """
    if date_value is None:
        return None
    if _ISO_DATE_RE.match(date_value):
        return date_value
    match = _COMPACT_DATE_RE.match(date_value)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    raise click.BadParameter(f"Invalid date '{date_value}'. Expected YYYY-MM-DD or YYYYMMDD.")


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
    @click.option("--rest-of-search", type=float, help="Rest of search bid adjustment percentage")
    @click.pass_context
    @handle_errors
    def set_placement(ctx, top_of_search, product_page, rest_of_search):
        """Set placement bid adjustments for this campaign."""
        if top_of_search is None and product_page is None and rest_of_search is None:
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
        register_auto_targets_campaign_commands(self, ensure_auth_client)
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

    @campaigns.command("create")
    @click.option("--name", required=True, help="Campaign name (max 128 characters)")
    @click.option("--budget", required=True, type=float, help="Daily budget amount")
    @click.option(
        "--targeting-type",
        required=True,
        type=click.Choice(["AUTO", "MANUAL"], case_sensitive=False),
        help="Campaign targeting type",
    )
    @click.option(
        "--state",
        default="ENABLED",
        type=click.Choice(["ENABLED", "PAUSED"], case_sensitive=False),
        show_default=True,
        help="Initial campaign state",
    )
    @click.option("--start-date", help="Start date (YYYY-MM-DD or YYYYMMDD)")
    @click.option("--end-date", help="End date (YYYY-MM-DD or YYYYMMDD)")
    @click.option(
        "--bidding-strategy",
        type=click.Choice(list(BIDDING_STRATEGIES.keys()), case_sensitive=False),
        help="Dynamic bidding strategy. " + ", ".join(f"{k} ({v})" for k, v in BIDDING_STRATEGIES.items()),
    )
    @click.option("--top-of-search", type=float, help="Top of search bid adjustment percentage")
    @click.option("--product-page", type=float, help="Product page bid adjustment percentage")
    @click.option("--rest-of-search", type=float, help="Rest of search bid adjustment percentage")
    @click.option("--portfolio-id", type=int, help="Portfolio ID")
    @click.pass_context
    @handle_errors
    def create_campaign(
        ctx,
        name,
        budget,
        targeting_type,
        state,
        start_date,
        end_date,
        bidding_strategy,
        top_of_search,
        product_page,
        rest_of_search,
        portfolio_id,
    ):
        """Create a new Sponsored Products campaign."""
        if (
            top_of_search is not None or product_page is not None or rest_of_search is not None
        ) and bidding_strategy is None:
            raise click.UsageError("--bidding-strategy is required when placement adjustments are provided.")

        _, client = ensure_auth_client(ctx)

        campaign = {
            "name": name,
            "state": state.upper(),
            "budget": {"budgetType": "DAILY", "budget": budget},
            "targetingType": targeting_type.upper(),
        }

        if portfolio_id is not None:
            campaign["portfolioId"] = portfolio_id

        normalized_start = _normalize_date(start_date)
        if normalized_start is not None:
            campaign["startDate"] = normalized_start

        normalized_end = _normalize_date(end_date)
        if normalized_end is not None:
            campaign["endDate"] = normalized_end

        placement_bidding = []
        for option, placement in PLACEMENTS.items():
            value = locals()[option]
            if value is not None:
                placement_bidding.append({"placement": placement, "percentage": value})

        if bidding_strategy is not None or placement_bidding:
            campaign["dynamicBidding"] = {
                "strategy": bidding_strategy.upper() if bidding_strategy else "AUTO_FOR_SALES",
                "placementBidding": placement_bidding,
            }

        result = client.create_campaigns(body={"campaigns": [campaign]})
        response = result.payload.get("campaigns", {})
        success = response.get("success", [])
        errors = response.get("error", [])

        if errors:
            error_detail = errors[0].get("details", errors[0].get("message", str(errors[0])))
            raise click.ClickException(f"Campaign creation failed: {error_detail}")

        if success:
            created = success[0]
            click.echo(f"✅ Created campaign: {name} (ID: {created.get('campaignId', 'N/A')})")
        else:
            click.echo("✅ Campaign created")

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
