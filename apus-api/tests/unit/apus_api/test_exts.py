from fastapi import FastAPI
from pyxis.resources import load_json
from starlette.testclient import TestClient

from apus_api.exts import override_openapi


def test_override_openapi():
    app = FastAPI()
    override_openapi(app)

    @app.get('/{msg}')
    def echo(msg: str):
        return msg

    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get('/openapi.json')

        assert response.status_code == 200
        assert response.json() == load_json(__file__, 'data/openapi.json')
