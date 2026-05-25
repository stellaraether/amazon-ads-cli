"""Main CLI entry point for Amazon Ads CLI."""

from .cli import _ensure_auth_client, cli
from .commands.adgroups import register_adgroups_commands
from .commands.asin_targets import register_asin_targets_commands
from .commands.auth import register_auth_commands
from .commands.campaigns import register_campaigns_commands
from .commands.keywords import register_keywords_commands
from .commands.negatives import register_negatives_commands
from .commands.report import register_report_commands
from .commands.targets import register_targets_commands
from .commands.update import register_update_commands

register_auth_commands(cli)
register_campaigns_commands(cli, _ensure_auth_client)
register_adgroups_commands(cli, _ensure_auth_client)
register_keywords_commands(cli, _ensure_auth_client)
register_negatives_commands(cli, _ensure_auth_client)
register_targets_commands(cli, _ensure_auth_client)
register_asin_targets_commands(cli, _ensure_auth_client)
register_report_commands(cli, _ensure_auth_client)
register_update_commands(cli)
