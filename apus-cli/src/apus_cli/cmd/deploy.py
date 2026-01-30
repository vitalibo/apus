from pathlib import Path  # noqa: TC003
from urllib.parse import urlparse

import typer
from apus_shared.cdk import boto3_session, synthesizer

from apus_cli.cdk.stack import ApusStack
from apus_cli.loader import load_resources


class DeployCommand:
    """Deploy APUS modules into AWS cloud."""

    def __init__(
        self,
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
        self.stack_name = stack_name
        self.resources = load_resources(*files)
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        self.tags = tags
        self.cloudformation = boto3_session.client('cloudformation')
        self.execute()

    def execute(self):
        template_url = self.synth()
        if not self.stack_exists():
            self.create_stack(template_url)
        else:
            self.update_stack(template_url)

    def stack_exists(self) -> bool:
        try:
            self.cloudformation.describe_stacks(StackName=self.stack_name)
        except self.cloudformation.exceptions.ClientError:
            return False
        return True

    def create_stack(self, template_url):
        print('Waiting for stack create to complete')
        self.cloudformation.create_stack(
            StackName=self.stack_name,
            TemplateURL=template_url,
            Capabilities=['CAPABILITY_IAM'],
        )

        waiter = self.cloudformation.get_waiter('stack_create_complete')
        waiter.wait(StackName=self.stack_name)
        print('Successfully created stack')

    def update_stack(self, template_url):
        print('Waiting for stack update to complete')
        self.cloudformation.update_stack(
            StackName=self.stack_name,
            TemplateURL=template_url,
            Capabilities=['CAPABILITY_IAM'],
        )

        waiter = self.cloudformation.get_waiter('stack_update_complete')
        waiter.wait(StackName=self.stack_name)
        print('Successfully updated stack')

    def synth(self):
        print('Synthesizing CloudFormation template...')

        s3_url = synthesizer.synth(
            ApusStack,
            bucket_prefix=self.s3_prefix,
            file_assets_bucket_name=self.s3_bucket,
            resources=self.resources,
        )

        url_parsed = urlparse(s3_url)
        return f'https://s3.amazonaws.com/{url_parsed.netloc}/{url_parsed.path[1:]}'
