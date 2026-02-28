from unittest import mock

from apus_monitoring.channels import dispatch


def test_dispatch():
    mock_monitor = mock.Mock()
    mock_cloudwatch = mock.Mock()
    mock_cloudwatch.type = 'cloudwatch'
    mock_email = mock.Mock()
    mock_email.type = 'email'
    mock_slack = mock.Mock()
    mock_slack.type = 'slack'
    mock_monitor.spec.channels = [mock_cloudwatch, mock_email, mock_slack]

    with (
        mock.patch('apus_monitoring.channels.cloudwatch.CloudWatchChannelHandler') as mock_cloudwatch_handler,
        mock.patch('apus_monitoring.channels.email.EmailChannelHandler') as mock_email_handler,
        mock.patch('apus_monitoring.channels.slack.SlackChannelHandler') as mock_slack_handler,
    ):
        actual = list(dispatch(mock_monitor))

        assert actual[0] == mock_cloudwatch_handler.return_value
        mock_cloudwatch_handler.assert_called_with(mock_monitor, mock_cloudwatch)
        assert actual[1] == mock_email_handler.return_value
        mock_email_handler.assert_called_with(mock_monitor, mock_email)
        assert actual[2] == mock_slack_handler.return_value
        mock_slack_handler.assert_called_with(mock_monitor, mock_slack)
