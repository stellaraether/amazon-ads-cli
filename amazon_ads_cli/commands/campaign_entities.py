"""Campaign-scoped entity command helpers."""

import re

import click

from ..cli import extract_error_detail, handle_errors
from .auto_targets import register_auto_targets_commands

_ASIN_RE = re.compile(r"^[Bb][0-9A-Za-z]{9}$")


def _looks_like_asin(text):
    """Return True if text matches a 10-character Amazon ASIN pattern."""
    return bool(_ASIN_RE.match(text)) if text else False


def _extract_asin(expression):
    """Return the ASIN value from a targeting expression."""
    if not expression:
        return "N/A"
    for item in expression:
        if item.get("type") in ("ASIN_SAME_AS", "ASIN_BRAND_SAME_AS"):
            return item.get("value", "N/A")
    return str(expression[0].get("value", "N/A")) if expression else "N/A"


def _is_asin_expression(expression):
    """Return True if expression contains an ASIN_SAME_AS predicate."""
    return any(item.get("type") == "ASIN_SAME_AS" for item in expression or [])


def register_negatives_campaign_commands(campaign_group, ensure_auth_client):
    """Register negative keyword commands scoped to a campaign ID context."""

    @campaign_group.group()
    def negatives():
        """Negative keyword management commands."""
        pass

    @negatives.command("list")
    @click.option("--show-ids", is_flag=True, help="Include negative keyword IDs in output")
    @click.pass_context
    @handle_errors
    def list_negatives(ctx, show_ids):
        """List negative keywords for this campaign."""
        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
        result = client.list_negative_keywords(
            body={
                "campaignIdFilter": {"include": [campaign_id]},
                "stateFilter": {"include": ["ENABLED"]},
            }
        )
        negatives = result.payload.get("negativeKeywords", [])

        if show_ids:
            click.echo(f"\n{'ID':<22} {'Negative Keyword':<35} {'Match':<15}")
            click.echo("-" * 75)
        else:
            click.echo(f"\n{'Negative Keyword':<35} {'Match':<15}")
            click.echo("-" * 55)
        asin_count = 0
        for neg in negatives:
            text = neg["keywordText"][:33]
            match = neg["matchType"]
            if show_ids:
                neg_id = neg.get("keywordId", "N/A")[:20]
                click.echo(f"{neg_id:<22} {text:<35} {match:<15}")
            else:
                click.echo(f"{text:<35} {match:<15}")
            if _looks_like_asin(neg.get("keywordText", "")):
                asin_count += 1
        if asin_count:
            click.echo(
                f"\n⚠️  Warning: {asin_count} item(s) look like ASINs. "
                "ASINs here are keyword negatives, not product negatives. "
                "Use 'amz-ads campaigns <id> negative-asin-targets' to manage competitor ASIN exclusions.",
                err=True,
            )

    @negatives.command("list-all")
    @click.option("--show-ids", is_flag=True, help="Include negative keyword IDs in output")
    @click.pass_context
    @handle_errors
    def list_all_negatives(ctx, show_ids):
        """List all negative keywords across all campaigns."""
        _, client = ensure_auth_client(ctx)
        result = client.list_negative_keywords(body={"stateFilter": {"include": ["ENABLED"]}})
        negatives = result.payload.get("negativeKeywords", [])

        if show_ids:
            click.echo(f"\n{'ID':<22} {'Campaign ID':<20} {'Negative Keyword':<35} {'Match':<15}")
            click.echo("-" * 95)
        else:
            click.echo(f"\n{'Campaign ID':<20} {'Negative Keyword':<35} {'Match':<15}")
            click.echo("-" * 80)
        asin_count = 0
        for neg in negatives:
            camp_id = neg.get("campaignId", "N/A")[:18]
            text = neg["keywordText"][:33]
            match = neg["matchType"]
            if show_ids:
                neg_id = neg.get("keywordId", "N/A")[:20]
                click.echo(f"{neg_id:<22} {camp_id:<20} {text:<35} {match:<15}")
            else:
                click.echo(f"{camp_id:<20} {text:<35} {match:<15}")
            if _looks_like_asin(neg.get("keywordText", "")):
                asin_count += 1
        if asin_count:
            click.echo(
                f"\n⚠️  Warning: {asin_count} item(s) look like ASINs. "
                "ASINs here are keyword negatives, not product negatives. "
                "Use 'amz-ads campaigns <id> negative-asin-targets' to manage competitor ASIN exclusions.",
                err=True,
            )

    @negatives.command("add")
    @click.argument("ad-group-id")
    @click.argument("keyword-text")
    @click.option(
        "--match-type",
        default="NEGATIVE_PHRASE",
        help="Match type: NEGATIVE_EXACT, NEGATIVE_PHRASE",
    )
    @click.pass_context
    @handle_errors
    def add_negative(ctx, ad_group_id, keyword_text, match_type):
        """Add a negative keyword to this campaign."""
        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
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


def register_asin_targets_campaign_commands(campaign_group, ensure_auth_client):
    """Register ASIN target commands scoped to a campaign ID context."""

    @campaign_group.group("asin-targets")
    def asin_targets():
        """ASIN target management commands."""
        pass

    @asin_targets.command("list")
    @click.pass_context
    @handle_errors
    def list_asin_targets(ctx):
        """List ASIN targets for this campaign."""
        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
        result = client.list_product_targets(
            body={
                "campaignIdFilter": {"include": [campaign_id]},
                "stateFilter": {"include": ["ENABLED"]},
            }
        )
        targets = result.payload.get("productTargets", [])
        asin_targets_list = [t for t in targets if _is_asin_expression(t.get("expression", []))]

        click.echo(f"\n{'Target ID':<20} {'Ad Group ID':<20} {'ASIN':<15} {'Bid':<8} {'State'}")
        click.echo("-" * 80)
        for target in asin_targets_list:
            target_id = target.get("targetId", "N/A")[:18]
            ag_id = target.get("adGroupId", "N/A")[:18]
            asin = _extract_asin(target.get("expression", []))[:13]
            bid = f"${target.get('bid', 'N/A')}"
            state = target.get("state", "N/A")
            click.echo(f"{target_id:<20} {ag_id:<20} {asin:<15} {bid:<8} {state}")

    @asin_targets.command("add")
    @click.argument("ad-group-id")
    @click.argument("asin")
    @click.option("--bid", default=1.0, help="Bid amount")
    @click.pass_context
    @handle_errors
    def add_asin_target(ctx, ad_group_id, asin, bid):
        """Add an ASIN target to this campaign."""
        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
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
        if success:
            target_id = success[0].get("targetId")
            click.echo(f"✅ Added ASIN target: {asin} (ID: {target_id}) - ${bid}")

    @asin_targets.command("remove")
    @click.argument("target-id")
    @click.pass_context
    @handle_errors
    def remove_asin_target(ctx, target_id):
        """Remove an ASIN target by ID."""
        _, client = ensure_auth_client(ctx)
        client.delete_product_targets(body={"targetIdFilter": {"include": [target_id]}})
        click.echo(f"✅ Removed ASIN target: {target_id}")


def register_negative_asin_targets_campaign_commands(campaign_group, ensure_auth_client):
    """Register negative ASIN target commands scoped to a campaign ID context."""

    @campaign_group.group("negative-asin-targets")
    def negative_asin_targets():
        """Negative ASIN target management commands."""
        pass

    @negative_asin_targets.command("list")
    @click.pass_context
    @handle_errors
    def list_negative_asin_targets(ctx):
        """List negative ASIN targets for this campaign."""
        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
        result = client.list_negative_product_targets(
            body={
                "campaignIdFilter": {"include": [campaign_id]},
                "stateFilter": {"include": ["ENABLED"]},
            }
        )
        targets = result.payload.get("negativeTargetingClauses", [])

        click.echo(f"\n{'Target ID':<20} {'Ad Group ID':<20} {'ASIN':<15} {'Type':<20} {'State'}")
        click.echo("-" * 95)
        for target in targets:
            target_id = target.get("targetId", "N/A")[:18]
            ag_id = target.get("adGroupId", "N/A")[:18]
            asin = _extract_asin(target.get("expression", []))[:13]
            expr_type = target.get("expressionType", "N/A")[:18]
            state = target.get("state", "N/A")
            click.echo(f"{target_id:<20} {ag_id:<20} {asin:<15} {expr_type:<20} {state}")

    @negative_asin_targets.command("list-all")
    @click.pass_context
    @handle_errors
    def list_all_negative_asin_targets(ctx):
        """List all negative ASIN targets across all campaigns."""
        _, client = ensure_auth_client(ctx)
        result = client.list_negative_product_targets(body={"stateFilter": {"include": ["ENABLED"]}})
        targets = result.payload.get("negativeTargetingClauses", [])

        click.echo(f"\n{'Campaign ID':<20} {'Ad Group ID':<20} {'ASIN':<15} {'Type':<20} {'State'}")
        click.echo("-" * 95)
        for target in targets:
            camp_id = target.get("campaignId", "N/A")[:18]
            ag_id = target.get("adGroupId", "N/A")[:18]
            asin = _extract_asin(target.get("expression", []))[:13]
            expr_type = target.get("expressionType", "N/A")[:18]
            state = target.get("state", "N/A")
            click.echo(f"{camp_id:<20} {ag_id:<20} {asin:<15} {expr_type:<20} {state}")

    @negative_asin_targets.command("add")
    @click.argument("ad-group-id")
    @click.argument("asin")
    @click.pass_context
    @handle_errors
    def add_negative_asin_target(ctx, ad_group_id, asin):
        """Add a negative ASIN target to this campaign."""
        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
        result = client.create_negative_product_targets(
            body={
                "negativeTargetingClauses": [
                    {
                        "campaignId": campaign_id,
                        "adGroupId": ad_group_id,
                        "expression": [{"value": asin, "type": "ASIN_SAME_AS"}],
                        "expressionType": "MANUAL",
                        "state": "ENABLED",
                    }
                ]
            }
        )
        success = result.payload.get("negativeTargetingClauses", {}).get("success", [])
        if success:
            target_id = success[0].get("targetId")
            click.echo(f"✅ Added negative ASIN target: {asin} (ID: {target_id})")

    @negative_asin_targets.command("remove")
    @click.argument("target-id")
    @click.pass_context
    @handle_errors
    def remove_negative_asin_target(ctx, target_id):
        """Remove a negative ASIN target by ID."""
        _, client = ensure_auth_client(ctx)
        client.delete_negative_product_targets(body={"negativeTargetIdFilter": {"include": [target_id]}})
        click.echo(f"✅ Removed negative ASIN target: {target_id}")


def register_keywords_campaign_commands(campaign_group, ensure_auth_client):
    """Register keyword commands scoped to a campaign ID context."""

    @campaign_group.group()
    def keywords():
        """Keyword management commands."""
        pass

    @keywords.command("list")
    @click.pass_context
    @handle_errors
    def list_keywords(ctx):
        """List keywords for this campaign."""
        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
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
    @click.argument("ad-group-id")
    @click.argument("keyword-text")
    @click.option("--match-type", default="EXACT", help="Match type: EXACT, PHRASE, BROAD")
    @click.option("--bid", default=1.0, help="Bid amount")
    @click.pass_context
    @handle_errors
    def add_keyword(ctx, ad_group_id, keyword_text, match_type, bid):
        """Add a keyword to this campaign."""
        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
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
        client.edit_keyword(keyword_id, body={"keywords": [{"keywordId": keyword_id, "bid": amount}]})
        click.echo(f"✅ Keyword {keyword_id} bid updated to ${amount}")


def register_targets_campaign_commands(campaign_group, ensure_auth_client):
    """Register product target commands scoped to a campaign ID context."""

    @campaign_group.group()
    def targets():
        """Product target management commands."""
        pass

    @targets.command("list")
    @click.pass_context
    @handle_errors
    def list_targets(ctx):
        """List product targets for this campaign."""
        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
        result = client.list_product_targets(
            body={
                "campaignIdFilter": {"include": [campaign_id]},
                "stateFilter": {"include": ["ENABLED"]},
            }
        )
        targets_list = result.payload.get("productTargets", [])

        click.echo(f"\n{'Target ID':<20} {'Ad Group ID':<20} {'Expression':<40} {'State'}")
        click.echo("-" * 95)
        for t in targets_list:
            camp_id = t.get("campaignId", "N/A")[:18]
            ag_id = t.get("adGroupId", "N/A")[:18]
            expr = str(t.get("expression", []))[:38]
            state = t.get("state", "N/A")
            click.echo(f"{camp_id:<20} {ag_id:<20} {expr:<40} {state}")

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


def register_adgroups_campaign_commands(campaign_group, ensure_auth_client):
    """Register ad group commands scoped to a campaign ID context."""

    @campaign_group.group()
    def adgroups():
        """Ad group management commands."""
        pass

    @adgroups.command("list")
    @click.pass_context
    @handle_errors
    def list_adgroups(ctx):
        """List ad groups for this campaign."""
        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
        result = client.list_ad_groups(body={"campaignIdFilter": {"include": [campaign_id]}})
        ad_groups = result.payload.get("adGroups", [])

        click.echo(f"\n{'ID':<20} {'Campaign ID':<20} {'Name':<30} {'State'}")
        click.echo("-" * 85)
        for ag in ad_groups:
            ag_id = ag["adGroupId"][:18]
            camp_id = ag["campaignId"][:18]
            name = ag["name"][:28]
            state = ag["state"]
            click.echo(f"{ag_id:<20} {camp_id:<20} {name:<30} {state}")

    @adgroups.command("create")
    @click.option("--name", required=True, help="Ad group name")
    @click.option("--default-bid", required=True, type=float, help="Default bid amount in dollars")
    @click.option(
        "--state",
        default="ENABLED",
        type=click.Choice(["ENABLED", "PAUSED"], case_sensitive=False),
        show_default=True,
        help="Initial ad group state",
    )
    @click.pass_context
    @handle_errors
    def create_adgroup(ctx, name, default_bid, state):
        """Create an ad group in this campaign.

        In an AUTO-targeting campaign, Amazon auto-provisions the four
        auto-targeting clauses at the ad group default bid.
        """
        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
        result = client.create_ad_groups(
            body={
                "adGroups": [
                    {
                        "name": name,
                        "campaignId": campaign_id,
                        "defaultBid": default_bid,
                        "state": state.upper(),
                    }
                ]
            }
        )
        response = result.payload.get("adGroups", {})
        errors = response.get("error", [])
        if errors:
            raise click.ClickException(f"Ad group creation failed: {extract_error_detail(errors[0])}")

        success = response.get("success", [])
        if success:
            ad_group_id = success[0].get("adGroupId", "N/A")
            click.echo(f"✅ Created ad group: {name} (ID: {ad_group_id})")
        else:
            click.echo(f"✅ Ad group created: {name}")


def register_product_ads_campaign_commands(campaign_group, ensure_auth_client):
    """Register product ad commands scoped to a campaign ID context."""

    @campaign_group.group("product-ads")
    def product_ads():
        """Product ad management commands."""
        pass

    @product_ads.command("list")
    @click.pass_context
    @handle_errors
    def list_product_ads(ctx):
        """List product ads for this campaign (excludes archived ads)."""
        _, client = ensure_auth_client(ctx)
        campaign_id = ctx.obj["campaign_id"]
        result = client.list_product_ads(
            body={
                "campaignIdFilter": {"include": [campaign_id]},
                "stateFilter": {"include": ["ENABLED", "PAUSED"]},
            }
        )
        ads = result.payload.get("productAds", [])

        click.echo(f"\n{'Ad ID':<20} {'Ad Group ID':<20} {'SKU':<25} {'ASIN':<15} {'State'}")
        click.echo("-" * 95)
        for ad in ads:
            ad_id = str(ad.get("adId", "N/A"))[:18]
            ag_id = str(ad.get("adGroupId", "N/A"))[:18]
            sku = str(ad.get("sku", "N/A"))[:23]
            asin = str(ad.get("asin", "N/A"))[:13]
            state = ad.get("state", "N/A")
            click.echo(f"{ad_id:<20} {ag_id:<20} {sku:<25} {asin:<15} {state}")

    @product_ads.command("list-all")
    @click.pass_context
    @handle_errors
    def list_all_product_ads(ctx):
        """List all product ads across all campaigns (excludes archived ads)."""
        _, client = ensure_auth_client(ctx)
        result = client.list_product_ads(body={"stateFilter": {"include": ["ENABLED", "PAUSED"]}})
        ads = result.payload.get("productAds", [])

        click.echo(f"\n{'Ad ID':<20} {'Campaign ID':<20} {'Ad Group ID':<20} {'SKU':<25} {'ASIN':<15} {'State'}")
        click.echo("-" * 115)
        for ad in ads:
            ad_id = str(ad.get("adId", "N/A"))[:18]
            camp_id = str(ad.get("campaignId", "N/A"))[:18]
            ag_id = str(ad.get("adGroupId", "N/A"))[:18]
            sku = str(ad.get("sku", "N/A"))[:23]
            asin = str(ad.get("asin", "N/A"))[:13]
            state = ad.get("state", "N/A")
            click.echo(f"{ad_id:<20} {camp_id:<20} {ag_id:<20} {sku:<25} {asin:<15} {state}")


def register_auto_targets_campaign_commands(campaign_group, ensure_auth_client):
    """Register auto-targeting group commands scoped to a campaign ID context."""
    register_auto_targets_commands(campaign_group, ensure_auth_client, "campaign")
