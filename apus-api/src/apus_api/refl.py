import json
import uuid
from datetime import date, datetime
from functools import partial
from typing import Annotated, Any

import forge
import pydantic
from apus_shared.models import BaseModel
from datamodel_code_generator import DataModelType, PythonVersion
from datamodel_code_generator.model import get_data_model_types
from datamodel_code_generator.parser.jsonschema import JsonSchemaParser
from fastapi import Path, Query

__all__ = [
    'create_model',
    'create_response_model',
    'path_arg',
    'query_arg',
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


query_arg = partial(_create_arg, Query)
path_arg = partial(_create_arg, Path)


def _response_model_translator(response):
    """Create a method to translate database rows into the response model."""

    def transform(rows):
        if response.content_schema is not None:
            rows = [transform_row(response.content_schema, item) for item in rows]
        first_row = rows[0] if rows else {}

        return {response.envelope.property: (first_row if response.envelope.type == 'object' else rows)}

    def transform_row(schema, row, name=None):
        if schema['type'] == 'object':
            return {pname: transform_row(props, row, pname) for pname, props in schema['properties'].items()}
        if schema['type'] == 'array':
            raise NotImplementedError
        return row[schema.get('path', name)]

    return classmethod(lambda cls, rows: cls(**transform(rows)))


def create_response_model(response):
    """Create a Pydantic response model based on the response specification."""

    model = dict[str, Any]
    if response.content_schema is not None:
        model = create_model(response.content_schema)
    if response.envelope.type == 'array':
        model = list[model]

    response_model = pydantic.create_model(
        'Response',
        __base__=BaseModel,
        **{response.envelope.property: (model, ...)},
    )

    response_model.from_rows = _response_model_translator(response)
    return response_model
