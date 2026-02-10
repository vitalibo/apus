from datetime import datetime
from unittest import mock

import pytest
import pytz
from pyxis.config import Config
from pyxis.resources import load_json, resource
from starlette.testclient import TestClient


@pytest.fixture(scope='module')
def mock_session():
    mock_session = mock.MagicMock()
    with mock.patch('apus_api.routers.data_gateway.deps.get_session') as mock_deps:
        mock_deps.return_value = lambda: mock_session
        yield mock_session


@pytest.fixture(scope='module')
def mock_cognito_idp():
    with (
        mock.patch('apus_api.routers.authentication.boto3.client') as mock_boto3,
        mock.patch('apus_api.routers.authentication.datetime') as mock_datetime,
        mock.patch.dict('os.environ', {'TEST_USER_POOL': 'testUserPool', 'TEST_CLIENT_ID': 'testClientId'}),
    ):

        def side_effect(**kwargs):
            if not (
                kwargs['AuthParameters']['USERNAME'] == 'test_user'
                and kwargs['AuthParameters']['PASSWORD'] == 'test_password'  # noqa: S105 # pragma: allowlist secret
            ):
                raise mock_cognito_idp.exceptions.NotAuthorizedException

        class NotAuthorizedException(Exception):  # noqa: N818
            pass

        class UserNotFoundException(Exception):  # noqa: N818
            pass

        mock_datetime.now.return_value = datetime(2101, 1, 2, 12, 34, 56, tzinfo=pytz.UTC)
        mock_cognito_idp = mock.Mock()
        mock_boto3.return_value = mock_cognito_idp
        mock_cognito_idp.describe_user_pool_client.return_value = {
            'UserPoolClient': {'ClientSecret': 'test_secret'}  # pragma: allowlist secret
        }
        mock_cognito_idp.exceptions.NotAuthorizedException = NotAuthorizedException
        mock_cognito_idp.exceptions.UserNotFoundException = UserNotFoundException
        mock_cognito_idp.initiate_auth.side_effect = side_effect
        yield mock_cognito_idp


@pytest.fixture(scope='module')
def dummy_config():
    config = Config(
        {
            'envs': {
                'LOG_LEVEL': 'DEBUG',
                'CONFIG_FILE': str(resource(__file__, 'data/data_gateway/manifest.json')),
            },
        }
    )

    with mock.patch('pyxis.config.ConfigFactory') as mock_config_factory:
        mock_config_factory.default_application.return_value = config
        yield config


@pytest.fixture(scope='module')
def test_client(mock_session, dummy_config, mock_cognito_idp):  # noqa: ARG001
    from apus_api.main import app  # noqa: PLC0415

    with (
        TestClient(app, raise_server_exceptions=False) as test_client,
        mock.patch('uuid.UUID', return_value='123e4567-e89b-12d3-a456-426614174000'),
    ):
        yield test_client


def test_data_gateway_errors(subtests, test_client, mock_session):
    with subtests.test('not found'):
        response = test_client.get('/unknown/path')

        assert response.status_code == 404
        assert response.json() == load_json(__file__, 'data/data_gateway/errors/not_found.json')

    with subtests.test('method not allowed'):
        response = test_client.get('/users/12345/orders/84f4b963')

        assert response.status_code == 405
        assert response.json() == load_json(__file__, 'data/data_gateway/errors/method_not_allowed.json')

    with subtests.test('internal server error'):
        mock_connection = mock.MagicMock()
        mock_session.connection.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.side_effect = RuntimeError

        response = test_client.request(**make_request())

        assert response.status_code == 500
        assert response.json() == load_json(__file__, 'data/data_gateway/errors/internal_server_error.json')

    with subtests.test('bad request'):
        response = test_client.request(
            **make_request(
                url='/users/foo/orders/bar',
                params={
                    'report_date': '02 Jan 2026',
                    'include_details': 'not_a_boolean',
                    'discount': 'ten_percent',
                },
                json={
                    'age': 15,
                    'tags': 'foo,bar,baz',
                },
            )
        )

        assert response.status_code == 400
        assert response.json() == load_json(__file__, 'data/data_gateway/errors/bad_request.json')

    with subtests.test('bad request: extra forbidden'):
        response = test_client.request(**make_request(params={'foo': 'bar'}))

        assert response.status_code == 400
        assert response.json() == load_json(__file__, 'data/data_gateway/errors/bad_request_extra_forbidden.json')

    with subtests.test('unauthorized'):
        body = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': 'wrong_password',  # pragma: allowlist secret
        }
        response = test_client.request('POST', '/auth', data=body)

        assert response.status_code == 401
        assert response.json() == load_json(__file__, 'data/data_gateway/errors/unauthorized.json')

    with subtests.test('unauthorized: missing token'):
        response = test_client.request('GET', '/users/1234')

        assert response.status_code == 401
        assert response.json() == load_json(__file__, 'data/data_gateway/errors/unauthorized.json')

    with subtests.test('forbidden'):
        response = test_client.request('GET', '/users/1234', headers={'Authorization': 'Bearer invalid_token'})

        assert response.status_code == 403
        assert response.json() == load_json(__file__, 'data/data_gateway/errors/forbidden.json')


def test_data_gateway(test_client, mock_session):
    mock_connection = mock.MagicMock()
    mock_session.connection.return_value.__enter__.return_value = mock_connection
    mock_connection.execute.return_value.fetchall.return_value = [
        mock.Mock(_mapping={'id': 1, 'name': 'Alice', 'timestamp': datetime(2024, 1, 15, 12, 12, 34, tzinfo=pytz.UTC)}),
        mock.Mock(_mapping={'id': 2, 'name': 'Bob', 'timestamp': datetime(2024, 1, 20, 15, 45, 0, tzinfo=pytz.UTC)}),
        mock.Mock(_mapping={'id': 3, 'name': 'Charlie', 'timestamp': None}),
    ]

    response = test_client.request(**make_request())

    assert response.status_code == 200
    assert response.json() == load_json(__file__, 'data/data_gateway/response.json')


def test_data_gateway_secured(subtests, test_client, mock_session):
    mock_connection = mock.MagicMock()
    mock_session.connection.return_value.__enter__.return_value = mock_connection
    mock_connection.execute.return_value.fetchall.return_value = [
        mock.Mock(_mapping={'id': 8, 'name': 'Max', 'created_at': datetime(2026, 1, 7, 23, 4, 56, tzinfo=pytz.UTC)}),
    ]

    with subtests.test('endpoint secured'):
        response = test_client.request('GET', '/users/1234')

        assert response.status_code == 401
        assert response.json() == load_json(__file__, 'data/data_gateway/errors/unauthorized.json')

    with subtests.test('get token'):
        body = {
            'grant_type': 'password',
            'username': 'test_user',
            'password': 'test_password',  # pragma: allowlist secret
        }
        response = test_client.request('POST', '/auth', data=body)

        assert response.status_code == 200
        assert response.json() == {
            'access_token': (
                'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.'
                'eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjQxMzQxMTI3OTZ9.'
                '1EosYL3qFTZC7BE92U5FCE70_8H6QzYPbfB1lGdRyso'  # pragma: allowlist secret
            ),
            'expires_in': 300,
            'token_type': 'Bearer',
        }

    with subtests.test('access secured endpoint'):
        access_token = response.json()['access_token']
        response = test_client.request('GET', '/users/1234', headers={'Authorization': f'Bearer {access_token}'})

        assert response.status_code == 200
        assert response.json() == load_json(__file__, 'data/data_gateway/response_secured.json')


def make_request(**kwargs):
    params = load_json(__file__, 'data/data_gateway/request.json')
    for name in ['params', 'json']:
        if name in kwargs:
            params[name].update(kwargs[name])
            del kwargs[name]
    return {**params, **kwargs}
