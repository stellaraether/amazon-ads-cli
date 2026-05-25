"""ASIN target management commands."""

import click

from ..cli import handle_errors


def register_asin_targets_commands(cli_group, ensure_auth_client):
    """Register ASIN target management CLI commands."""

    @cli_group.group("asin-targets")
    def asin_targets():
        """ASIN target management commands."""
        pass

    @asin_targets.command("add")
    @click.argument("campaign-id")
    @click.argument("ad-group-id")
    @click.argument("asin")
    @click.option("--bid", default=1.0, help="Bid amount")
    @click.pass_context
    @handle_errors
    def add_asin_target(ctx, campaign_id, ad_group_id, asin, bid):
        """Add an ASIN target to a campaign ad group."""
        _, client = ensure_auth_client(ctx)
        result = client.create_product_targets(
            body={
                "targetingClauses": [
                    {
                        "campaignId": campaign_id,
                        "adGroupId": ad_group_id,
                        "expression": [{"value": asin, "type": "ASIN_SAME_AS"}],
                        "expressionType": "MANUAL",
                        "state": "ENABLED",
                        "bid": bid,
                    }
                ]
            }
        )
        success = result.payload.get("targetingClauses", {}).get("success", [])
        errors = result.payload.get("targetingClauses", {}).get("error", [])
        if success:
            target_id = success[0].get("targetId")
            click.echo(f"✅ Added ASIN target: {asin} (ID: {target_id}) - ${bid}")
        elif errors:
            msg = (
                errors[0]
                .get("errors", [{}])[0]
                .get("errorValue", {})
                .get("otherError", {})
                .get("message", "Unknown error")
            )
            click.echo(f"❌ Error: {msg}")

    @asin_targets.command("remove")
    @click.argument("target-id")
    @click.pass_context
    @handle_errors
    def remove_asin_target(ctx, target_id):
        """Remove an ASIN target by ID."""
        _, client = ensure_auth_client(ctx)
        client.delete_product_targets(body={"targetIdFilter": {"include": [target_id]}})
        click.echo(f"✅ Removed ASIN target: {target_id}")
