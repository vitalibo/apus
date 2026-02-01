from unittest import mock

import sqlalchemy
from sqlalchemy import text

from apus_api.deps import get_session


def test_get_session():
    engine = sqlalchemy.create_engine('sqlite:///:memory:')
    mock_connection = mock.Mock()
    mock_connection.create_engine.return_value = engine

    session = next(get_session(mock_connection)())

    actual = session.execute(text('SELECT 123'))
    assert actual.scalar() == 123
