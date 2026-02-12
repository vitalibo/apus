# Resource

A Resource is the fundamental building block in APUS. All configuration are defined as resources. Resources
follow a structure inspired by Kubernetes Custom Resource Definitions (CRDs), making them familiar to users with
Kubernetes experience.

## Resource Structure

Every APUS resource has four top-level fields:

```yaml
apiVersion: <api-version>
kind: <resource-type>
metadata:
  name: <resource-name>
  # ... other metadata fields
spec:
# ... resource-specific configuration
```

### Attributes

- `apiVersion` (`string`, required) — API version that defines the schema for this resource.

- `kind` (`string`, required) — Type of resource. Determines which specification fields are available.

- `metadata` (`object`, required) — Resource metadata for identification and organization. See [Metadata](#metadata)
  section.

- `spec` (`object`, required) — [Resource-specific](#spec) configuration. The structure depends on the resource `kind`
  and
  `apiVersion`.

## Metadata

Metadata provides identification and organizational information for a resource.

```yaml
metadata:
  name: MyResource
  namespace: production
  labels:
    environment: prod
    team: platform
  annotations:
    description: My resource description
```

### Attributes

- `name` (`string`, required) — Unique name for the resource within its namespace.

- `namespace` (`string`, optional) — Logical grouping for resources. Default is `default`.

- `labels` (`map[string, string]`, optional) — Key-value pairs for resource classification and selection. Used for
  filtering and organizing resources.

- `annotations` (`map[string, string]`, optional) — Key-value pairs for attaching arbitrary metadata.

## Spec

The `spec` field contains the resource-specific configuration. The structure of `spec` depends on the resource `kind`
and `apiVersion`. Each resource type has its own schema for the `spec` field, which defines the configuration options
available for that resource.

Available resource types in APUS include:

| ApiVersion | Kind           | Description                        | Module | Documentation                                |
|------------|----------------|------------------------------------|--------|----------------------------------------------|
| apus/v1    | Connection     | Database connection configuration  | shared | [Connection](concepts/connection.md)         |
| apus/v1    | DataGateway    | API endpoint backed by SQL queries | api    | [Data Gateway](concepts/data-gateway.md)     |
| apus/v1    | Authentication | OAuth2 authentication endpoint     | api    | [Authentication](concepts/authentication.md) |
