from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import orm

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from apus_shared.models import Connection
    from sqlalchemy.orm import Session


def get_session(connection: Connection) -> Callable[[], Generator[Session, None, None]]:
    """Get a scoped session from a session factory."""

    engine = connection.create_engine()
    sessionmaker = orm.sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def wrap() -> Generator[Session, None, None]:
        session = None
        try:
            session = sessionmaker()
            yield session
        finally:
            session.close()

    return wrap
