import importlib
from unittest import mock

from apus_cli.cmd import destroy


def test_destroy():
    with mock.patch('apus_shared.cdk.boto3_session.__getattr__') as mock_session:
        mock_cloudformation = mock.Mock()
        mock_session.return_value.return_value = mock_cloudformation
        mock_cloudformation_waiter = mock.Mock()
        mock_cloudformation.get_waiter.return_value = mock_cloudformation_waiter
        importlib.reload(destroy)

        destroy.DestroyCommand(stack_name='test-stack')

        mock_cloudformation.delete_stack.assert_called_once_with(StackName='test-stack')
        mock_cloudformation.get_waiter.assert_called_once_with('stack_delete_complete')
        mock_cloudformation_waiter.wait.assert_called_once_with(StackName='test-stack')
