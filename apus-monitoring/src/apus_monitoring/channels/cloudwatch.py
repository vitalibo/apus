import boto3
from apus_shared.models import Resource

from apus_monitoring.channels import ChannelHandler
from apus_monitoring.models import BusinessMonitor, CloudWatchChannel


class CloudWatchChannelHandler(ChannelHandler):
    """Send alerts to CloudWatch as custom metrics."""

    BATCH_SIZE = 1000

    def __init__(self, monitor: Resource[BusinessMonitor], channel: CloudWatchChannel) -> None:
        super().__init__(monitor, channel)
        self._cloudwatch = boto3.client('cloudwatch')

    def send(self, alerts: list[dict]) -> None:
        metric = self._monitor.spec.metric

        metric_data = [
            {
                'MetricName': metric.name or metric.field,
                'Dimensions': [
                    {
                        'Name': dimension.name or dimension.field,
                        'Value': str(alert[dimension.field]),
                    }
                    for dimension in self._monitor.spec.dimensions.values()
                ],
                'Value': float(alert[metric.field]),
            }
            for alert in alerts
        ]

        for i in range(0, len(metric_data), self.BATCH_SIZE):
            self._cloudwatch.put_metric_data(
                Namespace=self._channel.namespace,
                MetricData=metric_data[i : i + self.BATCH_SIZE],
            )
