from unittest import mock

import sqlalchemy

from apus_monitoring.executor import Executor


def test_submit():
    mock_execute = mock.Mock()
    executor = Executor(max_workers=5)
    executor.execute = mock_execute
    mock_execute.side_effect = list(range(15))

    for i in range(10):
        resource = mock.Mock()
        resource.spec = f'monitor_{i}'
        executor.submit(resource)

    for future, resource in executor.futures():
        result = future.result()
        assert result < 10
        assert resource.spec.startswith('monitor_')


def test_execute():
    engine = sqlalchemy.create_engine('sqlite:///:memory:')
    mock_connection = mock.Mock()
    mock_connection.create_engine.return_value = engine
    mock_monitor = mock.Mock()
    mock_monitor.connection = mock_connection
    mock_monitor.query_template = 'SELECT 1 AS foo, 2 AS bar UNION ALL SELECT 3, 4'

    result = Executor.execute(mock_monitor)

    assert result == [{'bar': 2, 'foo': 1}, {'bar': 4, 'foo': 3}]
