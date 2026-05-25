"""Negative keyword management commands."""

import click

from ..cli import handle_errors


def register_negatives_commands(cli_group, ensure_auth_client):
    """Register negative keyword management CLI commands."""

    @cli_group.group()
    def negatives():
        """Negative keyword management commands."""
        pass

    @negatives.command("list")
    @click.argument("campaign-id")
    @click.pass_context
    @handle_errors
    def list_negatives(ctx, campaign_id):
        """List negative keywords for a campaign."""
        _, client = ensure_auth_client(ctx)
        result = client.list_negative_keywords(
            body={
                "campaignIdFilter": {"include": [campaign_id]},
                "stateFilter": {"include": ["ENABLED"]},
            }
        )
        negatives = result.payload.get("negativeKeywords", [])

        click.echo(f"\n{'Negative Keyword':<35} {'Match':<15}")
        click.echo("-" * 55)
        for neg in negatives:
            text = neg["keywordText"][:33]
            match = neg["matchType"]
            click.echo(f"{text:<35} {match:<15}")

    @negatives.command("list-all")
    @click.pass_context
    @handle_errors
    def list_all_negatives(ctx):
        """List all negative keywords across all campaigns."""
        _, client = ensure_auth_client(ctx)
        result = client.list_negative_keywords(body={"stateFilter": {"include": ["ENABLED"]}})
        negatives = result.payload.get("negativeKeywords", [])

        click.echo(f"\n{'Campaign ID':<20} {'Negative Keyword':<35} {'Match':<15}")
        click.echo("-" * 80)
        for neg in negatives:
            camp_id = neg.get("campaignId", "N/A")[:18]
            text = neg["keywordText"][:33]
            match = neg["matchType"]
            click.echo(f"{camp_id:<20} {text:<35} {match:<15}")

    @negatives.command("add")
    @click.argument("campaign-id")
    @click.argument("ad-group-id")
    @click.argument("keyword-text")
    @click.option(
        "--match-type",
        default="NEGATIVE_PHRASE",
        help="Match type: NEGATIVE_EXACT, NEGATIVE_PHRASE",
    )
    @click.pass_context
    @handle_errors
    def add_negative(ctx, campaign_id, ad_group_id, keyword_text, match_type):
        """Add a negative keyword to a campaign."""
        _, client = ensure_auth_client(ctx)
        client.create_negative_keyword(
            body={
                "negativeKeywords": [
                    {
                        "campaignId": campaign_id,
                        "adGroupId": ad_group_id,
                        "keywordText": keyword_text,
                        "matchType": match_type,
                        "state": "ENABLED",
                    }
                ]
            }
        )
        click.echo(f"✅ Added negative keyword: {keyword_text} ({match_type})")

    @negatives.command("remove")
    @click.argument("negative-keyword-id")
    @click.pass_context
    @handle_errors
    def remove_negative(ctx, negative_keyword_id):
        """Remove a negative keyword by ID."""
        _, client = ensure_auth_client(ctx)
        client.delete_negative_keywords(body={"negativeKeywordIdFilter": {"include": [negative_keyword_id]}})
        click.echo(f"✅ Removed negative keyword: {negative_keyword_id}")
