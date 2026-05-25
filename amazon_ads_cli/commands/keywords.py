"""Keyword management commands."""

import click

from ..cli import handle_errors


def register_keywords_commands(cli_group, ensure_auth_client):
    """Register keyword management CLI commands."""

    @cli_group.group()
    def keywords():
        """Keyword management commands."""
        pass

    @keywords.command("list")
    @click.argument("campaign-id")
    @click.pass_context
    @handle_errors
    def list_keywords(ctx, campaign_id):
        """List keywords for a campaign."""
        _, client = ensure_auth_client(ctx)
        result = client.list_keywords(body={})
        keywords = [k for k in result.payload.get("keywords", []) if k.get("campaignId") == campaign_id]

        click.echo(f"\n{'Keyword':<35} {'Match':<10} {'Bid':<8} {'State'}")
        click.echo("-" * 70)
        for kw in keywords:
            text = kw["keywordText"][:33]
            match = kw["matchType"]
            bid = f"${kw['bid']}"
            state = kw["state"]
            click.echo(f"{text:<35} {match:<10} {bid:<8} {state}")

    @keywords.command("list-all")
    @click.pass_context
    @handle_errors
    def list_all_keywords(ctx):
        """List all keywords across all campaigns."""
        _, client = ensure_auth_client(ctx)
        result = client.list_keywords(body={})
        keywords = result.payload.get("keywords", [])

        click.echo(f"\n{'Campaign ID':<20} {'Keyword':<35} {'Match':<10} {'Bid':<8} {'State'}")
        click.echo("-" * 90)
        for kw in keywords:
            camp_id = kw.get("campaignId", "N/A")[:18]
            text = kw["keywordText"][:33]
            match = kw["matchType"]
            bid = f"${kw['bid']}"
            state = kw["state"]
            click.echo(f"{camp_id:<20} {text:<35} {match:<10} {bid:<8} {state}")

    @keywords.command("add")
    @click.argument("campaign-id")
    @click.argument("ad-group-id")
    @click.argument("keyword-text")
    @click.option("--match-type", default="EXACT", help="Match type: EXACT, PHRASE, BROAD")
    @click.option("--bid", default=1.0, help="Bid amount")
    @click.pass_context
    @handle_errors
    def add_keyword(ctx, campaign_id, ad_group_id, keyword_text, match_type, bid):
        """Add a keyword to a campaign."""
        _, client = ensure_auth_client(ctx)
        client.create_keyword(
            body={
                "keywords": [
                    {
                        "campaignId": campaign_id,
                        "adGroupId": ad_group_id,
                        "keywordText": keyword_text,
                        "matchType": match_type,
                        "bid": bid,
                        "state": "ENABLED",
                    }
                ]
            }
        )
        click.echo(f"✅ Added keyword: {keyword_text} ({match_type}) - ${bid}")

    @keywords.command("bid")
    @click.argument("keyword-id")
    @click.argument("amount", type=float)
    @click.pass_context
    @handle_errors
    def set_bid(ctx, keyword_id, amount):
        """Update keyword bid."""
        _, client = ensure_auth_client(ctx)
        client.edit_keyword(
            keyword_id,
            body={"keywords": [{"keywordId": keyword_id, "bid": amount}]},
        )
        click.echo(f"✅ Keyword {keyword_id} bid updated to ${amount}")
