from apus_api.models import Resource
from apus_api.routers.data_gateway import DataGatewayRouter


def register(app, config):
    """Register routers to the FastAPI app based on config."""

    for definition in config.resources:
        resource = Resource(**dict(definition)).root
        if resource.kind == 'DataGateway':
            app.include_router(DataGatewayRouter(resource))
