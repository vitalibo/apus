from pathlib import Path  # noqa: TC003

import boto3
import typer

cli = typer.Typer(help='APUS Command Line Interface')


@cli.callback()
def configure(
        ctx: typer.Context,
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

    ctx.obj = {'session': boto3.Session(**options)}


@cli.command(help='Deploy APUS modules into AWS cloud.')
def deploy(
        ctx: typer.Context,
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
        tags: list[str] = typer.Option(  # noqa: B008
            None,
            '--tags',
            help='A list of tags to associate with the stack that is created or updated.',
        ),
):
    from apus_cli.cmd.deploy import DeployCommand  # noqa: PLC0415

    command = DeployCommand(ctx.obj['session'], stack_name, files, tags)
    command.execute()


@cli.command(help='Destroy APUS modules.')
def destroy(
        ctx: typer.Context,
        stack_name: str = typer.Option(
            ...,
            '--stack-name',
            help='The name of the AWS CloudFormation stack to destroy',
        ),
):
    from apus_cli.cmd.destroy import DestroyCommand  # noqa: PLC0415

    command = DestroyCommand(ctx.obj['session'], stack_name)
    command.execute()


if __name__ == '__main__':
    cli()
