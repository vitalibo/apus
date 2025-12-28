from typing import Literal

import pytest
from pydantic import ValidationError

from apus_shared import models
from apus_shared.models import BaseModel, Connection, Engine, create_resource
from unit.apus_shared.helpers import create_model, extract_errors, resource_as_objs

Resource = create_resource()


def test_create_resource():  # noqa: PLR0915
    cls_one = create_model(BaseModel, 'v1', 'One', one=(str, ...))
    cls_one_v2 = create_model(BaseModel, 'v2', 'One', one=(int, ...))
    cls_second = create_model(BaseModel, 'v1', 'Second', second=(str, ...))
    cls_third = create_model(BaseModel, 'v1', 'Third', type=(Literal['super'], ...))
    cls_third_sub_a = create_model(cls_third, type=(Literal['sub_a'], ...), value=(str, ...))
    cls_third_sub_b = create_model(cls_third, type=(Literal['sub_b'], ...), value=(int, ...))
    cls_fourth = create_model(BaseModel, 'v1', 'Fourth')
    cls_fourth_sub_a = create_model(cls_fourth, type=(Literal['sub_a'], ...))
    cls_fifth = create_model(BaseModel, 'v1', 'Fifth')

    resource = create_resource()

    actual = resource(**create_json_resource(api_version='v1', kind='One', spec={'one': 'foo'}))
    assert isinstance(actual.root, models.Resource)
    assert actual.root.api_version == 'v1'
    assert actual.root.kind == 'One'
    assert actual.root.metadata.name == 'One name'
    assert actual.root.metadata.namespace == 'test'
    assert actual.root.metadata.labels == {'env': 'test', 'app': 'test'}
    assert actual.root.metadata.annotations == {'apus/class': 'One'}
    assert isinstance(actual.root.spec, cls_one)
    assert actual.root.spec.one == 'foo'
    actual = resource(**create_json_resource(api_version='v2', kind='One', spec={'one': '123'}))
    assert isinstance(actual.root.spec, cls_one_v2)
    assert actual.root.spec.one == 123
    actual = resource(**create_json_resource(api_version='v1', kind='Second', spec={'second': '123'}))
    assert isinstance(actual.root.spec, cls_second)
    assert actual.root.spec.second == '123'
    actual = resource(**create_json_resource(api_version='v1', kind='Third', spec={'type': 'super'}))
    assert isinstance(actual.root.spec, cls_third)
    assert actual.root.spec.type == 'super'
    actual = resource(**create_json_resource(api_version='v1', kind='Third', spec={'type': 'sub_a', 'value': 'qwer'}))
    assert isinstance(actual.root.spec, cls_third_sub_a)
    assert actual.root.spec.type == 'sub_a'
    assert actual.root.spec.value == 'qwer'
    actual = resource(**create_json_resource(api_version='v1', kind='Third', spec={'type': 'sub_b', 'value': 123}))
    assert isinstance(actual.root.spec, cls_third_sub_b)
    assert actual.root.spec.type == 'sub_b'
    assert actual.root.spec.value == 123
    actual = resource(**create_json_resource(api_version='v1', kind='Fourth', spec={'type': 'sub_a'}))
    assert isinstance(actual.root.spec, cls_fourth_sub_a)
    assert actual.root.spec.type == 'sub_a'
    with pytest.raises(ValidationError) as e:
        resource(**create_json_resource(api_version='v2', kind='One', spec={'one': 'foo'}))
    assert extract_errors(e) == [('int_parsing', ('One/v2', 'spec', 'one'))]
    with pytest.raises(ValidationError) as e:
        resource(**create_json_resource(api_version='v3', kind='One', spec={'one': 123}))
    assert extract_errors(e) == [('union_tag_invalid', ())]
    with pytest.raises(ValidationError) as e:
        resource(**create_json_resource(api_version='v1', kind='Third', spec={'type': 'sub_b', 'value': 'qwer'}))
    assert extract_errors(e) == [('int_parsing', ('Third/v1', 'spec', 'sub_b', 'value'))]
    with pytest.raises(ValidationError) as e:
        resource(**create_json_resource(api_version='v1', kind='Third', spec={'type': 'sub_b'}))
    assert extract_errors(e) == [('missing', ('Third/v1', 'spec', 'sub_b', 'value'))]
    with pytest.raises(ValidationError) as e:
        resource(**create_json_resource(api_version='v1', kind='Third', spec={'type': 'subclass_c', 'value': 'qwer'}))
    assert extract_errors(e) == [('union_tag_invalid', ('Third/v1', 'spec'))]
    assert cls_fifth is not None


def test_connection(subtests):
    objs = resource_as_objs(__file__, 'data/connections.yaml')

    with subtests.test('mysql'):
        resource = Resource(**objs[0]).root

        assert resource.api_version == 'apus/v1'
        assert resource.kind == 'Connection'
        assert resource.metadata.name == 'MyConnection1'
        assert isinstance(resource.spec, Connection)
        assert resource.spec.engine == Engine.MYSQL
        assert resource.spec.host == 'mysql.example.com'
        assert resource.spec.port == 3306
        assert resource.spec.username == 'root'
        assert resource.spec.password == '5ecr3t'  # pragma: allowlist secret # noqa: S105
        assert resource.spec.database == 'mydb'
        assert resource.spec.properties == {
            'useUnicode': 'true',
            'characterEncoding': 'UTF-8',
        }

    with subtests.test('postgres'):
        resource = Resource(**objs[1]).root

        assert resource.api_version == 'apus/v1'
        assert resource.kind == 'Connection'
        assert resource.metadata.name == 'MyConnection2'
        assert isinstance(resource.spec, Connection)
        assert resource.spec.engine == Engine.POSTGRESQL
        assert resource.spec.host == 'postgres.example.com'
        assert resource.spec.port == 5432
        assert resource.spec.username == 'admin'
        assert resource.spec.password == '5ecr3t'  # pragma: allowlist secret # noqa: S105
        assert resource.spec.database == 'postgres'
        assert resource.spec.properties == {}

    with subtests.test('snowflake'):
        resource = Resource(**objs[2]).root

        assert resource.api_version == 'apus/v1'
        assert resource.kind == 'Connection'
        assert resource.metadata.name == 'MyConnection3'
        assert isinstance(resource.spec, Connection)
        assert resource.spec.engine == Engine.SNOWFLAKE
        assert resource.spec.host == 'myaccount.snowflakecomputing.com'
        assert resource.spec.port == 443
        assert resource.spec.username == 'admin'
        assert resource.spec.password is None
        assert resource.spec.private_key == 'MIIEvQIBADANBgkqhkiG9w0BAQEFAASC...'  # pragma: allowlist secret
        assert resource.spec.database == 'DWH'
        assert resource.spec.warehouse == 'COMPUTE_WH'
        assert resource.spec.role == 'SYSADMIN'


def create_json_resource(api_version, kind, spec):
    """Create an input dictionary for the resource model."""

    return {
        'apiVersion': api_version,
        'kind': kind,
        'metadata': {
            'name': f'{kind} name',
            'namespace': 'test',
            'labels': {
                'env': 'test',
                'app': 'test',
            },
            'annotations': {
                'apus/class': kind,
            },
        },
        'spec': spec,
    }
