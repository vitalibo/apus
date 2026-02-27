import abc
from typing import Generic, TypeVar

from apus_shared.models import Resource

from apus_monitoring.models import BusinessMonitor, Channel

T = TypeVar('T', bound=Channel)


class ChannelHandler(abc.ABC, Generic[T]):
    """Abstract base class for channel handlers."""

    def __init__(self, monitor: Resource[BusinessMonitor], channel: T) -> None:
        self._monitor = monitor
        self._channel = channel

    @abc.abstractmethod
    def send(self, alerts: list[dict]) -> None:
        """Sends the given alerts to the channel."""

    def __getattr__(self, item):
        return getattr(self._channel, item)


def dispatch(monitor: Resource[BusinessMonitor]):
    """Factory that yields a ChannelHandler for each channel on the monitor."""

    for channel in monitor.spec.channels:
        if channel.type == 'cloudwatch':
            from apus_monitoring.channels.cloudwatch import CloudWatchChannelHandler  # noqa: PLC0415

            yield CloudWatchChannelHandler(monitor, channel)
        elif channel.type == 'email':
            from apus_monitoring.channels.email import EmailChannelHandler  # noqa: PLC0415

            yield EmailChannelHandler(monitor, channel)
        elif channel.type == 'slack':
            from apus_monitoring.channels.slack import SlackChannelHandler  # noqa: PLC0415

            yield SlackChannelHandler(monitor, channel)
        else:
            raise ValueError(f'unresolved channel type: {channel.type}')
