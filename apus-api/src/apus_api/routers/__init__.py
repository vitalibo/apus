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

    resources = []
    for obj in objs:
        resource = GenericResource.model_validate(obj, context=context).root
        resources.append((resource.kind, resource))

    identities = {}
    for kind, resource in resources:
        if kind == 'Authentication':
            auth_route = AuthenticationRouter(resource)
            identities[resource.metadata.name] = auth_route.identity()
            app.include_router(auth_route)

    for kind, resource in resources:
        if kind == 'DataGateway':
            route = DataGatewayRouter(resource, identity=identities.get(resource.spec.authentication))
            app.include_router(route)

    app.include_router(HealthRouter())
