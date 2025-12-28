import random
import string

import pydantic

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


def extract_errors(e):
    """Extract error types and locations from a validation error."""

    return [(error['type'], error['loc']) for error in e.value.errors()]
