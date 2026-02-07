from collections import defaultdict

from apus_shared.models import Resource
from pyxis.config import ConfigFactory

from apus_api.models import Resource as GenericResource
from apus_api.routers.authentication import AuthenticationRouter
from apus_api.routers.data_gateway import DataGatewayRouter
from apus_api.routers.health import HealthRouter


def register(app, config):
    """Register routers to the FastAPI app based on config."""

    config = config.with_fallback(ConfigFactory.from_file(config.envs.CONFIG_FILE)).resolve()

    context = defaultdict(dict)
    objs = []
    for obj in config.resources:
        resource = Resource(**obj)
        context[resource.kind][resource.metadata.name] = obj
        objs.append(obj)

    for obj in objs:
        resource = GenericResource.model_validate(obj, context=context).root
        if resource.kind == 'DataGateway':
            app.include_router(DataGatewayRouter(resource))
        if resource.kind == 'Authentication':
            app.include_router(AuthenticationRouter(resource))

    app.include_router(HealthRouter())
