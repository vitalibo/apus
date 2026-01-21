from apus_shared.cdk import boto3_session

from apus_cli.cmd import Command


class DestroyCommand(Command):
    """Destroy APUS deployed modules."""

    def __init__(
        self,
        stack_name: str,
    ):
        self.stack_name = stack_name
        self.cloudformation = boto3_session.client('cloudformation')

    def execute(self):
        print('Destroying APUS resources...')  # noqa: T201
        self.cloudformation.delete_stack(StackName=self.stack_name)
        waiter = self.cloudformation.get_waiter('stack_delete_complete')
        waiter.wait(StackName=self.stack_name)
        print('Successfully destroyed stack')  # noqa: T201
