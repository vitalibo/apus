# Channel

A Channel resource defines notification channels used by [BusinessMonitor](business-monitor.md) to send alerts and
notifications. Channels are reusable and can be referenced by multiple monitors.

## Channel Types

APUS supports three types of channels:

| Channel Type | Description                         |
|--------------|-------------------------------------|
| `slack`      | Send alerts via Slack messaging     |
| `email`      | Send alerts via email notifications |
| `cloudwatch` | Send metrics to CloudWatch          |

## Defining a Channel

A Channel resource is defined as other APUS resource in YAML format with structure similar to Kubernetes custom
resources (CRDs)

```yaml
apiVersion: apus/v1
kind: Channel
metadata:
  name: <channel-name>
spec:
  type: <channel-type>
  # ... channel-specific fields
```

## Slack Channel

Slack channels send alert messages to specified Slack channels using a bot token.

### Attributes

- `type` (`enum`, required) — Channel type. Must be `slack`.

- `token` (`string`, required) — Slack bot API token for authentication. Generate via Slack API settings.

- `channels` (`list[string]`, optional) — List of Slack channel names or IDs to send alerts to. Minimum 1, maximum 16.
  These can be overridden.

### Example

```yaml
apiVersion: apus/v1
kind: Channel
metadata:
  name: SlackAlerts
spec:
  type: slack
  token: xoxb-your-token-here
  channels:
    - '#alerts'
    - '#important-notifications'
```

### How to create Slack application

1. Go to [Slack API](https://api.slack.com/apps) and click "Create New App".
2. Choose "From scratch" and provide an app name and select your workspace.
3. In the app settings, go to "OAuth & Permissions" and add the following scopes under "Bot Token Scopes":
    - `channels:read`
    - `chat:write`
4. Install the app to your workspace by clicking "Install App" in the sidebar.
5. Copy the "Bot User OAuth Token" and use it in your Channel configuration.
6. Add the app to the Slack channels you want to send alerts to by going to the channel, clicking "Integrations", and
   adding your app.

## Email Channel

Email channels send alert messages to specified email recipients via SMTP.

### Attributes

- `type` (`enum`, required) — Channel type. Must be `email`.

- `host` (`string`, required) — SMTP server hostname.

- `port` (`integer`, required) — SMTP server port number (0-65535).

- `username` (`string`, required) — SMTP username for authentication.

- `password` (`string`, required) — SMTP password for authentication.

- `recipients` (`list[string]`, optional) — List of email addresses to send alerts to. Minimum 1, maximum 16. These can
  be overridden.

### Example

```yaml
apiVersion: apus/v1
kind: Channel
metadata:
  name: EmailAlerts
spec:
  type: email
  host: smtp.example.com
  port: 587
  username: alerts@example.com
  password: email-password
  recipients:
    - oncall@example.com
    - admin@example.com
```

## CloudWatch Channel

CloudWatch channels send data to AWS CloudWatch metrics.

### Attributes

- `type` (`enum`, required) — Channel type. Must be `cloudwatch`.

- `namespace` (`string`, required) — CloudWatch namespace for the metrics. This can be overridden.

### Example

```yaml
apiVersion: apus/v1
kind: Channel
metadata:
  name: CloudWatchMetrics
spec:
  type: cloudwatch
  namespace: APUS/Monitoring
```
