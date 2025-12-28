from __future__ import annotations

import re
from functools import reduce
from typing import Annotated, Generic, TypeVar, Union

import pydantic
from pydantic import ConfigDict, Discriminator, Field, RootModel, Tag

__all__ = [
    'BaseModel',
    'Metadata',
    'Resource',
    'create_resource',
]

T = TypeVar('T', bound=pydantic.BaseModel)


class BaseModel(pydantic.BaseModel):
    """Base pydantic model for all models."""

    model_config = ConfigDict(
        extra='forbid',
        frozen=True,
        str_min_length=1,
        str_strip_whitespace=True,
    )

    def __str__(self):
        return self.model_dump_json()


_NameStr = _NamespaceStr = Annotated[
    str,
    Field(..., min_length=1, max_length=64, pattern='^[A-Za-z][A-Za-z0-9_-]+$'),
]

_LabelDict = _AnnotationDict = Annotated[
    dict[
        Annotated[str, Field(..., min_length=1, max_length=32, pattern=r'^[A-Za-z][A-Za-z0-9_/-]+$')],
        Annotated[str, Field(..., min_length=0, max_length=256)],
    ],
    Field(..., default_factory=dict, min_length=0, max_length=16),
]


class Metadata(BaseModel):
    """Metadata is used to uniquely identify a resource."""

    name: Annotated[_NameStr, Field(..., pattern='^[A-Za-z][A-Za-z0-9_ -]+$')]
    namespace: Annotated[_NamespaceStr, Field(default='default')]
    labels: _LabelDict
    annotations: _AnnotationDict


class Resource(BaseModel, Generic[T]):
    """Generic model used to represent any APUS resource."""

    api_version: Annotated[str, Field(..., alias='apiVersion', max_length=16, pattern=r'^[a-z][a-z0-9/.]+$')]
    kind: Annotated[str, Field(..., max_length=32, pattern=r'^[A-Z][A-Za-z0-9_]+$')]
    metadata: Metadata
    spec: T


def create_resource() -> type[RootModel[Resource]]:
    """Creates a pydantic model used to represent any APUS resource."""

    from apus_shared.fields import generic  # noqa: PLC0415

    classes = {}
    for cls in BaseModel.__subclasses__():
        if not ('__kind__' in cls.__dict__ and '__api_version__' in cls.__dict__):
            continue

        if not re.match(r'^[A-Z][A-Za-z0-9_]+$', cls.__kind__):
            raise ValueError(f'class {cls.__name__} has invalid kind {cls.__kind__}')
        if not re.match(r'^[a-z][a-z0-9/.]+$', cls.__api_version__):
            raise ValueError(f'class {cls.__name__} has invalid api version {cls.__api_version__}')

        tag = cls.__kind__ + '/' + cls.__api_version__
        if tag in classes:
            raise ValueError(f'tag {tag} is already registered')

        classes[tag] = Annotated[Resource[generic(cls)], Tag(tag)]

    if not classes:
        raise ValueError('no resource classes found')
    if len(classes) == 1:
        return RootModel[classes.popitem()[1]]

    def resource_discriminator(v):
        return v['kind'] + '/' + v['apiVersion']

    return RootModel[
        Annotated[
            reduce(lambda accumulator, resource: Union[accumulator, resource], classes.values()),
            Discriminator(resource_discriminator),
        ]
    ]
