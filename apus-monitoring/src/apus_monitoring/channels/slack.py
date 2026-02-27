import textwrap

import slack_sdk
from apus_shared.models import Resource
from slack_sdk.models import attachments, blocks

from apus_monitoring.channels import ChannelHandler
from apus_monitoring.models import BusinessMonitor, SlackChannel


class SlackChannelHandler(ChannelHandler):
    """A channel handler for sending alarms via Slack."""

    def __init__(self, monitor: Resource[BusinessMonitor], channel: SlackChannel) -> None:
        super().__init__(monitor, channel)
        self._client = slack_sdk.WebClient(token=channel.token)

    def send(self, alerts: list[dict]) -> None:
        def cell(row, *keys):
            values = {col.name or col.field: row[col.field] for col in keys}
            return '\n'.join((f'*{key}*\n{value}\n' for key, value in values.items()))

        monitor = self._monitor.spec
        for channel in self._channel.channels:
            self._client.chat_postMessage(
                channel=channel,
                text=f'[APUS] {self._monitor.metadata.name}',
                blocks=[
                    blocks.SectionBlock(
                        text=blocks.MarkdownTextObject(
                            text=textwrap.dedent(f"""
                            *{self._monitor.metadata.name}*

                            {self._monitor.metadata.annotations.get('description', '')}
                            """)
                        )
                    ),
                    blocks.DividerBlock(),
                    blocks.ContextBlock(
                        elements=[blocks.MarkdownTextObject(text='Sent by *APUS Monitoring*.')],
                    ),
                ],
                attachments=[
                    attachments.BlockAttachment(
                        color='#ff0000',
                        blocks=[
                            blocks.SectionBlock(
                                fields=[
                                    blocks.MarkdownTextObject(text=cell(alert, *monitor.dimensions.values())),
                                    blocks.MarkdownTextObject(text=cell(alert, monitor.metric)),
                                ]
                            ),
                            blocks.DividerBlock(),
                        ],
                    )
                    for alert in alerts
                ],
            )
