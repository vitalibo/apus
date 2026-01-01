from datetime import datetime
from unittest import mock

import pytest
import pytz
from apus_shared.resources import resource_as_json, resource_as_obj
from starlette.testclient import TestClient

from apus_api.main import app
from apus_api.models import Resource
from apus_api.routers.data_gateway import DataGatewayRouter


@pytest.fixture(scope='module')
def mock_session():
    mock_session = mock.MagicMock()
    with mock.patch('apus_api.routers.data_gateway.deps.get_session') as mock_deps:
        mock_deps.return_value = lambda: mock_session
        yield mock_session


@pytest.fixture(scope='module')
def test_client(mock_session):  # noqa: ARG001
    resource = Resource(**resource_as_obj(__file__, 'data/data_gateway/manifest.yaml')).root
    app.include_router(DataGatewayRouter(resource))
    with (
        TestClient(app, raise_server_exceptions=False) as test_client,
        mock.patch('uuid.UUID', return_value='123e4567-e89b-12d3-a456-426614174000'),
    ):
        yield test_client


def test_data_gateway_errors(subtests, test_client, mock_session):
    with subtests.test('not found'):
        response = test_client.get('/unknown/path')

        assert response.status_code == 404
        assert response.json() == resource_as_json(__file__, 'data/data_gateway/errors/not_found.json')

    with subtests.test('method not allowed'):
        response = test_client.get('/users/12345/orders/84f4b963')

        assert response.status_code == 405
        assert response.json() == resource_as_json(__file__, 'data/data_gateway/errors/method_not_allowed.json')

    with subtests.test('internal server error'):
        mock_connection = mock.MagicMock()
        mock_session.connection.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.side_effect = RuntimeError

        response = test_client.request(**default_request())

        assert response.status_code == 500
        assert response.json() == resource_as_json(__file__, 'data/data_gateway/errors/internal_server_error.json')

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
        assert response.json() == resource_as_json(__file__, 'data/data_gateway/errors/bad_request.json')


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
    assert response.json() == resource_as_json(__file__, 'data/data_gateway/response.json')


def default_request(**kwargs):
    params = resource_as_json(__file__, 'data/data_gateway/request.json')
    for name in ['params', 'json']:
        if name in kwargs:
            params[name].update(kwargs[name])
            del kwargs[name]
    return {**params, **kwargs}
