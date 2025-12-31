import json
from functools import partial
from typing import Annotated

import forge
from datamodel_code_generator import DataModelType, PythonVersion
from datamodel_code_generator.model import get_data_model_types
from datamodel_code_generator.parser.jsonschema import JsonSchemaParser
from fastapi import Path, Query


def create_model(json_schema: dict) -> type:
    """
    Create a Pydantic model from a JSON schema.

    :param json_schema: JSON schema to create the model from.
    :return: Pydantic V2 model.
    """

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
    )

    namespace = {}
    exec(parser.parse(), namespace)  # pylint: disable=exec-used
    return namespace['Model']


def __arg(cls, obj):
    """
    Create a FastAPI argument from a parameter object.

    :param cls: FastAPI parameter class.
    :param obj: Parameter object.
    """

    return forge.arg(
        f'{cls.__name__.lower()}Parameters_{obj.name}',
        type=Annotated[
            {'string': str, 'integer': int, 'number': float, 'boolean': bool}[obj.type],
            cls(**obj.model_dump(by_alias=True, exclude_none=True, exclude={'type', 'default'})),
        ],
        **obj.model_dump(exclude_none=True, include={'default'}),
    )


query_arg = partial(__arg, Query)
path_arg = partial(__arg, Path)
