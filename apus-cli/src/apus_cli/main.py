import typer
from apus_shared.cdk import boto3_session

from apus_cli.cmd.deploy import DeployCommand
from apus_cli.cmd.destroy import DestroyCommand

app = typer.Typer(help='APUS Command Line Interface')


@app.callback()
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


app.command(name='deploy', help='Deploy APUS modules into AWS cloud.')(DeployCommand)
app.command(name='destroy', help='Destroy APUS modules.')(DestroyCommand)

if __name__ == '__main__':
    app()
