import random
import string

import pydantic
import pytest

from apus_shared.models import BaseModel


@pytest.fixture
def helpers():
    return Helpers()


class Helpers:
    """Helper class for testing."""

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
