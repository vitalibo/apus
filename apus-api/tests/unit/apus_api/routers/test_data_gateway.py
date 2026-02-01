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
def test_client(mock_session, dummy_config):  # noqa: ARG001
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

        response = test_client.request(**default_request())

        assert response.status_code == 500
        assert response.json() == load_json(__file__, 'data/data_gateway/errors/internal_server_error.json')

    with subtests.test('bad request'):
        response = test_client.request(
            **default_request(
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
        response = test_client.request(
            **default_request(
                params={
                    'foo': 'bar',
                }
            )
        )

        assert response.status_code == 400
        assert response.json() == load_json(__file__, 'data/data_gateway/errors/bad_request_extra_forbidden.json')


def test_data_gateway(test_client, mock_session):
    mock_connection = mock.MagicMock()
    mock_session.connection.return_value.__enter__.return_value = mock_connection
    mock_connection.execute.return_value.fetchall.return_value = [
        mock.Mock(_mapping={'id': 1, 'name': 'Alice', 'timestamp': datetime(2024, 1, 15, 12, 12, 34, tzinfo=pytz.UTC)}),
        mock.Mock(_mapping={'id': 2, 'name': 'Bob', 'timestamp': datetime(2024, 1, 20, 15, 45, 0, tzinfo=pytz.UTC)}),
        mock.Mock(_mapping={'id': 3, 'name': 'Charlie', 'timestamp': None}),
    ]

    response = test_client.request(**default_request())

    assert response.status_code == 200
    assert response.json() == load_json(__file__, 'data/data_gateway/response.json')


def default_request(**kwargs):
    params = load_json(__file__, 'data/data_gateway/request.json')
    for name in ['params', 'json']:
        if name in kwargs:
            params[name].update(kwargs[name])
            del kwargs[name]
    return {**params, **kwargs}
