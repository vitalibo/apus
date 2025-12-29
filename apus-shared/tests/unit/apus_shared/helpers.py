import json
import random
import string
from pathlib import Path

import pydantic
import yaml
from pyxis.functions import require_not_none

from apus_shared.models import BaseModel


def create_model(base=BaseModel, api_version=None, kind=None, name=None, **kwargs):
    """Create dynamic pydantic model."""

    def random_chars():
        return ''.join(random.choices(string.ascii_letters + string.digits, k=5))  # noqa: S311

    dynamic_name = f'{kind}{api_version}' if kind and api_version else f'Random{random_chars()}'
    model_cls = pydantic.create_model(name or dynamic_name, __base__=base, **kwargs)

    if api_version:
        model_cls.__api_version__ = api_version
    if kind:
        model_cls.__kind__ = kind
    return model_cls


def summarize_errors(e):
    """Extract error types and locations from a validation error."""

    return [(error['type'], error['loc']) for error in e.value.errors()]


def resource(root: str, path: str) -> Path:
    """Returns an absolute path to a resource."""

    return Path.joinpath(Path(require_not_none(root, 'root')).parent, require_not_none(path, 'path'))


def resource_as_str(root: str, path: str, encoding: str = 'utf-8', **kwargs) -> str:
    """Returns a resource as a string."""

    return resource(root, path).read_text(encoding)


def resource_as_obj(root: str, path: str, **kwargs):
    """Returns a resource as a yaml object."""

    return yaml.safe_load(resource_as_str(root, path, **kwargs))


def resource_as_objs(root: str, path: str, **kwargs):
    """Returns a resource as a yaml array."""

    return list(yaml.safe_load_all(resource_as_str(root, path, **kwargs)))


def resource_as_json(root: str, path: str, **kwargs):
    """Returns a resource as a json object."""

    return json.loads(resource_as_str(root, path), **kwargs)
