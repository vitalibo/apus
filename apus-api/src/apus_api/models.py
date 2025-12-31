from enum import Enum
from functools import reduce
from typing import Annotated, Any, Literal, Optional, Union

from apus_shared.fields import expand_dict, expand_obj, reference  # noqa: TC002
from apus_shared.models import BaseModel, Connection, create_resource
from pydantic import Field
from pyxis.enum import EnumMixin

Primitive = Union[str, int, float, bool]


class Parameter(BaseModel):
    """An abstract class to represent a parameter."""

    name: Annotated[
        str, Field(..., min_length=1, max_length=64, pattern='^[A-Za-z][A-Za-z0-9_-]+$', serialization_alias='alias')
    ]
    description: Annotated[Optional[str], Field(default=None, min_length=1, max_length=256)]


class PathParameter(Parameter):
    """Represents a path parameter in a HTTP request."""


class QueryParameter(Parameter):
    """Represents a query parameter in a HTTP request."""

    required: Annotated[bool, Field(default=True)]
    default: Annotated[Optional[Primitive], Field(default=None)]
    deprecated: Annotated[bool, Field(default=False)]


class StringFormat(str, EnumMixin, Enum):
    """String format mixin."""

    DATE = 'date'
    DATE_TIME = 'date-time'
    UUID = 'uuid'


class StringMixin(BaseModel):
    """String validation mixin."""

    type: Annotated[Literal['string'], Field('string')]
    min_length: Annotated[Optional[int], Field(default=None, ge=0, alias='minLength')]
    max_length: Annotated[Optional[int], Field(default=None, ge=0, alias='maxLength')]
    pattern: Annotated[Optional[str], Field(default=None, min_length=1, max_length=256)]
    format: Annotated[Optional[StringFormat], Field(default=None)]


class NumberMixin(BaseModel):
    """Number validation mixin."""

    type: Annotated[Literal['number', 'integer'], Field('number')]
    minimum: Annotated[Optional[float], Field(default=None, serialization_alias='ge')]
    maximum: Annotated[Optional[float], Field(default=None, serialization_alias='le')]
    exclusive_minimum: Annotated[
        Optional[bool], Field(default=None, alias='exclusiveMinimum', serialization_alias='gt')
    ]
    exclusive_maximum: Annotated[
        Optional[bool], Field(default=None, alias='exclusiveMaximum', serialization_alias='lt')
    ]
    multiple_of: Annotated[Optional[float], Field(default=None, alias='multipleOf')]


class BooleanMixin(BaseModel):
    """Boolean validation mixin."""

    type: Annotated[Literal['boolean'], Field('boolean')]


def mixin(cls):
    """Make a union of the given class with the mixins."""

    return dict[
        str,
        Annotated[
            reduce(
                lambda accumulator, resource: Union[accumulator, resource],
                [
                    type(f'{cls.__name__}{obj_mixin.__name__}', (cls, obj_mixin), {})
                    for obj_mixin in [StringMixin, NumberMixin, BooleanMixin]
                ],
            ),
            Field(..., discriminator='type'),
        ],
    ]


class Request(BaseModel):
    """A http request definition."""

    path: Annotated[str, ...]
    http_method: Annotated[str, Field(pattern='^(GET|POST)$', alias='httpMethod')]
    path_parameters: Annotated[
        mixin(PathParameter), expand_dict('name'), Field(min_length=0, max_length=16, alias='pathParameters')
    ]
    query_parameters: Annotated[
        mixin(QueryParameter), expand_dict('name'), Field(min_length=0, max_length=16, alias='queryParameters')
    ]
    body: Annotated[Optional[dict[str, Any]], Field(default=None)]


class DataGateway(BaseModel):
    """A Data Gateway resource specification."""

    __api_version__ = 'apus/v1'
    __kind__ = 'DataGateway'

    request: Annotated[Request, ...]
    connection: Annotated[reference(Connection), expand_obj()]
    query_template: Annotated[str, ...]


Resource = create_resource()
