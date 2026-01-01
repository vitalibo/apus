import json
import uuid
from collections import defaultdict
from datetime import date, datetime
from functools import partial
from typing import Annotated

import forge
from datamodel_code_generator import DataModelType, PythonVersion
from datamodel_code_generator.model import get_data_model_types
from datamodel_code_generator.parser.jsonschema import JsonSchemaParser
from fastapi import Path, Query

__all__ = [
    'create_model',
    'path_arg',
    'query_arg',
    'unpack_params',
]


def create_model(json_schema: dict) -> type:
    """Create a Pydantic model from a JSON schema."""

    data_model_types = get_data_model_types(
        DataModelType.PydanticV2BaseModel, target_python_version=PythonVersion.PY_39
    )
    parser = JsonSchemaParser(
        json.dumps(json_schema),
        data_model_type=data_model_types.data_model,
        data_model_root_type=data_model_types.root_model,
        data_model_field_type=data_model_types.field_model,
        data_type_manager_type=data_model_types.data_type_manager,
        dump_resolve_reference_action=data_model_types.dump_resolve_reference_action,
        validation=True,
    )

    namespace = {}
    exec(parser.parse() + '\n\nModel.model_rebuild()', namespace)  # noqa: S102
    return namespace['Model']


def _create_arg(cls, obj):
    """Create a FastAPI argument from a parameter object."""

    dtype = {
        ('string', None): str,
        ('integer', None): int,
        ('number', None): float,
        ('boolean', None): bool,
        ('string', 'date'): date,
        ('string', 'date-time'): datetime,
        ('string', 'uuid'): uuid.UUID,
    }[
        obj.type,
        obj.format if hasattr(obj, 'format') else None,
    ]

    return forge.arg(
        f'{cls.__name__.lower()}Parameters_{obj.name}',
        type=Annotated[
            dtype,
            cls(**obj.model_dump(by_alias=True, exclude_none=True, exclude={'type', 'default'})),
        ],
        **obj.model_dump(exclude_none=True, include={'default'}),
    )


def unpack_params(func):
    """Unpack parameters from FastAPI into a nested dictionary."""

    def wrap(session, _, **kwargs):
        params = defaultdict(dict)
        for key, value in kwargs.items():
            group, *path = key.split('_', 1)
            if path:
                params[group][path[0]] = value
            else:
                params[group] = value

        return func(session=session, params=dict(params))

    return wrap


query_arg = partial(_create_arg, Query)
path_arg = partial(_create_arg, Path)
