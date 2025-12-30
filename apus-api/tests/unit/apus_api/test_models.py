from apus_api.models import PathParameter, QueryParameter, Request
from apus_shared.resources import resource_as_objs


def test_request(subtests):
    objs = resource_as_objs(__file__, 'data/requests.yaml')

    with subtests.test('request'):
        actual = Request(**objs[0])

        assert actual.path == '/my/path/{id}'
        assert actual.http_method == 'POST'
        assert actual.path_parameters.get('id') is not None

        assert isinstance(actual.path_parameters['id'], PathParameter)
        assert actual.path_parameters['id'].name == 'id'
        assert actual.path_parameters['id'].description is None
        assert actual.path_parameters['id'].type == 'integer'
        assert actual.path_parameters['id'].minimum is None
        assert {'minimum', 'maximum', 'exclusive_minimum', 'exclusive_maximum', 'multiple_of'}.issubset(
            dir(actual.path_parameters['id'])
        )
        assert not {'min_length', 'max_length', 'pattern'}.issubset(dir(actual.path_parameters['id']))

        assert actual.query_parameters.get('fields') is not None
        assert isinstance(actual.query_parameters['fields'], QueryParameter)
        assert actual.query_parameters['fields'].name == 'fields'
        assert actual.query_parameters['fields'].description is None
        assert actual.query_parameters['fields'].type == 'string'
        assert actual.query_parameters['fields'].min_length is None
        assert {'min_length', 'max_length', 'pattern'}.issubset(dir(actual.query_parameters['fields']))
        assert not {'minimum', 'maximum', 'exclusive_minimum', 'exclusive_maximum', 'multiple_of'}.issubset(
            dir(actual.query_parameters['fields'])
        )

        assert actual.query_parameters.get('expand') is not None
        assert isinstance(actual.query_parameters['expand'], QueryParameter)
        assert actual.query_parameters['expand'].name == 'expand'
        assert actual.query_parameters['expand'].description is None
        assert actual.query_parameters['expand'].type == 'boolean'
        assert not {'min_length', 'max_length', 'pattern'}.issubset(dir(actual.query_parameters['expand']))
        assert not {'minimum', 'maximum', 'exclusive_minimum', 'exclusive_maximum', 'multiple_of'}.issubset(
            dir(actual.query_parameters['expand'])
        )

        assert actual.body == {
            'properties': {
                'street_name': {
                    'type': 'string',
                },
                'street_type': {
                    'enum': ['Street', 'Avenue', 'Boulevard'],
                    'type': 'string',
                },
            },
            'type': 'object',
        }
