import importlib
import re
from unittest import mock

import pytest

from apus_shared.cdk import boto3_session


def test_session(subtests):
    with mock.patch('boto3.Session') as mock_boto3:
        mock_session = mock.Mock()
        mock_boto3.return_value = mock_session
        importlib.reload(boto3_session)

        with (
            subtests.test('client not initialized'),
            pytest.raises(RuntimeError, match=re.escape('Session has not been initialized yet. Call Session() first.')),
        ):
            boto3_session.client('s3')

        with subtests.test('1st init'):
            actual = boto3_session.Session(profile_name='test', region_name='us-west-2')

            assert actual == mock_session
            mock_boto3.assert_called_once_with(profile_name='test', region_name='us-west-2')

        with subtests.test('2nd init'):
            actual = boto3_session.Session(profile_name='test2', region_name='us-east-1')
            assert actual == mock_session

        with subtests.test('get client'):
            actual = boto3_session.client('s3')

            assert actual == mock_session.client.return_value
            mock_session.client.assert_called_once_with('s3')

        with subtests.test('get resource'):
            actual = boto3_session.resource('dynamodb')

            assert actual == mock_session.resource.return_value
            mock_session.resource.assert_called_once_with('dynamodb')
