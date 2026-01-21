from urllib.parse import urlparse

from apus_shared.cdk import boto3_session, synthesizer

from apus_cli.cmd import Command


class DeployCommand(Command):
    """Deploy APUS modules into AWS cloud."""

    def __init__(self, stack_name, resources, s3_bucket, s3_prefix, tags):
        self.stack_name = stack_name
        self.resources = resources
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        self.tags = tags
        self.cloudformation = boto3_session.client('cloudformation')

    def execute(self):
        print('Deploying APUS resources...')  # noqa: T201
        template_url = self.synth()
        if not self._stack_exists():
            self._create_stack(template_url)
        else:
            self._update_stack(template_url)

    def _stack_exists(self) -> bool:
        try:
            self.cloudformation.describe_stacks(StackName=self.stack_name)
        except self.cloudformation.exceptions.ClientError:
            return False
        return True

    def _create_stack(self, template_url):
        print('Waiting for stack create to complete')  # noqa: T201
        self.cloudformation.create_stack(
            StackName=self.stack_name,
            TemplateURL=template_url,
            Capabilities=['CAPABILITY_IAM'],
        )

        waiter = self.cloudformation.get_waiter('stack_create_complete')
        waiter.wait(StackName=self.stack_name)
        print('Successfully created stack')  # noqa: T201

    def _update_stack(self, template_url):
        print('Waiting for stack update to complete')  # noqa: T201
        self.cloudformation.update_stack(
            StackName=self.stack_name,
            TemplateURL=template_url,
            Capabilities=['CAPABILITY_IAM'],
        )

        waiter = self.cloudformation.get_waiter('stack_update_complete')
        waiter.wait(StackName=self.stack_name)
        print('Successfully updated stack')  # noqa: T201

    def synth(self):
        print('Synthesizing CloudFormation template...')  # noqa: T201
        from apus_api.cdk.stack import ApusApiStack  # noqa: PLC0415

        s3_url = synthesizer.synth(
            ApusApiStack,
            bucket_prefix=self.s3_prefix,
            file_assets_bucket_name=self.s3_bucket,
            domain_name='apus-api.vitalibo.click',
            config=self.resources,
        )

        url_parsed = urlparse(s3_url)
        return f'https://s3.amazonaws.com/{url_parsed.netloc}/{url_parsed.path[1:]}'
