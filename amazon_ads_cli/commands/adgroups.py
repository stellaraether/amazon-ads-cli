"""Ad group management commands."""

import click

from ..cli import extract_error_detail, handle_errors
from .adgroup_entities import (
    register_asin_targets_adgroup_commands,
    register_auto_targets_adgroup_commands,
    register_keywords_adgroup_commands,
    register_negative_asin_targets_adgroup_commands,
    register_negatives_adgroup_commands,
    register_product_ads_adgroup_commands,
    register_targets_adgroup_commands,
)


def _fetch_ad_group(client, ad_group_id):
    """Fetch a single ad group by ID, including archived ones."""
    result = client.list_ad_groups(
        body={
            "adGroupIdFilter": {"include": [ad_group_id]},
            "stateFilter": {"include": ["ENABLED", "PAUSED", "ARCHIVED"]},
        }
    )
    ad_groups = result.payload.get("adGroups", [])
    if not ad_groups:
        raise click.ClickException(f"Ad group {ad_group_id} not found")
    return ad_groups[0]


def _check_ad_group_errors(result, action):
    """Raise on per-item errors in an ad group create/edit response."""
    errors = result.payload.get("adGroups", {}).get("error", [])
    if errors:
        raise click.ClickException(f"Ad group {action} failed: {extract_error_detail(errors[0])}")


def _register_adgroup_management_commands(group, ensure_auth_client):
    """Register show/bid/enable/pause/archive on an ad-group-scoped group."""

    @group.command("show")
    @click.pass_context
    @handle_errors
    def show_adgroup(ctx):
        """Show full details for this ad group."""
        _, client = ensure_auth_client(ctx)
        ad_group_id = ctx.obj["ad_group_id"]
        ad_group = _fetch_ad_group(client, ad_group_id)
        click.echo(f"\n📋 Ad group: {ad_group['name']}")
        click.echo(f"   ID: {ad_group['adGroupId']}")
        click.echo(f"   Campaign ID: {ad_group['campaignId']}")
        click.echo(f"   State: {ad_group['state']}")
        click.echo(f"   Default bid: ${ad_group.get('defaultBid', 'N/A')}")

    @group.command("bid")
    @click.argument("amount", type=float)
    @click.pass_context
    @handle_errors
    def set_bid(ctx, amount):
        """Set the default bid for this ad group (amount in dollars)."""
        _, client = ensure_auth_client(ctx)
        ad_group_id = ctx.obj["ad_group_id"]
        result = client.edit_ad_groups(body={"adGroups": [{"adGroupId": ad_group_id, "defaultBid": amount}]})
        _check_ad_group_errors(result, "bid update")
        click.echo(f"✅ Ad group {ad_group_id} default bid set to ${amount}")

    @group.command("enable")
    @click.pass_context
    @handle_errors
    def enable_adgroup(ctx):
        """Enable this ad group."""
        _, client = ensure_auth_client(ctx)
        ad_group_id = ctx.obj["ad_group_id"]
        result = client.edit_ad_groups(body={"adGroups": [{"adGroupId": ad_group_id, "state": "ENABLED"}]})
        _check_ad_group_errors(result, "enable")
        click.echo(f"✅ Ad group {ad_group_id} enabled")

    @group.command("pause")
    @click.pass_context
    @handle_errors
    def pause_adgroup(ctx):
        """Pause this ad group."""
        _, client = ensure_auth_client(ctx)
        ad_group_id = ctx.obj["ad_group_id"]
        result = client.edit_ad_groups(body={"adGroups": [{"adGroupId": ad_group_id, "state": "PAUSED"}]})
        _check_ad_group_errors(result, "pause")
        click.echo(f"✅ Ad group {ad_group_id} paused")

    @group.command("archive")
    @click.pass_context
    @handle_errors
    def archive_adgroup(ctx):
        """Archive this ad group. The name can then be reused."""
        _, client = ensure_auth_client(ctx)
        ad_group_id = ctx.obj["ad_group_id"]
        client.delete_ad_groups(body={"adGroupIdFilter": {"include": [ad_group_id]}})
        click.echo(f"✅ Ad group {ad_group_id} archived")


class _AdgroupEntityGroup(click.Group):
    """Group that stores the resolved ad group ID in context."""

    def __init__(self, ensure_auth_client, **kwargs):
        super().__init__(**kwargs)
        self.ensure_auth_client = ensure_auth_client
        _register_adgroup_management_commands(self, ensure_auth_client)
        register_negatives_adgroup_commands(self, ensure_auth_client)
        register_asin_targets_adgroup_commands(self, ensure_auth_client)
        register_negative_asin_targets_adgroup_commands(self, ensure_auth_client)
        register_keywords_adgroup_commands(self, ensure_auth_client)
        register_targets_adgroup_commands(self, ensure_auth_client)
        register_auto_targets_adgroup_commands(self, ensure_auth_client)
        register_product_ads_adgroup_commands(self, ensure_auth_client)


class AdgroupGroup(click.Group):
    """Ad group group that dispatches 'list' to a command and IDs to entity groups."""

    def __init__(self, ensure_auth_client, **kwargs):
        super().__init__(**kwargs)
        self.ensure_auth_client = ensure_auth_client
        self._entity_group = _AdgroupEntityGroup(ensure_auth_client, name="<ad-group-id>")

    def get_command(self, ctx, cmd_name):
        known = super().get_command(ctx, cmd_name)
        if known is not None:
            return known
        ctx.ensure_object(dict)
        ctx.obj["ad_group_id"] = cmd_name
        return self._entity_group

    def format_commands(self, ctx, formatter):
        rows = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None:
                continue
            help_text = cmd.get_short_help_str(limit=80)
            rows.append((subcommand, help_text))
        rows.append(("<ad-group-id>", "Ad-group-scoped entity commands (show, bid, product-ads, targets, etc.)."))
        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)


def register_adgroups_commands(cli_group, ensure_auth_client):
    """Register ad group management CLI commands."""

    @cli_group.group(cls=AdgroupGroup, ensure_auth_client=ensure_auth_client)
    def adgroups():
        """Ad group management commands."""
        pass

    @adgroups.command("list")
    @click.option("--campaign-id", help="Filter by campaign ID")
    @click.pass_context
    @handle_errors
    def list_adgroups(ctx, campaign_id):
        """List all ad groups."""
        _, client = ensure_auth_client(ctx)
        body = {}
        if campaign_id:
            body["campaignIdFilter"] = {"include": [campaign_id]}

        result = client.list_ad_groups(body=body)
        ad_groups = result.payload.get("adGroups", [])

        click.echo(f"\n{'ID':<20} {'Campaign ID':<20} {'Name':<30} {'State'}")
        click.echo("-" * 85)
        for ag in ad_groups:
            ag_id = ag["adGroupId"][:18]
            camp_id = ag["campaignId"][:18]
            name = ag["name"][:28]
            state = ag["state"]
            click.echo(f"{ag_id:<20} {camp_id:<20} {name:<30} {state}")
