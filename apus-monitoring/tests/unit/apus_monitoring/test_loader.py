from pyxis.config import Config
from pyxis.resources import resource

from apus_monitoring.loader import load_monitors


def test_load_monitors():
    config = Config({'args': {'config_file': resource(__file__, 'data/load_monitors.json')}})
    actual = load_monitors(config)

    assert len(actual) == 1
    assert actual[0].metadata.name == 'monitor'
    assert actual[0].spec.connection.host == 'localhost'
    assert actual[0].spec.channels[0].type == 'cloudwatch'
    assert actual[0].spec.channels[1].type == 'slack'
    assert actual[0].spec.channels[1].channels == ['foo', 'bar']
