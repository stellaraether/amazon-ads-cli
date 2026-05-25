"""Product target management commands."""

import click

from ..cli import handle_errors


def register_targets_commands(cli_group, ensure_auth_client):
    """Register product target management CLI commands."""

    @cli_group.group()
    def targets():
        """Product target management commands."""
        pass

    @targets.command("list-all")
    @click.pass_context
    @handle_errors
    def list_all_targets(ctx):
        """List all product targets across all campaigns."""
        _, client = ensure_auth_client(ctx)
        result = client.list_product_targets(body={})
        targets_list = result.payload.get("productTargets", [])

        click.echo(f"\n{'Campaign ID':<20} {'Ad Group ID':<20} {'Expression':<40} {'State'}")
        click.echo("-" * 95)
        for t in targets_list:
            camp_id = t.get("campaignId", "N/A")[:18]
            ag_id = t.get("adGroupId", "N/A")[:18]
            expr = str(t.get("expression", []))[:38]
            state = t.get("state", "N/A")
            click.echo(f"{camp_id:<20} {ag_id:<20} {expr:<40} {state}")

    @targets.command("delete")
    @click.argument("target-id")
    @click.pass_context
    @handle_errors
    def delete_target(ctx, target_id):
        """Delete a product target by ID."""
        _, client = ensure_auth_client(ctx)
        client.delete_product_targets(body={"targetIdFilter": {"include": [target_id]}})
        click.echo(f"✅ Deleted target: {target_id}")
