from typing import Annotated, Literal, Optional

from apus_shared.fields import expand_dict, expand_list, expand_obj, overridable, reference  # noqa: TC002
from apus_shared.models import BaseModel, Connection, ScheduleStr  # noqa: TC002
from pydantic import Field

__all__ = [
    'BusinessMonitor',
    'Channel',
    'CloudWatchChannel',
    'Column',
    'Dimension',
    'EmailChannel',
    'Metric',
    'SlackChannel',
]


class Column(BaseModel):
    """An abstract class that represents a column in a table."""

    field: Annotated[str, Field(..., min_length=1, max_length=64)]
    name: Annotated[Optional[str], Field(None, min_length=1, max_length=64)]
    description: Annotated[Optional[str], Field(None, min_length=1, max_length=256)]


class Metric(Column):
    """Represents a metric."""


class Dimension(Column):
    """Represents a dimension."""


class Channel(BaseModel):
    """An abstract class that represents a channel."""

    __api_version__ = 'apus/v1'
    __kind__ = 'Channel'


class SlackChannel(Channel):
    """A channel for sending alerts via Slack."""

    type: Literal['slack']
    token: str
    channels: Annotated[Optional[list[str]], Field(None, min_length=1, max_length=16), overridable]


class EmailChannel(Channel):
    """A channel for sending alerts via email."""

    type: Literal['email']
    host: str
    port: int
    username: str
    password: str
    recipients: Annotated[Optional[list[str]], Field(None, min_length=1, max_length=16), overridable]


class CloudWatchChannel(Channel):
    """A channel for sending metrics to CloudWatch."""

    type: Literal['cloudwatch']
    namespace: Annotated[str, overridable]


class BusinessMonitor(BaseModel):
    """Represents a business monitor."""

    __api_version__ = 'apus/v1'
    __kind__ = 'BusinessMonitor'

    schedule: Annotated[ScheduleStr, ...]
    connection: Annotated[reference(Connection), expand_obj()]
    metric: Annotated[Metric, expand_obj('field')]
    dimensions: Annotated[dict[str, Dimension], expand_dict('field'), Field(min_length=0, max_length=16)]
    query_template: Annotated[str, ...]
    channels: Annotated[list[reference(Channel)], expand_list(), Field(min_length=1, max_length=16)]
