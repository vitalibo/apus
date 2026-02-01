from fastapi import FastAPI
from starlette.testclient import TestClient

from apus_api.routers import HealthRouter


def test_health(subtests):
    app = FastAPI()
    app.include_router(HealthRouter())

    with TestClient(app, raise_server_exceptions=False) as test_client:
        with subtests.test('healthy'):
            response = test_client.get('/health')

            assert response.status_code == 200
            assert response.text == 'up'

        with subtests.test('excluded from schema'):
            response = test_client.get('/openapi.json')

            assert response.status_code == 200
            assert 'health' not in response.text
