import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import jinja2
from apus_shared.models import Resource
from pyxis.resources import load_text

from apus_monitoring.channels import ChannelHandler
from apus_monitoring.models import BusinessMonitor, EmailChannel


class EmailChannelHandler(ChannelHandler):
    """A channel handler for sending alerts via email."""

    def __init__(self, monitor: Resource[BusinessMonitor], channel: EmailChannel) -> None:
        super().__init__(monitor, channel)
        self._template = jinja2.Template(load_text(__file__, 'templates/email.html.jinja2'))

    def send(self, alerts: list[dict]) -> None:
        with smtplib.SMTP_SSL(
            host=self._channel.host, port=self._channel.port, context=ssl.create_default_context()
        ) as smtp:
            smtp.login(user=self._channel.username, password=self._channel.password)

            msg = MIMEMultipart('alternative')
            msg['From'] = self._channel.username
            msg['To'] = ','.join(self._channel.recipients)
            msg['Subject'] = f'[APUS] {self._monitor.metadata.name}'
            msg.attach(MIMEText(self._template.render(monitor=self._monitor, alerts=alerts), 'html'))

            smtp.sendmail(from_addr=self._channel.username, to_addrs=self._channel.recipients, msg=msg.as_string())
