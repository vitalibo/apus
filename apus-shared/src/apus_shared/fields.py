import typing
from collections import defaultdict
from functools import reduce
from typing import Annotated, Any, Literal, Optional, Union

import pydantic
from pydantic import BeforeValidator, Discriminator, Field, Tag
from pydantic_core import PydanticCustomError
from pydantic_core.core_schema import ValidationInfo

from apus_shared.models import BaseModel

__all__ = [
    'overridable',
    'generic',
    'reference',
    'optional_fields',
    'expand_obj',
    'expand_list',
    'expand_dict',
    'subclasses'
]

overridable = object()

T = typing.TypeVar('T', bound=BaseModel)


def generic(cls: type[BaseModel]) -> type[BaseModel]:
    """Create a generic class that can represent any of the subclasses for a given class."""

    classes = [cls] + subclasses(cls)
    if len(classes) == 1:
        return cls

    fields = []
    for subclass in classes:
        for field_name, field_info in subclass.model_fields.items():
            if typing.get_origin(field_info.annotation) == Literal \
                    and field_name not in fields:  # pylint: disable=comparison-with-callable
                fields.append(field_name)
    if not fields:
        raise ValueError('at least one field with type typing.Literal is required')

    tag_class = {}
    for subclass in classes:  # pylint: disable=too-many-nested-blocks
        try:
            tag = ()
            for field_name in fields:
                field_info = subclass.model_fields.get(field_name, None)
                if field_info is None:
                    raise ValueError(
                        f'{subclass.__name__}. discriminator field {field_name} is required')
                if typing.get_origin(field_info.annotation) != Literal:  # pylint: disable=comparison-with-callable
                    raise ValueError(
                        f'{subclass.__name__}. discriminator field {field_name} must be of type typing.Literal')
                literal, *_ = typing.get_args(field_info.annotation)
                tag = (*tag, literal)

            tag_class[tag] = subclass
        except ValueError as e:
            if subclass != cls or str(e).endswith('type typing.Literal'):
                raise e

    if len(tag_class) == 1:
        return tag_class.popitem()[1]

    return Annotated[
        reduce(lambda acc, obj: typing.Union[acc, obj], (
            Annotated[cls, Tag('::'.join(tag))] for tag, cls in tag_class.items()
        )),
        Discriminator(lambda obj: '::'.join(
            obj.get(field, 'None') if isinstance(obj, dict) else '' for field in fields
        ))
    ]


def reference(
        cls: type[T], field_name: str = 'id', include_fields: set[str] = None, exclude_fields: set[str] = None
) -> type[T]:
    """Resolve a reference to a resource by its field name."""

    def verify_allowed_extra(value):
        if isinstance(value, dict) and field_name in value:
            validator(**value)
        return value

    def resolve_reference(value, info: ValidationInfo):
        if not (isinstance(value, dict) and field_name in value):
            return value

        resource_name = value[field_name]
        resource_obj = info.context.get(cls.__kind__, {}).get(resource_name)
        if resource_obj is None:
            raise PydanticCustomError('reference.not_found',
                                      f"the reference '{resource_name}' not found")

        return {
            **resource_obj['spec'],
            **{key: value[key] for key in value if key != field_name}
        }

    fields = optional_fields(cls, include_fields, exclude_fields)
    validator = pydantic.create_model(cls.__name__ + 'Val', __base__=BaseModel, **{field_name: (str, ...)}, **fields)
    return Annotated[generic(cls), BeforeValidator(resolve_reference), BeforeValidator(verify_allowed_extra)]


def optional_fields(cls: type[BaseModel], include_fields: set[str] = None, exclude_fields: set[str] = None) -> dict:
    """Create a dictionary of optional fields for a given class."""

    def optional(field):
        annotation = field.annotation
        attributes_set = dict(field._attributes_set)  # pylint: disable=protected-access
        if typing.get_origin(field.annotation) != Optional:
            annotation = Optional[annotation]

        return Annotated[annotation, Field(**attributes_set)]

    fields = {}
    fields_info = defaultdict(set)
    for subclass in [cls] + cls.__subclasses__():
        for field_name, field_info in subclass.model_fields.items():
            if not ((field_name not in (exclude_fields or {})) and
                    ((field_name in (include_fields or {})) or (overridable in field_info.metadata))):
                continue

            infos = fields_info[field_name]
            infos.add(field_info)

            if len(infos) == 1:
                fields[field_name] = (optional(field_info), None)
            else:
                union = Union[tuple(optional(info) for info in infos)]
                fields[field_name] = (Optional[union], None)

    return fields


def expand_obj(field_name: str = 'id') -> BeforeValidator:
    """Allow expanding a string field into an object field."""

    def parse_root(value: Any) -> Any:
        if isinstance(value, dict) and len(value) == 1:
            key, val = next(iter(value.items()))
            if isinstance(val, dict):
                return {**val, field_name: key}
        if isinstance(value, (str, int, float, bool)):
            return {field_name: value}
        return value

    return BeforeValidator(parse_root)


def expand_list(field_name: str = 'id') -> BeforeValidator:
    """Allow expanding a string field into a list field."""

    def parse_dict(key: str, value: Any) -> Any:
        if value is None:
            return {field_name: key}
        if isinstance(value, dict):
            return {**value, field_name: key}
        return value

    def parse_list(value: Any) -> Any:
        if isinstance(value, str):
            return {field_name: value}
        if isinstance(value, dict) and len(value) == 1:
            key, val = next(iter(value.items()))
            if isinstance(val, dict):
                return {**val, field_name: key}
        return value

    def parse_root(value: Any) -> Any:
        if isinstance(value, dict):
            return [parse_dict(key, val) for key, val in value.items()]

        if isinstance(value, list):
            return [parse_list(val) for val in value]

        return value

    return BeforeValidator(parse_root)


def expand_dict(field_name: str = 'id') -> BeforeValidator:
    """Allow expanding a string field into a dict field."""

    def parse_dict(key: str, value: Any) -> Any:
        if value is None:
            return {field_name: key}
        if isinstance(value, dict):
            return {**value, field_name: key}
        return value

    def parse_list(i: int, value: Any) -> Any:
        if isinstance(value, str):
            return value, {field_name: value}
        if isinstance(value, dict) and len(value) == 1:
            key, val = next(iter(value.items()))
            if isinstance(val, dict):
                return key, {**val, field_name: key}
        if field_name in value:
            return value[field_name], value
        # I don't know how to handle this value, so we just return it as-is
        # and hope that the validator will catch it
        return str(i), value

    def parse_root(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: parse_dict(key, val)
                for key, val in value.items()
            }

        if isinstance(value, list):
            out = {}
            for i, val in enumerate(value):
                key, val = parse_list(i, val)
                if key in out:
                    raise PydanticCustomError(
                        'dict.unique_keys',
                        f"the dict has duplicated key '{key}'")
                out[key] = val
            return out

        # wrong type, return the value as-is
        return value

    return BeforeValidator(parse_root)


def subclasses(root_cls):
    """Returns all the subclasses of a given class."""

    def classes(cls):
        yield cls
        for subclass in cls.__subclasses__():
            yield subclass
            yield from subclasses(subclass)

    return list(classes(root_cls))[1:]
