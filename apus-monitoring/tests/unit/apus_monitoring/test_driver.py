import importlib
from unittest import mock

import pytest


def test_driver():
    with (
        mock.patch('pyxis.aws.config.ConfigFactory.default_application') as mock_config_factory,
        mock.patch('apus_monitoring.loader.load_monitors') as mock_load_monitors,
        mock.patch('apus_monitoring.executor.Executor') as mock_executor_factory,
        mock.patch('apus_monitoring.channels.dispatch') as mock_dispatch,
    ):
        from apus_monitoring import driver  # noqa: PLC0415

        mock_config_factory.reset_mock()
        importlib.reload(driver)
        mock_monitor1 = mock.Mock()
        mock_monitor2 = mock.Mock()
        mock_load_monitors.return_value = [mock_monitor1, mock_monitor2]
        mock_executor = mock.Mock()
        mock_future1 = mock.Mock()
        mock_future1.result.return_value = ['alert1', 'alert2']
        mock_future2 = mock.Mock()
        mock_future2.result.return_value = ['alert3']
        mock_executor.futures.return_value = [(mock_future1, mock_monitor1), (mock_future2, mock_monitor2)]
        mock_executor_factory.return_value = mock_executor
        mock_channel1 = mock.Mock()
        mock_channel2 = mock.Mock()
        mock_channel3 = mock.Mock()
        mock_dispatch.side_effect = [[mock_channel1], [mock_channel2, mock_channel3]]

        driver.main()

        mock_config_factory.assert_called_once_with()
        mock_load_monitors.assert_called_once_with(mock_config_factory.return_value)
        mock_executor_factory.assert_called_once_with(max_workers=2)
        mock_executor.submit.assert_has_calls([mock.call(mock_monitor1), mock.call(mock_monitor2)])
        mock_future1.result.assert_called_once_with()
        mock_future2.result.assert_called_once_with()
        mock_channel1.send.assert_called_once_with(['alert1', 'alert2'])
        mock_channel2.send.assert_called_once_with(['alert3'])
        mock_channel3.send.assert_called_once_with(['alert3'])


def test_driver_errors():
    with (
        mock.patch('pyxis.aws.config.ConfigFactory.default_application') as mock_config_factory,
        mock.patch('apus_monitoring.loader.load_monitors') as mock_load_monitors,
        mock.patch('apus_monitoring.executor.Executor') as mock_executor_factory,
        mock.patch('apus_monitoring.channels.dispatch') as mock_dispatch,
    ):
        from apus_monitoring import driver  # noqa: PLC0415

        mock_config_factory.reset_mock()
        importlib.reload(driver)
        mock_monitor1 = mock.Mock()
        mock_monitor2 = mock.Mock()
        mock_load_monitors.return_value = [mock_monitor1, mock_monitor2]
        mock_executor = mock.Mock()
        mock_future1 = mock.Mock()
        mock_future1.result.side_effect = Exception('monitor1 failed')
        mock_future2 = mock.Mock()
        mock_future2.result.return_value = ['alert3']
        mock_executor.futures.return_value = [(mock_future1, mock_monitor1), (mock_future2, mock_monitor2)]
        mock_executor_factory.return_value = mock_executor
        mock_channel2 = mock.Mock()
        mock_channel2.send.side_effect = Exception('channel2 failed')
        mock_channel3 = mock.Mock()
        mock_dispatch.return_value = [mock_channel2, mock_channel3]

        with pytest.raises(RuntimeError, match='one or more errors occurred during execution') as e:
            driver.main()

        assert e.value.args[1] == [mock_future1.result.side_effect, mock_channel2.send.side_effect]
        mock_config_factory.assert_called_once_with()
        mock_load_monitors.assert_called_once_with(mock_config_factory.return_value)
        mock_executor_factory.assert_called_once_with(max_workers=2)
        mock_executor.submit.assert_has_calls([mock.call(mock_monitor1), mock.call(mock_monitor2)])
        mock_future1.result.assert_called_once_with()
        mock_future2.result.assert_called_once_with()
        mock_channel2.send.assert_called_once_with(['alert3'])
        mock_channel3.send.assert_called_once_with(['alert3'])
