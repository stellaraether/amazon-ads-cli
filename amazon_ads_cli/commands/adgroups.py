"""Ad group management commands."""

import click

from ..cli import handle_errors
from .adgroup_entities import (
    register_asin_targets_adgroup_commands,
    register_keywords_adgroup_commands,
    register_negative_asin_targets_adgroup_commands,
    register_negatives_adgroup_commands,
    register_targets_adgroup_commands,
)


class _AdgroupEntityGroup(click.Group):
    """Group that stores the resolved ad group ID in context."""

    def __init__(self, ensure_auth_client, **kwargs):
        super().__init__(**kwargs)
        self.ensure_auth_client = ensure_auth_client
        register_negatives_adgroup_commands(self, ensure_auth_client)
        register_asin_targets_adgroup_commands(self, ensure_auth_client)
        register_negative_asin_targets_adgroup_commands(self, ensure_auth_client)
        register_keywords_adgroup_commands(self, ensure_auth_client)
        register_targets_adgroup_commands(self, ensure_auth_client)


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
        rows.append(("<ad-group-id>", "Ad-group-scoped entity commands (negatives, targets, etc.)."))
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
