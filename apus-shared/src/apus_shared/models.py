from typing import TypeVar, Annotated, Generic, Type

import pydantic
from pydantic import ConfigDict, Field, RootModel

__all__ = [
    'BaseModel',
    'Metadata',
    'Resource'
]

T = TypeVar('T', bound=pydantic.BaseModel)


class BaseModel(pydantic.BaseModel):
    """Base pydantic model for all models."""

    model_config = ConfigDict(
        extra='forbid',
        frozen=True,
        str_min_length=1,
        str_strip_whitespace=True
    )

    def __str__(self):
        return self.model_dump_json()


_NameStr = _NamespaceStr = Annotated[
    str,
    Field(..., min_length=1, max_length=64, pattern='^[A-Za-z][A-Za-z0-9_-]+$')
]

_LabelDict = _AnnotationDict = Annotated[
    dict[
        Annotated[str, Field(..., min_length=1, max_length=32, pattern=r'^[A-Za-z][A-Za-z0-9_/-]+$')],
        Annotated[str, Field(..., min_length=0, max_length=256)],
    ],
    Field(..., default_factory=dict, min_length=0, max_length=16)
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


def create_resource() -> Type[RootModel[Resource]]:
    pass
