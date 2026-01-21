from collections import defaultdict

import apus_api.models  # noqa: F401
import yaml
from apus_shared.models import Resource, create_resource


def load_resources(*paths):
    """Loads and parses APUS resources from YAML files located at the given paths."""

    context = defaultdict(dict)
    objs = []
    for file in [
        p
        for path in paths
        for p in (path.rglob('*') if path.is_dir() else [path])
        if p.is_file() and p.suffix.lower() in {'.yaml', '.yml'}
    ]:
        for obj in yaml.safe_load_all(file.open()):
            resource = Resource(**obj)
            context[resource.kind][resource.metadata.name] = obj
            objs.append(obj)

    generic_resource = create_resource()
    resources = []
    for obj in objs:
        resource = generic_resource.model_validate(obj, context=context)
        resources.append(resource.root)

    return {'resources': objs}
