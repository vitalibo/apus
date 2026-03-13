# Business Monitor

A BusinessMonitor resource defines a business metric that is continuously monitored and tracked over time.
It uses a database connection to execute queries and collects metrics according to a defined schedule.
The collected metrics can be categorized using dimensions and sent to various channels for alerting or visualization.

## Defining a Business Monitor

A BusinessMonitor resource is defined as other APUS resource in YAML format with structure similar to Kubernetes custom
resources (CRDs)

```yaml
apiVersion: apus/v1
kind: BusinessMonitor
metadata:
  name: <monitor-name>
spec:
  schedule: <cron-schedule>
  connection: <reference-to-connection>
  metric: <metric-definition>
  dimensions: <metric-dimensions>
  query_template: <query-template>
  channels: <reference-to-channels>
```

### Attributes

- `schedule` (`string`, required) - A cron expression defining when the monitor runs. Supported formats include AWS cron
  syntax `0 9 * * ? *` (daily at 9 AM) and interval syntax `10 hours` (every 10 hours).

- `connection` (`Connection`, required) - Object or reference to a [Connection](connection.md) resource that
  defines the database connection parameters.

- `metric` (`Metric`, required) - Reference to a [Metric](#metric-and-dimension) definition that specifies the metric to
  be collected.

- `dimensions` (`map[string, Dimension]`, required) - Map of dimension names to [Dimension](#metric-and-dimension)
  definitions for categorizing the metric data.

- `query_template` (`string`, required) - SQL query template using Jinja2 syntax.

- `channels` (`list[Channel]`, required) - List of references to one or more [Channel](channel.md) resources for sending
  alerts and notifications.

### Metric and Dimension

Metrics and dimensions are defined as part of the BusinessMonitor specification. They specify how to extract values from
the database query results.

#### Attributes

- `field` (`string`, required) — The field name in the database result set.

- `name` (`string`, optional) — Display name for the metric or dimension.

- `description` (`string`, optional) — Human-readable description of the metric or dimension.

## Examples

### Basic Monitor

```yaml
apiVersion: apus/v1
kind: BusinessMonitor
metadata:
  name: DailySalesMonitor
spec:
  schedule: '* */6 * * ? *'
  connection:
    reference: MySQLConnection
  metric:
    field: sales
    name: Daily Sales
    description: Total sales amount per day
  dimensions:
    category:
      name: Product Category
      description: Category of the product sold
  query_template: |
    SELECT
      category,
      SUM(amount) as total_sales
    FROM sales
    WHERE date = CURRENT_DATE
  channels:
    - SlackAlerts
    - EmailAlerts:
        recipients:
          - 'vitalibo@apus.io'
```
