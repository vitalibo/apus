# Data Gateway

A Data Gateway resource defines an API endpoint that executes SQL queries against a [database](connection.md) and
returns the results as a structured HTTP response. It connects HTTP request parameters to SQL query templates, enabling
the creation of RESTful APIs backed by database queries. Data Gateways support both `GET` and `POST` methods, allowing
parameters to be passed via URL path, query string, or request body. They also support validation of input parameters
using JSON Schema and can be secured with [authentication](authentication.md) resources.

## Defining a Data Gateway

A Data Gateway resource is defined as other APUS resource in YAML format with structure similar to Kubernetes custom
resources (CRDs)

```yaml
apiVersion: apus/v1
kind: DataGateway
metadata:
  name: <endpoint-name>
spec:
  connection: <connection-object-or-reference>
  request:
  # ... request configuration
  query_template:
  # ... SQL query template
```

### Attributes

- `domain` (`string`, optional) — Custom domain for the endpoint. If not set, the endpoint will be available via the
  load balancer's endpoint URL.

- `authentication` (`string`, optional) — Reference to an [Authentication](authentication.md) resource. If set, the
  endpoint requires authentication, otherwise it is public.

- `connection` (`string`, required) — Object or reference to a [Connection](connection.md) resource that defines the
  database connection parameters.

- `request` (`object`, required) — HTTP request configuration. See [Request](#request) section.

- `response` (`object`, optional) — HTTP response configuration. See [Response](#response) section.

- `query_template` (`string`, required) — SQL query template using Jinja2 syntax. Parameters from path, query, and
  request body are available as template variables.

### Request

The request object defines the HTTP endpoint path, method, and parameters.

#### Attributes

- `path` (`string`, required) — URL path pattern for the endpoint. Supports path parameters in curly braces
  (e.g., `/resource/{id}`).

- `httpMethod` (`enum`, required) — HTTP method. Allowed values: `GET`, `POST`.

- `pathParameters` (`map[str, object]`, optional) — List of [path parameter](#path-parameter) definitions. Each
  parameter must correspond to a placeholder in the path. Key is the parameter name, and value is the parameter
  definition object.

- `queryParameters` (`map[str, object]`, optional) — List of [query parameter](#query-parameter) definitions. Key is the
  parameter name, and value is the parameter definition object.

- `body` (`object`, optional) — JSON Schema defining the request body structure. Only applicable for `POST` requests.

### Path Parameter

Path parameters are extracted from the URL path and are always required.

#### Attributes

- `name` (`string`, conditionally required) — Parameter name. Must match a placeholder in the path. Key name if defined
  in `pathParameters` as a map, or `name` field if defined as a list.

- `description` (`string`, optional) — Parameter description for Swagger API documentation.

- `type` (`enum`, required) — Parameter data type. Allowed values: `string`, `integer`, `number`, `boolean`. Path
  parameters are always treated as strings in the URL, but can be cast to other types
  for [validation](#parameter-validation) and documentation.

### Query Parameter

Query parameters are extracted from the URL query string.

#### Attributes

- `name` (`string`, conditionally required) — Parameter name. Key name if defined in `queryParameters` as a map, or
  `name` field if defined as a list.

- `description` (`string`, optional) — Parameter description for Swagger API documentation.

- `type` (`enum`, required) — Parameter data type. Allowed values: `string`, `integer`, `number`, `boolean`. Query
  parameters are always treated as strings in the URL, but can be cast to other types for [validation](#validation) and
  documentation.

- `required` (`boolean`, optional) — Whether the parameter is required. Default is `true`.

- `default` (`string | integer | number | boolean`, optional) — Default value when the parameter is not provided.

- `deprecated` (`boolean`, optional) — Whether the parameter is deprecated. Default is `false`.

### Response

The response object defines the HTTP response configuration.

#### Attributes

- `statusCode` (`integer`, optional) — HTTP status code for successful responses. Default is `200`. Valid range:
  100-599.

- `envelope` (`object`, optional) — Response envelope configuration. See [Envelope](#envelope) section.

- `schema` (`object`, optional) — JSON Schema defining the response data structure. Used for response formatting and
  Swagger API documentation. If not provided, the response will return raw query results.

### Envelope

The envelope wraps the query results in a standard response structure.

#### Attributes

- `type` (`enum`, optional) — Envelope type. Allowed values: `object` (returns first row), `array` (returns all rows).
  Default is `array`.

- `property` (`string`, optional) — Property name for the data in the response envelope. Default is `data`.

### Query Template

The query template uses Jinja2 syntax to construct SQL queries dynamically. Parameters from the HTTP request are
available as template variables with the following naming convention:

- Path parameters: `pathParameters_<name>` (e.g., `pathParameters_id`)
- Query parameters: `queryParameters_<name>` (e.g., `queryParameters_filter`)
- Body parameters: `body.<field>` (e.g., `body.street_name`)
- Identity parameters (from authentication): `identity.<field>` (e.g., `identity.username`)

Use SQLAlchemy's named parameter syntax (`:parameter_name`) for safe parameter binding to prevent SQL injection.

## Parameter Validation

Data Gateway supports validation of input parameters using JSON Schema. You can define a JSON Schema for path
parameters, query parameters, and request body. If the incoming request does not conform to the schema, the endpoint
will return a `400 Bad Request` response with details about the validation errors.

### String Parameters

String parameters can be further validated using additional constraints such as minimum and maximum length, regex
patterns, and predefined formats.

#### Attributes

- `type` (`string`, required) — Must be set to `string` for string parameters.

- `minLength` (`integer`, optional) — Minimum length of the string. Must be a non-negative integer.

- `maxLength` (`integer`, optional) — Maximum length of the string. Must be a non-negative integer.

- `pattern` (`string`, optional) — Regular expression pattern that the string must match. Must be a valid regex pattern.

- `format` (`string`, optional) — Predefined string formats. Allowed values: `date`, `date-time`, or `uuid`.

### Numeric Parameters

Numeric parameters can be validated using minimum and maximum value constraints.

#### Attributes

- `type` (`string`, required) — Must be set to `integer` or `number` for numeric parameters.

- `minimum` (`number`, optional) — Minimum value for the parameter.

- `maximum` (`number`, optional) — Maximum value for the parameter.

- `exclusiveMinimum` (`number`, optional) — Exclusive minimum value for the parameter.

- `exclusiveMaximum` (`number`, optional) — Exclusive maximum value for the parameter.

- `multipleOf` (`number`, optional) — The parameter value must be a multiple of this number.

### Boolean Parameters

Boolean parameters can be validated to ensure they are either `true` or `false`.

#### Attributes

- `type` (`string`, required) — Must be set to `boolean` for boolean parameters.

## Examples

### GET Endpoint

A simple endpoint that retrieves a resource by ID:

```yaml
apiVersion: apus/v1
kind: DataGateway
metadata:
  name: GetUserById
spec:
  connection: MyConnection
  request:
    path: '/users/{userId}'
    httpMethod: GET
    pathParameters:
      - name: userId
        type: integer
        minimum: 1
        description: Unique identifier of the user
    queryParameters: [ ]
  query_template: |
    SELECT * FROM users
    WHERE id = :pathParameters_userId
```

### GET Endpoint with Query Parameters

An endpoint with optional filtering:

```yaml
apiVersion: apus/v1
kind: DataGateway
metadata:
  name: ListProducts
spec:
  connection: MyConnection
  request:
    path: '/products'
    httpMethod: GET
    pathParameters: [ ]
    queryParameters:
      - name: category
        type: string
        required: false
      - name: limit
        type: integer
        default: 10
  response:
    statusCode: 200
    envelope:
      type: array
      property: products
  query_template: |
    SELECT * FROM products
    {% if queryParameters_category %}
    WHERE category = :queryParameters_category
    {% endif %}
    LIMIT :queryParameters_limit
```

### POST Endpoint with Request Body

An endpoint that accepts a JSON body:

```yaml
apiVersion: apus/v1
kind: DataGateway
metadata:
  name: CreateAddress
spec:
  connection: Connection
  request:
    path: '/addresses'
    httpMethod: POST
    pathParameters: [ ]
    queryParameters: [ ]
    body:
      type: object
      properties:
        street_name:
          type: string
        street_type:
          type: string
          enum:
            - Street
            - Avenue
            - Boulevard
  response:
    statusCode: 201
  query_template: |
    INSERT INTO addresses (street_name, street_type)
    VALUES (:body.street_name, :body.street_type)
```

## Documentation

Data Gateway endpoints are automatically documented in the Swagger UI based on their configuration. The path, HTTP
method, parameters, and response schema are all included in the API documentation. You can enhance the documentation
using metadata labels and annotations as described below.

- `summary` — Short summary displayed in API documentation. Defaults to the resource name.
- `description` — Detailed description for the endpoint.

Annotations with the `tags/` prefix are used to group endpoints in the API documentation.

```yaml
apiVersion: apus/v1
kind: DataGateway
metadata:
  name: GetUser
  labels:
    summary: Get user by ID
    description: Retrieves a user record by their unique identifier
  annotations:
    tags/Users: User management endpoints
spec:
# ...
```

## Errors

If an error occurs during request processing, the endpoint will return an appropriate HTTP status code along with a JSON
response containing error details.

### 400 Bad Request

Returned when the request is malformed, missing required parameters, or fails validation. The response body will contain
details about the validation errors.

```json
{
  "status": 400,
  "message": "Bad Request",
  "errors": {
    "path.user_id": {
      "details": [
        {
          "type": "int_parsing",
          "msg": "Input should be a valid integer, unable to parse string as an integer"
        }
      ],
      "original": "foo"
    }
  },
  "requestId": "123e4567-e89b-12d3-a456-426614174000"
}
```

As shown in the example above, the `errors` field contains a map of parameter names to their respective validation
errors. Each error includes a type, message, and the original value that caused the validation failure. The `requestId`
field can be used for tracing and debugging purposes.

### 401 Unauthorized

Returned when the endpoint requires authentication and the request does not include valid credentials.

```json
{
  "status": 401,
  "message": "Unauthorized",
  "requestId": "123e4567-e89b-12d3-a456-426614174000"
}
```

### 403 Forbidden

Returned when the endpoint requires authentication and the provided credentials do not have sufficient permissions to
access the resource, or token is invalid or expired.

### 404 Not Found

Returned when the requested endpoint does not exist.

### 405 Method Not Allowed

Returned when the HTTP method used in the request is not supported by the endpoint (e.g., using `POST` on an endpoint
that only supports `GET`).

### 500 Internal Server Error

Returned when an unexpected error occurs during request processing. The response body may contain additional details
for debugging purposes. Each response includes a unique `X-Request-Id` header that can be used for tracing and
debugging.
