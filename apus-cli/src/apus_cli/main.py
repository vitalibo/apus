from pathlib import Path  # noqa: TC003

import typer
from apus_shared.cdk import boto3_session

from apus_cli.cmd.deploy import DeployCommand
from apus_cli.cmd.destroy import DestroyCommand

cli = typer.Typer(help='APUS Command Line Interface')


@cli.callback()
def configure(
    profile: str = typer.Option(
        None,
        '--profile',
        help='Use a specific AWS profile from your credential file.',
    ),
    region: str = typer.Option(
        None,
        '--region',
        help='The AWS region to use. Overrides config/env settings.',
    ),
):
    options = {}
    if profile:
        options['profile_name'] = profile
    if region:
        options['region_name'] = region

    boto3_session.Session(**options)


@cli.command(help='Deploy APUS modules into AWS cloud.')
def deploy(
    files: list[Path] = typer.Option(  # noqa: B008
        ...,
        '--files',
        '-f',
        exists=True,
        help='List of manifest files to deploy',
    ),
    stack_name: str = typer.Option(
        ...,
        '--stack-name',
        help='The name of the AWS CloudFormation stack you re/deploying to',
    ),
    s3_bucket: str = typer.Option(
        ...,
        '--s3-bucket',
        help='The name of the S3 bucket where this command uploads your artifacts',
    ),
    s3_prefix: str = typer.Option(
        ...,
        '--s3-prefix',
        help="A prefix name that the command adds to the artifacts' name when it uploads them to the S3 bucket",
    ),
    tags: list[str] = typer.Option(  # noqa: B008
        None,
        '--tags',
        help='A list of tags to associate with the stack that is created or updated.',
    ),
):
    command = DeployCommand(stack_name, files, s3_bucket, s3_prefix, tags)
    command.execute()


@cli.command(help='Destroy APUS modules.')
def destroy(
    stack_name: str = typer.Option(
        ...,
        '--stack-name',
        help='The name of the AWS CloudFormation stack to destroy',
    ),
):
    command = DestroyCommand(stack_name)
    command.execute()


if __name__ == '__main__':
    cli()
