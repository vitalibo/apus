from collections import defaultdict

from apus_shared.models import Resource
from pyxis.config import ConfigFactory

from apus_monitoring.models import Resource as GenericResource


def load_monitors(config) -> list:
    """Loads and parses BusinessMonitor resources from the config."""

    config = config.with_fallback(ConfigFactory.from_file(config.args.config_file)).resolve()

    context = defaultdict(dict)
    objs = []
    for obj in config.resources:
        resource = Resource(**obj)
        context[resource.kind][resource.metadata.name] = obj
        objs.append(obj)

    monitors = []
    for obj in objs:
        resource = GenericResource.model_validate(obj, context=context).root
        if resource.kind == 'BusinessMonitor':
            monitors.append(resource)

    return monitors
