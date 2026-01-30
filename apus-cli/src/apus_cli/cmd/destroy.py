import typer
from apus_shared.cdk import boto3_session


class DestroyCommand:
    """Destroy APUS deployed modules."""

    def __init__(
        self,
        stack_name: str = typer.Option(
            ...,
            '--stack-name',
            help='The name of the AWS CloudFormation stack to destroy',
        ),
    ):
        self.stack_name = stack_name
        self.cloudformation = boto3_session.client('cloudformation')
        self.execute()

    def execute(self):
        print('Destroying APUS resources...')
        self.cloudformation.delete_stack(StackName=self.stack_name)
        waiter = self.cloudformation.get_waiter('stack_delete_complete')
        waiter.wait(StackName=self.stack_name)
        print('Successfully destroyed stack')
