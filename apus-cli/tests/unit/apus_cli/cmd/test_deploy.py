import importlib
from pathlib import Path
from unittest import mock

from apus_cli.cdk.stack import ApusStack
from apus_cli.cmd import deploy


def test_deploy_create():
    with (
        mock.patch('apus_shared.cdk.boto3_session.__getattr__') as mock_session,
        mock.patch('apus_cli.loader.load_resources') as mock_load_resources,
        mock.patch('apus_shared.cdk.synthesizer.synth') as mock_synthesizer,
    ):
        mock_cloudformation = mock.Mock()
        mock_session.return_value.return_value = mock_cloudformation
        mock_cloudformation_waiter = mock.Mock()
        mock_cloudformation.get_waiter.return_value = mock_cloudformation_waiter
        mock_cloudformation.exceptions.ClientError = Exception
        mock_cloudformation.describe_stacks.side_effect = Exception('Stack does not exist')
        mock_synthesizer.return_value = 's3://my-s3-bucket-name/apus/v1/template.yaml'
        importlib.reload(deploy)

        deploy.DeployCommand(
            files=[Path('foo.yaml'), Path('bar.yaml')],
            stack_name='test-stack',
            s3_bucket='my-s3-bucket-name',
            s3_prefix='apus/v1/',
            tags=['Environment=Test', 'Project=APUS'],
        )

        mock_load_resources.assert_called_once_with(Path('foo.yaml'), Path('bar.yaml'))
        mock_synthesizer.assert_called_once_with(
            ApusStack,
            bucket_prefix='apus/v1/',
            file_assets_bucket_name='my-s3-bucket-name',
            resources=mock_load_resources.return_value,
        )
        mock_cloudformation.describe_stacks.assert_called_once_with(StackName='test-stack')
        mock_cloudformation.create_stack.assert_called_once_with(
            StackName='test-stack',
            TemplateURL='https://s3.amazonaws.com/my-s3-bucket-name/apus/v1/template.yaml',
            Capabilities=['CAPABILITY_IAM'],
        )
        mock_cloudformation.get_waiter.assert_called_once_with('stack_create_complete')
        mock_cloudformation_waiter.wait.assert_called_once_with(StackName='test-stack')


def test_deploy_update():
    with (
        mock.patch('apus_shared.cdk.boto3_session.__getattr__') as mock_session,
        mock.patch('apus_cli.loader.load_resources') as mock_load_resources,
        mock.patch('apus_shared.cdk.synthesizer.synth') as mock_synthesizer,
    ):
        mock_cloudformation = mock.Mock()
        mock_session.return_value.return_value = mock_cloudformation
        mock_cloudformation_waiter = mock.Mock()
        mock_cloudformation.get_waiter.return_value = mock_cloudformation_waiter
        mock_cloudformation.describe_stacks.return_value = {'Stacks': [{}]}
        mock_synthesizer.return_value = 's3://my-s3-bucket-name/apus/v1/template.yaml'
        importlib.reload(deploy)

        deploy.DeployCommand(
            files=[Path('foo.yaml'), Path('bar.yaml')],
            stack_name='test-stack',
            s3_bucket='my-s3-bucket-name',
            s3_prefix='apus/v1/',
            tags=['Environment=Test', 'Project=APUS'],
        )

        mock_load_resources.assert_called_once_with(Path('foo.yaml'), Path('bar.yaml'))
        mock_synthesizer.assert_called_once_with(
            ApusStack,
            bucket_prefix='apus/v1/',
            file_assets_bucket_name='my-s3-bucket-name',
            resources=mock_load_resources.return_value,
        )
        mock_cloudformation.describe_stacks.assert_called_once_with(StackName='test-stack')
        mock_cloudformation.update_stack.assert_called_once_with(
            StackName='test-stack',
            TemplateURL='https://s3.amazonaws.com/my-s3-bucket-name/apus/v1/template.yaml',
            Capabilities=['CAPABILITY_IAM'],
        )
        mock_cloudformation.get_waiter.assert_called_once_with('stack_update_complete')
        mock_cloudformation_waiter.wait.assert_called_once_with(StackName='test-stack')
