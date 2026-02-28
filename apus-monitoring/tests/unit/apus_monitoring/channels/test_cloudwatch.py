import json
from unittest import mock

from pyxis.resources import load_json

from apus_monitoring.channels.cloudwatch import CloudWatchChannelHandler
from apus_monitoring.models import Resource


@mock.patch('boto3.client')
def test_send(mock_client):
    resource = Resource(**load_json(__file__, 'data/cloudwatch/business_monitor.json')).root
    mock_cloudwatch = mock_client.return_value
    handler = CloudWatchChannelHandler(resource, resource.spec.channels[0])
    handler.BATCH_SIZE = 2

    handler.send(
        [{'dim1': f'value_{i}1', 'dim2': f'value_{i}2', 'dim3': f'value_{i}3', 'metric1': i * 1.23} for i in range(3)]
    )

    assert json.loads(json.dumps(mock_cloudwatch.put_metric_data.mock_calls)) == load_json(
        __file__, 'data/cloudwatch/put_metric_data.json'
    )
