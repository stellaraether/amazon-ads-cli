"""Ad group management commands."""

import click

from ..cli import handle_errors


def register_adgroups_commands(cli_group, ensure_auth_client):
    """Register ad group management CLI commands."""

    @cli_group.group()
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
