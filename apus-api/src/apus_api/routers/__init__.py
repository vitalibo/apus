from pyxis.config import ConfigFactory

from apus_api.models import Resource
from apus_api.routers.data_gateway import DataGatewayRouter
from apus_api.routers.health import HealthRouter


def register(app, config):
    """Register routers to the FastAPI app based on config."""

    config = config.with_fallback(ConfigFactory.from_file(config.envs.CONFIG_FILE)).resolve()

    for definition in config.resources:
        resource = Resource(**dict(definition)).root
        if resource.kind == 'DataGateway':
            app.include_router(DataGatewayRouter(resource))

    app.include_router(HealthRouter())
