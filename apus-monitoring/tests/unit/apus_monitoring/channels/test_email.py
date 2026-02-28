import base64
import re
from unittest import mock

from pyxis import resources
from pyxis.resources import load_json, load_text

from apus_monitoring.channels.email import EmailChannelHandler
from apus_monitoring.models import Resource


@mock.patch('smtplib.SMTP_SSL')
def test_send(mock_smtp):
    resource = Resource(**load_json(__file__, 'data/email/business_monitor.json')).root
    mock_smtp.return_value.__enter__.return_value = mock_smtp
    handler = EmailChannelHandler(resource, resource.spec.channels[0])

    handler.send(
        [{'dim1': f'value_{i}1', 'dim2': f'value_{i}2', 'dim3': f'value_{i}3', 'metric1': i * 1.23} for i in range(3)]
    )

    mock_smtp.login.assert_called_once_with(user='test', password='123')  # noqa: S106
    msg = mock_smtp.sendmail.mock_calls[0].kwargs['msg']
    msg_parts = msg.split('\n\n')
    assert base64.b64decode(msg_parts[2]).decode() == load_text(__file__, 'data/email/smtp_ssl_sendmail.html')
    msg = msg.replace(msg_parts[2], '<base64 encoded html>')
    msg = re.sub(r'===============[^=]+==', '===============<random boundary>==', msg)
    assert msg == resources.load_text(__file__, 'data/email/smtp_ssl_sendmail.txt')
