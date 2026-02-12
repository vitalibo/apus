# Connection

A Connection resource defines database connection parameters used to establish sessions for query execution.
This resource is reusable and can be referenced by another resource types such as [DataGateway](data-gateway.md)
or [BusinessMonitor](business-monitor.md).

## Supported Engines

Currently, APUS supports the following database engines:

| Engine       | Driver                | Description              |
|--------------|-----------------------|--------------------------|
| `mysql`      | `mysql+pymysql`       | MySQL database           |
| `postgresql` | `postgresql+psycopg2` | PostgreSQL database      |
| `snowflake`  | `snowflake`           | Snowflake data warehouse |

## Defining a Connection

A Connection resource is defined as other APUS resource in YAML format with structure similar to Kubernetes custom
resources (CRDs)

```yaml
apiVersion: apus/v1
kind: Connection
metadata:
  name: <connection-name>
spec:
  engine: <engine-type>
  # ... other connection-specific fields
```

### MySQL / PostgreSQL Connection

MySQL and PostgreSQL connections, use standard relational database connection parameters such as host, port, username,
password, and database name.

#### Attributes

- `engine` (`enum`, required) — Database engine type. Allowed values: `mysql`, `postgresql`.

- `host` (`string`, required) — Database server hostname or IP address.

- `port` (`integer`, required) — Database server port number (0-65535).

- `username` (`string`, required) — Database username for authentication.

- `password` (`string`, required) — Database password for authentication.

- `database` (`string`, required) — Default database name to connect to.

- `properties` (`map[string, string]`, optional) - Additional connection properties as key-value pairs. This can be used
  to specify driver-specific parameters (for example, SSL settings, timeouts, and so on).

#### Example

##### MySQL Connection

```yaml
apiVersion: apus/v1
kind: Connection
metadata:
  name: MySQLConnection
spec:
  engine: mysql
  host: mysql.example.com
  port: 3306
  username: root
  password: secret
  database: mydb
  properties:
    useUnicode: 'true'
    characterEncoding: UTF-8
```

##### PostgreSQL Connection

```yaml
apiVersion: apus/v1
kind: Connection
metadata:
  name: PostgresConnection
spec:
  engine: postgresql
  host: postgres.example.com
  port: 5432
  username: admin
  password: secret
  database: postgres
```

### Snowflake Connection

Snowflake connections use Key-pair authentication instead of password-based authentication.
The connection parameters include Snowflake account identifier, username,
and [PEM-encoded](https://docs.snowflake.com/en/user-guide/key-pair-auth) private key.

#### Attributes

- `engine` (`enum`, required) — Must be `snowflake`.

- `account` (`string`, required) — Snowflake account identifier.

- `host` (`string`, optional) — Snowflake host URL. If not set, it is auto-derived from the account identifier as
  `{account}.snowflakecomputing.com`.

- `port` (`integer`, optional) — Connection port number (0-65535). Default is 443.

- `username` (`string`, required) — Snowflake username for authentication.

- `private_key` (`string`, required) — PEM-encoded private key for authentication.

- `database` (`string`, optional) — Default database name.

- `schema` (`string`, optional) — Default schema name.

- `warehouse` (`string`, optional) — Default warehouse name.

- `role` (`string`, optional) — Default role name.

- `properties` (`map[string, string]`, optional) - Additional connection properties as key-value pairs. This can be used
  to specify driver-specific parameters (for example, SSL settings, timeouts, and so on).

#### Example

```yaml
apiVersion: apus/v1
kind: Connection
metadata:
  name: SnowflakeConnection
spec:
  engine: snowflake
  account: myaccount
  username: admin
  private_key: MIIEvQIBADANBgkqhkiG9w0BAQEFAASC...
  database: sampledb
  schema: public
  warehouse: compute_wh
  role: sysadmin
```

## Security Considerations

- Store sensitive credentials (passwords, private keys) using external secret management
- Use private key authentication for Snowflake instead of deprecated password authentication
- Apply least-privilege principles when configuring database users
