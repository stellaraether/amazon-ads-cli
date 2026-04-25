# Amazon Ads CLI

Command line interface for Amazon Advertising API v3.

## Installation

```bash
pip install amazon-ads-cli
```

## Setup

Create credentials file at `~/.config/python-ad-api/credentials.yml`:

```yaml
version: '1.0'

default:
  refresh_token: "your-refresh-token"
  client_id: "your-client-id"
  client_secret: "your-client-secret"
  profile_id: "your-profile-id"
```

## Usage

### Campaigns

```bash
# List campaigns
python3 -m amazon_ads_cli.main campaigns list

# Pause campaign
python3 -m amazon_ads_cli.main campaigns pause <campaign-id>

# Enable campaign
python3 -m amazon_ads_cli.main campaigns enable <campaign-id>
```

### Keywords

```bash
# List keywords for a campaign
python3 -m amazon_ads_cli.main keywords list <campaign-id>
```

### Reports

```bash
# Get today's performance
python3 -m amazon_ads_cli.main report today
```

## Development

```bash
# Clone repo
git clone https://github.com/stellaraether/amazon-ads-cli.git
cd amazon-ads-cli

# Install in editable mode
pip install -e .

# Run locally
python3 -m amazon_ads_cli.main campaigns list
```

## Requirements

- Python 3.8+
- `python-amazon-ad-api` library
- Amazon Advertising API credentials

## License

MIT
