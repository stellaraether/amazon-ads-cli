"""Auto-targeting group command helpers.

Amazon Sponsored Products auto campaigns expose four implicit targeting groups
through the v3 /sp/targets endpoint with expressionType AUTO. This module maps
the low-level predicate types to friendly console names and registers list/set
commands scoped to either a campaign or an ad group.
"""

import click

from ..cli import handle_errors

#: Friendly CLI name -> v3 targeting expression predicate type.
AUTO_TARGET_TYPES = {
    "close-match": "QUERY_HIGH_REL_MATCHES",
    "loose-match": "QUERY_BROAD_REL_MATCHES",
    "substitutes": "ASIN_SUBSTITUTE_RELATED",
    "complements": "ASIN_ACCESSORY_RELATED",
}

#: v3 predicate type -> friendly CLI name.
PREDICATE_LABELS = {v: k for k, v in AUTO_TARGET_TYPES.items()}

#: Stable display order matching the console.
GROUP_ORDER = ["close-match", "loose-match", "substitutes", "complements"]


def _resolve_group(name):
    """Return the v3 predicate type for a friendly group name."""
    key = name.lower().replace("_", "-")
    if key not in AUTO_TARGET_TYPES:
        raise click.UsageError(f"Invalid group '{name}'. Choose from: {', '.join(GROUP_ORDER)}")
    return AUTO_TARGET_TYPES[key]


def _predicate_label(target):
    """Return the friendly label for a targeting clause, or the raw type."""
    expression = target.get("expression") or []
    pred_type = expression[0].get("type") if expression else None
    return PREDICATE_LABELS.get(pred_type, pred_type or "unknown")


def _fetch_auto_targets(client, body):
    """Return targeting clauses with expressionType AUTO for the given filter body."""
    result = client.list_product_targets(body=body)
    targets = result.payload.get("targetingClauses", [])
    return [t for t in targets if (t.get("expressionType") or "").upper() == "AUTO"]


def _fetch_default_bids(client, ad_group_ids):
    """Return a dict of adGroupId -> defaultBid."""
    if not ad_group_ids:
        return {}

    result = client.list_ad_groups(body={"adGroupIdFilter": {"include": list(ad_group_ids)}})
    return {ag["adGroupId"]: ag.get("defaultBid") for ag in result.payload.get("adGroups", [])}


def _format_adjustment(bid, default_bid):
    """Return '+N%', '-N%', or '0%' for a bid vs the ad group default bid."""
    if default_bid is None or default_bid == 0:
        return "N/A"
    pct = (bid - default_bid) / default_bid * 100
    sign = "+" if pct > 0 else ""
    return f"{sign}{pct:.0f}%"


def _build_scope_body(ctx, scope_type):
    """Build the list_product_targets filter body for the current scope."""
    if scope_type == "campaign":
        return {"campaignIdFilter": {"include": [ctx.obj["campaign_id"]]}}
    return {"adGroupIdFilter": {"include": [ctx.obj["ad_group_id"]]}}


def register_auto_targets_commands(group, ensure_auth_client, scope_type):
    """Register `auto-targets` subcommands on a campaign or ad-group scoped group."""

    @group.group("auto-targets")
    def auto_targets():
        """Auto-targeting group management."""
        pass

    @auto_targets.command("list")
    @click.pass_context
    @handle_errors
    def list_auto_targets(ctx):
        """List auto-targeting groups."""
        _, client = ensure_auth_client(ctx)
        body = _build_scope_body(ctx, scope_type)
        auto_targets_list = _fetch_auto_targets(client, body)

        if not auto_targets_list:
            click.echo("No auto-targeting groups found.")
            return

        ad_group_ids = {t.get("adGroupId") for t in auto_targets_list if t.get("adGroupId")}
        default_bids = _fetch_default_bids(client, ad_group_ids)

        click.echo(f"\n{'Group':<15} {'Target ID':<20} {'Ad Group ID':<20} {'State':<10} {'Bid':<12} {'vs Default'}")
        click.echo("-" * 95)

        def sort_key(target):
            label = _predicate_label(target)
            return GROUP_ORDER.index(label) if label in GROUP_ORDER else 99

        for target in sorted(auto_targets_list, key=sort_key):
            label = _predicate_label(target)
            target_id = target.get("targetId", "N/A")[:18]
            ad_group_id = target.get("adGroupId", "N/A")[:18]
            state = target.get("state", "N/A")
            default_bid = default_bids.get(target.get("adGroupId"))
            bid = target.get("bid")

            if bid is not None:
                bid_str = f"${bid:.2f}"
                adjustment = _format_adjustment(bid, default_bid)
            elif default_bid is not None:
                bid_str = f"${default_bid:.2f}*"
                adjustment = "0% (inherited)"
            else:
                bid_str = "N/A"
                adjustment = "N/A"

            click.echo(f"{label:<15} {target_id:<20} {ad_group_id:<20} {state:<10} {bid_str:<12} {adjustment}")

    @auto_targets.command("set")
    @click.argument("group_name")
    @click.option(
        "--state",
        type=click.Choice(["enabled", "disabled"], case_sensitive=False),
        help="Enable or disable the targeting group.",
    )
    @click.option(
        "--bid-adjustment",
        type=float,
        help="Bid adjustment percentage relative to the ad group default bid.",
    )
    @click.option("--bid", type=float, help="Absolute bid amount.")
    @click.pass_context
    @handle_errors
    def set_auto_target(ctx, group_name, state, bid_adjustment, bid):
        """Set state or bid for an auto-targeting group."""
        if state is None and bid_adjustment is None and bid is None:
            raise click.UsageError("At least one of --state, --bid-adjustment, or --bid is required.")
        if bid_adjustment is not None and bid is not None:
            raise click.UsageError("Use either --bid-adjustment or --bid, not both.")

        _, client = ensure_auth_client(ctx)
        predicate = _resolve_group(group_name)
        body = _build_scope_body(ctx, scope_type)
        auto_targets_list = _fetch_auto_targets(client, body)

        matching = [t for t in auto_targets_list if (t.get("expression") or [{}])[0].get("type") == predicate]

        if not matching:
            raise click.ClickException(f"Auto-targeting group '{group_name}' not found in this scope.")

        default_bids = {}
        if bid_adjustment is not None:
            ad_group_ids = {t.get("adGroupId") for t in matching if t.get("adGroupId")}
            default_bids = _fetch_default_bids(client, ad_group_ids)

        updates = []
        for target in matching:
            update = {"targetId": target["targetId"]}
            if state is not None:
                update["state"] = state.upper()

            if bid is not None:
                update["bid"] = bid
            elif bid_adjustment is not None:
                ad_group_id = target.get("adGroupId")
                default_bid = default_bids.get(ad_group_id)
                if default_bid is None:
                    raise click.ClickException(f"Could not determine default bid for ad group {ad_group_id}.")
                update["bid"] = round(default_bid * (1 + bid_adjustment / 100), 2)

            updates.append(update)

        client.edit_product_targets(body={"targetingClauses": updates})

        parts = []
        if state:
            parts.append(f"state={state.upper()}")
        if bid is not None:
            parts.append(f"bid=${bid:.2f}")
        elif bid_adjustment is not None:
            bids = ", ".join(f"${u['bid']:.2f}" for u in updates)
            parts.append(f"bid={bids}")

        count = len(updates)
        scope_word = "ad group" if scope_type == "ad_group" else "ad group(s)"
        click.echo(f"✅ Updated {group_name} in {count} {scope_word} ({', '.join(parts)})")

    @auto_targets.command("recommend")
    @click.pass_context
    @handle_errors
    def recommend_auto_targets(ctx):
        """Get bid recommendations for auto-targeting groups."""
        _, client = ensure_auth_client(ctx)
        body = _build_scope_body(ctx, scope_type)
        auto_targets_list = _fetch_auto_targets(client, body)

        if not auto_targets_list:
            raise click.ClickException("No auto-targeting groups found in this scope.")

        first = auto_targets_list[0]
        campaign_id = first.get("campaignId")
        ad_group_id = first.get("adGroupId")

        if not campaign_id or not ad_group_id:
            raise click.ClickException("Could not determine campaign/ad group for recommendations.")

        result = client.get_targeting_bid_recommendations(
            body={
                "recommendationType": "BIDS_FOR_EXISTING_AD_GROUP",
                "campaignId": campaign_id,
                "adGroupId": ad_group_id,
                "targetingExpressions": [
                    {"type": "CLOSE_MATCH"},
                    {"type": "LOOSE_MATCH"},
                    {"type": "SUBSTITUTES"},
                    {"type": "COMPLEMENTS"},
                ],
            }
        )

        recommendations = result.payload.get("bidRecommendations", [])
        if not recommendations:
            click.echo("No recommendations available.")
            return

        rec = recommendations[0]
        click.echo(f"\n📊 Bid recommendations (theme: {rec.get('theme', 'N/A')})")
        click.echo(f"{'Group':<15} {'Suggested Bids'}")
        click.echo("-" * 45)

        for expr_rec in rec.get("bidRecommendationsForTargetingExpressions", []):
            pred = expr_rec.get("targetingExpression", {}).get("type")
            label = {
                "CLOSE_MATCH": "close-match",
                "LOOSE_MATCH": "loose-match",
                "SUBSTITUTES": "substitutes",
                "COMPLEMENTS": "complements",
            }.get(pred, pred)
            bids = [f"${v['suggestedBid']:.2f}" for v in expr_rec.get("bidValues", [])]
            click.echo(f"{label:<15} {', '.join(bids) if bids else 'N/A'}")
