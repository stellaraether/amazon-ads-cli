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
amz-ads campaigns list

# Pause campaign
amz-ads campaigns pause <campaign-id>

# Enable campaign
amz-ads campaigns enable <campaign-id>
```

### Keywords

```bash
# List keywords for a campaign
amz-ads keywords list <campaign-id>
```

### Reports

```bash
# Get today's performance
amz-ads report today
```

## License

MIT
