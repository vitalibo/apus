import json
from pathlib import Path

import yaml
from pyxis.functions import require_not_none


def resource(root: str, path: str) -> Path:
    """Returns an absolute path to a resource."""

    return Path.joinpath(Path(require_not_none(root, 'root')).parent, require_not_none(path, 'path'))


def resource_as_str(root: str, path: str, encoding: str = 'utf-8') -> str:
    """Returns a resource as a string."""

    return resource(root, path).read_text(encoding)


def resource_as_obj(root: str, path: str):
    """Returns a resource as a yaml object."""

    return yaml.safe_load(resource_as_str(root, path))


def resource_as_objs(root: str, path: str):
    """Returns a resource as a yaml array."""

    return list(yaml.safe_load_all(resource_as_str(root, path)))


def resource_as_json(root: str, path: str, **kwargs):
    """Returns a resource as a json object."""

    return json.loads(resource_as_str(root, path), **kwargs)
