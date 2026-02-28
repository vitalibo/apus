import json
from unittest import mock

from pyxis.resources import load_json
from slack_sdk.models import JsonObject

from apus_monitoring.channels.slack import SlackChannelHandler
from apus_monitoring.models import Resource


@mock.patch('slack_sdk.WebClient')
def test_send(mock_client):
    resource = Resource(**load_json(__file__, 'data/slack/business_monitor.json')).root
    handler = SlackChannelHandler(resource, resource.spec.channels[0])

    handler.send(
        [{'dim1': f'value_{i}1', 'dim2': f'value_{i}2', 'dim3': f'value_{i}3', 'metric1': i * 1.23} for i in range(3)]
    )

    mock_client.assert_called_once_with(token='xoxb-1234567890  #pragma: allowlist secret')  # noqa: S106
    assert json.loads(json.dumps(mock_client.return_value.chat_postMessage.mock_calls, default=serde)) == load_json(
        __file__, 'data/slack/chat_postMessage.json'
    )


def serde(obj):
    return obj.to_dict() if isinstance(obj, JsonObject) else obj
