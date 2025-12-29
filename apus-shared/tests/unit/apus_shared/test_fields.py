from typing import Annotated, Literal, Optional

import pydantic
import pytest
from pydantic import ValidationError

from apus_shared.fields import expand_dict, expand_list, expand_obj, generic, optional_fields, overridable, reference
from apus_shared.models import BaseModel


def test_generic(subtests, helpers):
    cls = helpers.create_model(one=(str, ...))
    root_cls = helpers.create_model(model=(generic(cls), ...))

    with subtests.test('create instance'):
        actual = root_cls(model={'one': 'two'})
        assert isinstance(actual.model, cls)
        assert actual.model.one == 'two'

    with subtests.test('validation error: invalid string'):
        with pytest.raises(ValidationError) as e:
            root_cls(model={'one': 2})
        assert helpers.simplified_errors(e) == [('string_type', ('model', 'one'))]


def test_generic_subclass(subtests, helpers):
    cls = helpers.create_model()
    sub_a = helpers.create_model(cls, one=(Literal['a'], 'a'))
    sub_b = helpers.create_model(cls, one=(Literal['b'], 'b'), two=(str, ...))
    sub_c = helpers.create_model(cls, one=(Literal['c'], 'c'), two=(int, ...))
    root_cls = helpers.create_model(model=(generic(cls), ...))

    with subtests.test('create sub_a instance'):
        actual = root_cls(model={'one': 'a'})
        assert isinstance(actual.model, sub_a)
        assert actual.model.one == 'a'

    with subtests.test('create sub_b instance'):
        actual = root_cls(model={'one': 'b', 'two': '2'})
        assert isinstance(actual.model, sub_b)
        assert actual.model.one == 'b'
        assert actual.model.two == '2'

    with subtests.test('create sub_c instance'):
        actual = root_cls(model={'one': 'c', 'two': 3})
        assert isinstance(actual.model, sub_c)
        assert actual.model.one == 'c'
        assert actual.model.two == 3

    with subtests.test('validation error: no discriminator tag'):
        with pytest.raises(ValidationError) as e:
            root_cls(model={})
        assert helpers.simplified_errors(e) == [('union_tag_invalid', ('model',))]

    with subtests.test('validation error: unknown discriminator tag'):
        with pytest.raises(ValidationError) as e:
            root_cls(model={'one': 'd'})
        assert helpers.simplified_errors(e) == [('union_tag_invalid', ('model',))]

    with subtests.test('validation error: extra fields forbidden'):
        with pytest.raises(ValidationError) as e:
            root_cls(model={'one': 'a', 'two': 2})
        assert helpers.simplified_errors(e) == [('extra_forbidden', ('model', 'a', 'two'))]

    with subtests.test('validation error: missing required field'):
        with pytest.raises(ValidationError) as e:
            root_cls(model={'one': 'b'})
        assert helpers.simplified_errors(e) == [('missing', ('model', 'b', 'two'))]

    with subtests.test('validation error: invalid string'):
        with pytest.raises(ValidationError) as e:
            root_cls(model={'one': 'b', 'two': 2})
        assert helpers.simplified_errors(e) == [('string_type', ('model', 'b', 'two'))]


def test_generic_subclass_inheritance(subtests, helpers):
    cls = helpers.create_model(one=(Literal['none'], 'none'))
    sub_a = helpers.create_model(cls, one=(Literal['a'], 'a'))
    sub_b = helpers.create_model(cls, one=(Literal['b'], 'b'), two=(str, ...))
    sub_b_sub_c = helpers.create_model(sub_b, one=(Literal['c'], 'c'), three=(int, ...))
    root_cls = helpers.create_model(model=(generic(cls), ...))

    with subtests.test('create instances'):
        actual = root_cls(model={'one': 'none'})
        assert isinstance(actual.model, cls)
        assert actual.model.one == 'none'

    with subtests.test('create sub_a instance'):
        actual = root_cls(model={'one': 'a'})
        assert isinstance(actual.model, sub_a)
        assert actual.model.one == 'a'

    with subtests.test('create sub_a instance'):
        actual = root_cls(model={'one': 'b', 'two': '123'})
        assert isinstance(actual.model, sub_b)
        assert actual.model.one == 'b'
        assert actual.model.two == '123'

    with subtests.test('create sub_b_sub_c instance'):
        actual = root_cls(model={'one': 'c', 'two': '123', 'three': 123})
        assert isinstance(actual.model, sub_b_sub_c)
        assert actual.model.one == 'c'
        assert actual.model.two == '123'
        assert actual.model.three == 123

    with subtests.test("validation error: missing required field 'three'"):
        with pytest.raises(ValidationError) as e:
            root_cls(model={'one': 'c', 'two': '123'})
        assert helpers.simplified_errors(e) == [('missing', ('model', 'c', 'three'))]

    with subtests.test("validation error: missing required field 'two'"):
        with pytest.raises(ValidationError) as e:
            root_cls(model={'one': 'c', 'three': 123})
        assert helpers.simplified_errors(e) == [('missing', ('model', 'c', 'two'))]


def test_generic_required_discriminator(helpers):
    cls = helpers.create_model()
    unused_sub_a = helpers.create_model(cls, one=(str, ...))

    with pytest.raises(ValueError) as e:
        helpers.create_model(model=(generic(cls), ...))
    assert str(e.value) == 'at least one field with type typing.Literal is required'


def test_generic_required_discriminator_in_all_subclasses(helpers):
    cls = helpers.create_model()
    unused_sub_a = helpers.create_model(cls, name='A', one=(Literal['a'], 'a'))
    unused_sub_b = helpers.create_model(cls, name='B')

    with pytest.raises(ValueError) as e:
        helpers.create_model(model=(generic(cls), ...))
    assert str(e.value) == 'B. discriminator field one is required'


def test_generic_required_discriminator_type_as_literal(helpers):
    cls = helpers.create_model()
    unused_sub_a = helpers.create_model(cls, name='C', one=(Literal['a'], 'a'))
    unused_sub_b = helpers.create_model(cls, name='D', one=(str, ...))

    with pytest.raises(ValueError) as e:
        helpers.create_model(model=(generic(cls), ...))
    assert str(e.value) == 'D. discriminator field one must be of type typing.Literal'


def test_generic_requires_discriminator_type_as_literal_in_superclass(helpers):
    cls = helpers.create_model(name='E', one=(str, ...))
    unused_sub_a = helpers.create_model(cls, one=(Literal['a'], 'a'))
    unused_sub_b = helpers.create_model(cls, one=(Literal['b'], 'b'))

    with pytest.raises(ValueError) as e:
        helpers.create_model(model=(generic(cls), ...))
    assert str(e.value) == 'E. discriminator field one must be of type typing.Literal'


def test_reference(subtests, helpers):
    cls = helpers.create_model(kind='Y', field1=(str, ...), field2=(str, ...))
    root_cls = helpers.create_model(field3=(Annotated[reference(cls), expand_obj()], ...))
    context = {'Y': {'refName': {'spec': {'field1': 'foo', 'field2': 'bar'}}}}

    with subtests.test('resolve reference'):
        actual = root_cls.model_validate({'field3': 'refName'}, context=context)
        assert isinstance(actual.field3, cls)
        assert actual.field3.field1 == 'foo'
        assert actual.field3.field2 == 'bar'

    with subtests.test('validation error: reference not found'):
        with pytest.raises(ValidationError) as e:
            root_cls.model_validate({'field3': 'refName2'}, context=context)
        assert helpers.simplified_errors(e) == [('reference.not_found', ('field3',))]

    with subtests.test('validation error: override forbidden for field'):
        with pytest.raises(ValidationError) as e:
            root_cls.model_validate({'field3': {'refName': {'field1': 'baz'}}}, context=context)
        assert helpers.simplified_errors(e) == [('extra_forbidden', ('field3', 'field1'))]


def test_reference_overridable(subtests, helpers):
    cls = helpers.create_model(kind='Y', field1=(str, ...), field2=(Annotated[str, overridable], ...))
    root_cls = helpers.create_model(field3=(Annotated[reference(cls), expand_obj()], ...))
    context = {'Y': {'refName': {'spec': {'field1': 'foo', 'field2': 'bar'}}}}

    with subtests.test('resolve reference'):
        actual = root_cls.model_validate({'field3': 'refName'}, context=context)
        assert isinstance(actual.field3, cls)
        assert actual.field3.field1 == 'foo'
        assert actual.field3.field2 == 'bar'

    with subtests.test('validation error: reference not found'):
        with pytest.raises(ValidationError) as e:
            root_cls.model_validate({'field3': 'refName2'}, context=context)
        assert helpers.simplified_errors(e) == [('reference.not_found', ('field3',))]

    with subtests.test('override allowed field'):
        actual = root_cls.model_validate({'field3': {'refName': {'field2': 'baz'}}}, context=context)
        assert isinstance(actual.field3, cls)
        assert actual.field3.field1 == 'foo'
        assert actual.field3.field2 == 'baz'

    with subtests.test('validation error: override forbidden for field'):
        with pytest.raises(ValidationError) as e:
            root_cls.model_validate({'field3': {'refName': {'field1': 'baz'}}}, context=context)
        assert helpers.simplified_errors(e) == [('extra_forbidden', ('field3', 'field1'))]


def test_optional_fields(subtests, helpers):
    cls = helpers.create_model(
        field1=(str, ...),
        field2=(str, ...),
        field3=(str, ...),
        field4=(Annotated[str, overridable], ...),
        field5=(Annotated[str, overridable], ...),
        field6=(Annotated[str, overridable], ...),
    )
    unused_sub_a = helpers.create_model(
        cls,
        field1=(str, ...),
        field2=(int, ...),
        field4=(int, ...),
        field6=(Annotated[int, overridable], ...),
    )

    with subtests.test('optional fields'):
        fields = optional_fields(cls, include_fields={'field2'}, exclude_fields={'field3', 'field5'})
        assert fields.keys() == {'field2', 'field4', 'field6'}

    root_cls = pydantic.create_model('root_cls', __base__=BaseModel, **fields)

    with subtests.test('create instance without fields'):
        actual = root_cls()
        assert actual.field2 is None
        assert actual.field4 is None
        assert actual.field6 is None

    with subtests.test('create instance with all fields'):
        actual = root_cls(field2='foo', field4='bar', field6='baz')
        assert actual.field2 == 'foo'
        assert actual.field4 == 'bar'
        assert actual.field6 == 'baz'

    with subtests.test('create instance with overridden fields'):
        actual = root_cls(field2=123, field6=789)
        assert actual.field2 == 123
        assert actual.field4 is None
        assert actual.field6 == 789  # is overridable in subclass

    with subtests.test('validation error: not-overridable in subclass'):
        with pytest.raises(ValidationError) as e:
            root_cls(field4=456)
        assert helpers.simplified_errors(e) == [('string_type', ('field4',))]

    with subtests.test('validation error: extra field forbidden'):
        with pytest.raises(ValidationError) as e:
            root_cls(field1='foo')
        assert helpers.simplified_errors(e) == [('extra_forbidden', ('field1',))]


def case(func, name=None, params=None, expected=None, errors=None):
    """Create a test case for the expanded model."""

    kv_cls = pydantic.create_model('KeyValue', __base__=BaseModel, key=(str, ...), value=(Optional[str], None))
    annotated = {
        expand_obj: Annotated[kv_cls, expand_obj('key')],
        expand_dict: Annotated[dict[str, kv_cls], expand_dict('key')],
        expand_list: Annotated[list[kv_cls], expand_list('key')],
    }[func]

    model = pydantic.create_model('Model', __base__=BaseModel, field=(annotated, ...))
    return pytest.param(model, params, expected, errors, id=name)


@pytest.mark.parametrize(
    ('model', 'params', 'expected', 'errors'),
    [
        case(
            expand_obj,
            'just a string key',
            params='foo',
            expected={
                'key': 'foo',
                'value': None,
            },
        ),
        case(
            expand_obj,
            'override value',
            params={
                'foo': {
                    'value': 'bar',
                }
            },
            expected={
                'key': 'foo',
                'value': 'bar',
            },
        ),
        case(
            expand_obj,
            'provide full object',
            params={
                'key': 'foo',
                'value': 'bar',
            },
            expected={
                'key': 'foo',
                'value': 'bar',
            },
        ),
        case(
            expand_obj,
            'validation error: invalid model type',
            params=[
                'foo',
            ],
            errors=[
                {
                    'loc': ('field',),
                    'msg': 'Input should be a valid dictionary or instance of KeyValue',
                    'type': 'model_type',
                }
            ],
        ),
        case(
            expand_obj,
            'validation error: unexpected keys',
            params={
                'foo': 'bar',
            },
            errors=[
                {
                    'loc': ('field', 'key'),
                    'msg': 'Field required',
                    'type': 'missing',
                },
                {
                    'loc': ('field', 'foo'),
                    'msg': 'Extra inputs are not permitted',
                    'type': 'extra_forbidden',
                },
            ],
        ),
        case(
            expand_list,
            'list of mixed inputs',
            params=[
                'val1',
                'val1',
                {
                    'val2': {
                        'value': 'foo',
                    }
                },
                {
                    'key': 'val3',
                    'value': 'bar',
                },
            ],
            expected=[
                {
                    'key': 'val1',
                    'value': None,
                },
                {
                    'key': 'val1',
                    'value': None,
                },
                {
                    'key': 'val2',
                    'value': 'foo',
                },
                {
                    'key': 'val3',
                    'value': 'bar',
                },
            ],
        ),
        case(
            expand_list,
            'dict of mixed inputs as list',
            params={
                'val1': {},
                'val2': {
                    'value': 'foo',
                },
                'val3': {
                    'key': 'val4',
                    'value': 'bar',
                },
            },
            expected=[
                {
                    'key': 'val1',
                    'value': None,
                },
                {
                    'key': 'val2',
                    'value': 'foo',
                },
                {
                    'key': 'val3',
                    'value': 'bar',
                },
            ],
        ),
        case(
            expand_list,
            'validation error: not a list',
            params='foo',
            errors=[
                {
                    'loc': ('field',),
                    'msg': 'Input should be a valid list',
                    'type': 'list_type',
                }
            ],
        ),
        case(
            expand_list,
            'validation error: invalid model type',
            params={
                'foo': 'bar',
            },
            errors=[
                {
                    'loc': ('field', 0),
                    'msg': 'Input should be a valid dictionary or instance of KeyValue',
                    'type': 'model_type',
                }
            ],
        ),
        case(
            expand_dict,
            'list of mixed inputs as dict',
            params=[
                'val1',
                {
                    'val2': {
                        'value': 'foo',
                    }
                },
                {
                    'key': 'val3',
                },
                {
                    'key': 'val4',
                    'value': 'bar',
                },
                {
                    'val5': {
                        'key': 'val6',
                        'value': 'baz',
                    }
                },
            ],
            expected={
                'val1': {
                    'key': 'val1',
                    'value': None,
                },
                'val2': {
                    'key': 'val2',
                    'value': 'foo',
                },
                'val3': {
                    'key': 'val3',
                    'value': None,
                },
                'val4': {
                    'key': 'val4',
                    'value': 'bar',
                },
                'val5': {
                    'key': 'val5',
                    'value': 'baz',
                },
            },
        ),
        case(
            expand_dict,
            'dict of mixed inputs',
            params={
                'val1': {},
                'val2': {
                    'value': 'foo',
                },
                'val3': {
                    'key': 'val4',
                },
            },
            expected={
                'val1': {
                    'key': 'val1',
                    'value': None,
                },
                'val2': {
                    'key': 'val2',
                    'value': 'foo',
                },
                'val3': {
                    'key': 'val3',
                    'value': None,
                },
            },
        ),
        case(
            expand_dict,
            'validation error: duplicated keys',
            params=[
                'val1',
                'val1',
            ],
            errors=[
                {
                    'type': 'dict.unique_keys',
                    'msg': "the dict has duplicated key 'val1'",
                    'loc': ('field',),
                }
            ],
        ),
        case(
            expand_dict,
            'validation error: unexpected keys',
            params=[
                {
                    'foo': 'bar',
                    'value': 'baz',
                }
            ],
            errors=[
                {
                    'type': 'missing',
                    'msg': 'Field required',
                    'loc': ('field', '0', 'key'),
                },
                {
                    'type': 'extra_forbidden',
                    'msg': 'Extra inputs are not permitted',
                    'loc': ('field', '0', 'foo'),
                },
            ],
        ),
        case(
            expand_dict,
            'validation error: not a dict',
            params='foo',
            errors=[
                {
                    'loc': ('field',),
                    'msg': 'Input should be a valid dictionary',
                    'type': 'dict_type',
                }
            ],
        ),
    ],
)
def test_expanded(model, params, expected, errors):
    def success():
        actual = model(field=params)

        assert actual.model_dump() == {'field': expected}

    def failure():
        with pytest.raises(ValidationError) as e:
            model(field=params)

        assert e.value.errors(include_url=False, include_context=False, include_input=False) == errors

    if errors:
        return failure()
    return success()
