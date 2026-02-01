from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Request  # noqa: TC002
from fastapi.exceptions import RequestValidationError
from sqlalchemy import orm

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from apus_shared.models import Connection
    from sqlalchemy.orm import Session

__all__ = [
    'get_session',
    'strict_query_params',
]


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


def strict_query_params(request: Request):
    """Raise an error if there are any extra query parameters not defined in the route."""

    dependant = request.scope['route'].dependant
    allowed_params = [field.alias for field in dependant.query_params]
    extra_params = [param for param in request.query_params if param not in allowed_params]

    if extra_params:
        raise RequestValidationError(
            [
                {
                    'type': 'extra_forbidden',
                    'loc': ('query', param),
                    'msg': 'Extra inputs are not permitted',
                    'input': request.query_params[param],
                }
                for param in extra_params
            ]
        )
