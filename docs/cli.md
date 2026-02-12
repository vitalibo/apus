# Command Line Interface

The APUS CLI (`apus`) is a command-line tool for deploying and managing APUS resources on AWS. It synthesizes
CloudFormation templates from your resource definitions and manages the deployment lifecycle.

## Installation

Install the APUS CLI using pip:

```bash
pip install 'git+https://github.com/vitalibo/apus.git'
```

## Usage

```bash
apus [OPTIONS] COMMAND [ARGS]
```

#### Global Options

- `--profile TEXT` — Use a specific AWS profile from your credential file.

- `--region TEXT` — The AWS region to use. Overrides config/env settings.

- `--help` — Show help message and exit.

### Commands

#### deploy

Deploy APUS resources to AWS. This command reads resource definitions from YAML files, synthesizes a CloudFormation
template, and creates or updates the stack.

```bash
apus deploy [OPTIONS]
```

##### Options

- `-f, --files PATH` (required, multiple) — List of manifest files or directories to deploy. Can be specified multiple
  times. If a directory is provided, all `.yaml` and `.yml` files in the directory (recursively) will be loaded.

- `--stack-name TEXT` (required) — The name of the AWS CloudFormation stack to create or update.

- `--s3-bucket TEXT` (required) — The name of the S3 bucket where the CLI uploads deployment artifacts (CloudFormation
  templates, asset files).

- `--s3-prefix TEXT` (required) — A prefix added to artifact names when uploading to the S3 bucket. Useful for
  organizing multiple deployments.

- `--tags TEXT` (multiple) — Tags to associate with the CloudFormation stack. Can be specified multiple times in
  `Key=Value` format.

##### Example

Deploy resources from multiple files:

```bash
apus --profile production \
     --region us-west-2 \
       deploy \
     --files connections.yaml --files endpoints/ \
     --stack-name my-apus-stack \
     --s3-bucket my-deployment-bucket \
     --s3-prefix my-apus-api/v1.2.34/
```

#### destroy

Destroy a deployed APUS stack and all its resources.

```bash
apus destroy [OPTIONS]
```

##### Options

- `--stack-name TEXT` (required) — The name of the AWS CloudFormation stack to destroy.

##### Example

Destroy a stack:

```bash
apus --profile production destroy --stack-name prod-apus-stack
```

## Resource Files

The CLI loads resources from YAML files. Files can contain single or multiple resources separated by `---`:

```yaml
# api.yaml
apiVersion: apus/v1
kind: Connection
metadata:
  name: UserDatabase
spec:
  engine: postgresql
  host: userdb.example.com
---
apiVersion: apus/v1
kind: DataGateway
metadata:
  name: GetUsers
spec:
  connection: UserDatabase
  request:
    path: /users
    httpMethod: GET
  query_template: |
    SELECT * FROM users
```

## Deployment Workflow

1. **Load Resources** — CLI reads and validates all YAML files
2. **Synthesize Template** — Generates CloudFormation template from resources
3. **Upload Artifacts** — Uploads template and assets to S3
4. **Deploy Stack** — Creates or updates CloudFormation stack
5. **Wait for Completion** — Monitors stack until deployment completes

## Errors

### Validation Errors

If resource files contain invalid definitions, the CLI will fail before deployment with descriptive error messages:

```
Connection/apus/v1.spec.snowflake.account
  Field required [type=missing, input_value={'engine': 'snowflake', '...aGVsbG8='}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.10/v/missing
```

This indicates that the `account` field is required for a Snowflake connection but was not provided in the YAML file.

### Deployment Errors

If CloudFormation deployment fails, check the stack events in the AWS Console for details:
