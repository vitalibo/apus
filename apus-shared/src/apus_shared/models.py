from __future__ import annotations

import re
from collections import UserString
from enum import Enum
from functools import reduce
from typing import TYPE_CHECKING, Annotated, Any, Generic, Literal, Optional, TypeVar, Union
from urllib.parse import quote_plus

import pydantic
import sqlalchemy
from pydantic import ConfigDict, Discriminator, Field, RootModel, Tag
from pydantic_core import PydanticCustomError, core_schema
from pyxis.enum import EnumMixin

if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
    from pydantic.json_schema import JsonSchemaValue

__all__ = [
    'BaseModel',
    'Connection',
    'Engine',
    'Metadata',
    'Resource',
    'ScheduleStr',
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


class Engine(str, EnumMixin, Enum):
    """Supported engines."""

    MYSQL = 'mysql'
    POSTGRESQL = 'postgresql'
    SNOWFLAKE = 'snowflake'

    @property
    def driver(self):
        return {
            self.MYSQL: 'mysql+pymysql',
            self.POSTGRESQL: 'postgresql+psycopg2',
            self.SNOWFLAKE: 'snowflake',
        }[self]


class Connection(BaseModel):
    """Connection to a database."""

    __api_version__ = 'apus/v1'
    __kind__ = 'Connection'

    engine: Literal[Engine.MYSQL, Engine.POSTGRESQL]
    host: str
    port: Annotated[int, Field(..., ge=0, le=65535)]
    username: str
    password: str
    database: str
    properties: Annotated[dict[str, str], Field(default_factory=dict)]

    def create_engine(self, **kwargs) -> sqlalchemy.Engine:
        params = {
            'driver': self.engine.driver,
            'host': kwargs.get('host', self.host),
            'port': kwargs.get('port', self.port),
            'username': kwargs.get('username', self.username),
            'password': quote_plus(kwargs.get('password', self.password)),
            'database': kwargs.get('database', self.database),
        }

        connection_str = '{driver}://{username}:{password}@{host}:{port}/{database}'

        properties = self.properties.copy()
        properties.update(kwargs.get('properties', {}))
        if properties:
            params['props'] = '&'.join(f'{key}={quote_plus(value)}' for key, value in properties.items())
            connection_str += '?{props}'

        return sqlalchemy.create_engine(connection_str.format(**params))


class SnowflakeConnection(Connection):
    """Connection to a Snowflake database."""

    engine: Literal[Engine.SNOWFLAKE]
    account: str
    host: Annotated[Optional[str], Field(default=None)]
    port: Annotated[int, Field(default=443, ge=0, le=65535)]
    password: None = None  # deprecated single-factor password sign-in
    private_key: str
    database: Annotated[Optional[str], Field(default=None)]
    schema_name: Annotated[Optional[str], Field(default=None, alias='schema')]
    warehouse: Annotated[Optional[str], Field(default=None)]
    role: Annotated[Optional[str], Field(default=None)]

    def create_engine(self, **kwargs) -> sqlalchemy.Engine:
        from snowflake.sqlalchemy import URL  # noqa: PLC0415

        params = {
            'account': kwargs.get('account', self.account),
            'port': kwargs.get('port', self.port),
            'user': kwargs.get('username', self.username),
        }

        if 'host' in kwargs or self.host:
            params['host'] = kwargs.get('host', self.host)
        if 'database' in kwargs or self.database:
            params['database'] = kwargs.get('database', self.database)
        if 'schema' in kwargs or self.schema_name:
            params['schema'] = kwargs.get('schema', self.schema_name)
        if 'warehouse' in kwargs or self.warehouse:
            params['warehouse'] = kwargs.get('warehouse', self.warehouse)
        if 'role' in kwargs or self.role:
            params['role'] = kwargs.get('role', self.role)

        if self.properties or 'properties' in kwargs:
            properties = self.properties.copy()
            properties.update(kwargs.get('properties', {}))
            params.update(properties)

        return sqlalchemy.create_engine(
            URL(**params),
            connect_args={
                'private_key': kwargs.get('private_key', self.private_key),
            },
        )


class ScheduleStr(UserString):
    """Pydantic model for a schedule string, which can be either interval expressions or cron expressions."""

    @classmethod
    def __get_pydantic_core_schema__(  # noqa: PLW3201
        cls, _source: type[Any], _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        try:
            import croniter  # noqa: PLC0415,F401
        except ImportError as e:
            raise ImportError('schedule validator requires croniter package, run `pip install croniter`') from e

        return core_schema.no_info_after_validator_function(cls._validate, core_schema.str_schema())

    @classmethod
    def __get_pydantic_json_schema__(  # noqa: PLW3201
        cls, _core_schema: core_schema.CoreSchema, _handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        field_schema = _handler(_core_schema)
        field_schema.update(type='string', format='schedule')
        return field_schema

    @classmethod
    def _validate(cls, expr: str) -> str:
        if cls.is_interval(expr) or cls.is_cron(expr):
            return expr

        raise PydanticCustomError(
            'value_error',
            'value is not a valid cron or interval expression',
        )

    @staticmethod
    def is_interval(expr: str) -> bool:
        """Checks if the given expression is a valid interval expression."""

        return re.match(r'(\d+ (minute|hour|day|week|month|year)s?)', expr) is not None

    @staticmethod
    def is_cron(expr: str) -> bool:
        """Checks if the given expression is a valid cron expression."""

        from croniter import croniter  # noqa: PLC0415

        return croniter.is_valid(expr)
