import json
import random
import string
from pathlib import Path

import pydantic
import pytest
import yaml
from pyxis.functions import require_not_none

from apus_shared.models import BaseModel


@pytest.fixture
def helpers():
    return Helpers()


class Helpers:
    """Helper class for testing."""

    @staticmethod
    def resource(root: str, path: str) -> Path:
        return Path.joinpath(Path(require_not_none(root, 'root')).parent, require_not_none(path, 'path'))

    @staticmethod
    def resource_as_str(root: str, path: str, encoding: str = 'utf-8', **kwargs) -> str:
        return Helpers.resource(root, path).read_text(encoding)

    @staticmethod
    def resource_as_obj(root: str, path: str, **kwargs):
        return yaml.safe_load(Helpers.resource_as_str(root, path, **kwargs))

    @staticmethod
    def resource_as_objs(root: str, path: str, **kwargs):
        return list(yaml.safe_load_all(Helpers.resource_as_str(root, path, **kwargs)))

    @staticmethod
    def resource_as_json(root: str, path: str, **kwargs):
        return json.loads(Helpers.resource_as_str(root, path), **kwargs)

    @staticmethod
    def simplified_errors(e):
        return [(error['type'], error['loc']) for error in e.value.errors()]

    @staticmethod
    def random_chars(k=5):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=k))  # noqa: S311

    @staticmethod
    def create_model(base=BaseModel, api_version=None, kind=None, name=None, **kwargs):
        dynamic_name = f'{kind}{api_version}' if kind and api_version else f'Random{Helpers.random_chars()}'
        model_cls = pydantic.create_model(name or dynamic_name, __base__=base, **kwargs)

        if api_version:
            model_cls.__api_version__ = api_version
        if kind:
            model_cls.__kind__ = kind
        return model_cls
