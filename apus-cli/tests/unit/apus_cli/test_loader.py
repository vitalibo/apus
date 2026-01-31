from pathlib import Path

import pytest
from pydantic import ValidationError
from pyxis.resources import load_yaml, load_yaml_all, resource

from apus_cli.loader import load_resources


def test_load_resources():
    resources = load_resources(
        Path(resource(__file__, 'data/loader/api')),
        Path(resource(__file__, 'data/loader/connections.yaml')),
    )

    actual = {r.metadata.name: r for r in resources}

    assert actual['MyEndpoint1'].model_dump() == load_yaml(__file__, 'data/loader/api/endpoints/endpoint1.yml')
    assert actual['MyEndpoint2'].model_dump() == load_yaml(__file__, 'data/loader/api/endpoints/endpoint2.yml')
    assert actual['MyConnection1'].model_dump() == load_yaml_all(__file__, 'data/loader/connections.yaml')[0]
    assert actual['MyConnection2'].model_dump() == load_yaml_all(__file__, 'data/loader/connections.yaml')[1]


def test_load_resources_unresolved():
    with pytest.raises(ValidationError) as e:
        load_resources(
            Path(resource(__file__, 'data/loader/api')),
        )

    assert e.value.errors()[0]['type'] == 'reference.not_found'
