# Authentication

An Authentication resource defines an OAuth2 token endpoint backed
by [AWS Cognito User Pools](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools.html).
It provides user authentication for [Data Gateway](data-gateway.md) endpoints, enabling secure access to database
queries. When a Data Gateway references an Authentication resource, it requires valid credentials to access the
endpoint.

## How It Works

1. Client sends credentials (username/password) to the authentication endpoint
2. APUS API validates credentials against the configured Cognito User Pool
3. On success, APUS API returns a JWT access token
4. Client includes the token in subsequent requests to protected Data Gateway endpoints
5. Data Gateway validates the token and extracts user identity for query execution

## Defining an Authentication

An Authentication resource is defined as other APUS resource in YAML format with structure similar to Kubernetes custom
resources (CRDs)

```yaml
apiVersion: apus/v1
kind: Authentication
metadata:
  name: <authentication-name>
spec:
  path: <token-endpoint-path>
  expiresIn: <token-expiration-seconds>
```

### Attributes

- `domain` (`string`, optional) — Custom domain for the authentication endpoint. If not set, the endpoint will be
  available via the load balancer's endpoint URL. Must match the domain of Data Gateway endpoints that reference this
  authentication.

- `path` (`string`, required) — URL path for the OAuth2 token endpoint (e.g., `/auth/token`). This is where clients
  send credentials to obtain access tokens.

- `expiresIn` (`integer`, required) — Token expiration time in seconds. Minimum value is 60 seconds.

- `userPool` (`string`, optional) — External Cognito User Pool ID. If not set, APUS automatically creates and manages
  a new User Pool during deployment.

- `clientId` (`string`, optional) — External Cognito User Pool Client ID. Required when `userPool` is specified.

### Example

#### Managed User Pool

When `userPool` and `clientId` are not specified, APUS automatically creates a Cognito User Pool with the following
configuration:

- Admin-only user creation (users cannot self-register)
- Password authentication flow enabled
- Client secret generated automatically

```yaml
apiVersion: apus/v1
kind: Authentication
metadata:
  name: MyAuth
spec:
  path: /auth/token
  expiresIn: 3600
```

#### External User Pool

To use an existing Cognito User Pool, specify both `userPool` and `clientId`:

```yaml
apiVersion: apus/v1
kind: Authentication
metadata:
  name: MyAuth
spec:
  path: /auth/token
  expiresIn: 3600
  userPool: us-east-1_aBcDeFgHi
  clientId: 1a2b3c4d5e6f7g8h9i0j
```

The external User Pool must have:

- `ALLOW_USER_PASSWORD_AUTH` enabled in the app client
- A client secret configured

## User Management

You can manage users in the Cognito User Pool using the AWS Console or AWS CLI. For example, to create a user via AWS
CLI:

```bash
aws cognito-idp admin-create-user \
    --user-pool-id us-east-1_aBcDeFgHi \
    --username johndoe \
    --temporary-password TempPass123!
```

Next, set a permanent password for the user:

```bash
aws cognito-idp admin-set-user-password \
    --user-pool-id us-east-1_aBcDeFgHi \
    --username johndoe \
    --password NewPass456! \
    --permanent
```

## OAuth2 Authentication Flow

The authentication endpoint implements the OAuth2 Resource Owner Password Credentials flow.

### Request

```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

grant_type=password&username=<username>&password=<password>
```

### Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

Access token is a JWT that includes the authenticated user's identity in the `sub` claim. The token must be included in
the `Authorization` header when accessing protected Data Gateway endpoints:

```http
GET /profile
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

After the token expires, the client must re-authenticate to obtain a new token.

## Errors

### 401 Unauthorized

Returned when the provided credentials are invalid or the user does not exist.

```json
{
  "status": 401,
  "message": "Unauthorized",
  "requestId": "123e4567-e89b-12d3-a456-426614174000"
}
```

## Documentation

Authentication endpoints are automatically documented in the Swagger UI. You can enhance the documentation using
metadata labels and annotations.

- `summary` — Short summary displayed in API documentation. Defaults to the resource name.
- `description` — Detailed description for the endpoint.

Annotations with the `tags/` prefix are used to group endpoints in the API documentation.

```yaml
apiVersion: apus/v1
kind: Authentication
metadata:
  name: ApiAuth
  labels:
    summary: Obtain access token
    description: Authenticates user credentials and returns a JWT access token
  annotations:
    tags/Authentication: Authentication endpoints
spec:
  path: /auth/token
  expiresIn: 3600
```

## Security Considerations

- Use HTTPS in production to protect credentials in transit
- Consider using short-lived tokens (e.g., 15-60 minutes) for sensitive operations
