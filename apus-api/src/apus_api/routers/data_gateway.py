from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Annotated, Any

import forge
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm.session import Session

from apus_api import deps
from apus_api.utils import create_model, path_arg, query_arg

if TYPE_CHECKING:
    from apus_shared.models import Resource

    from apus_api.models import DataGateway


class DataGatewayRouter(APIRouter):
    """A router for a Data Gateway."""

    def __init__(self, resource: Resource[DataGateway]) -> None:
        super().__init__()
        self.resource = resource
        {
            'GET': self.get,
            'POST': self.post,
        }[resource.spec.request.http_method](
            path=resource.spec.request.path,
            summary=resource.metadata.labels.get('summary', resource.metadata.name),
            description=resource.metadata.labels.get('description'),
            tags={k[4:]: v for k, v in resource.metadata.annotations.items() if k.startswith('tags/')},
        )(forge.sign(*self._signature(resource.spec))(self._unpack_params(self.handle)))

    def handle(self, session: Session, params: dict[str, Any]):
        logging.info('params: %s', params)
        with session.connection() as conn:
            result = conn.execute(text(self.resource.spec.query_template))
        return result.fetchall()

    @staticmethod
    def _signature(spec: DataGateway):
        params = [forge.arg('session', type=Annotated[Session, Depends(deps.get_session(spec.connection))])]

        params.extend(path_arg(v) for v in spec.request.path_parameters.values())
        params.extend(
            query_arg(v) for v in sorted(spec.request.query_parameters.values(), key=lambda v: not v.required)
        )

        if spec.request.body is not None:
            params.append(forge.arg('body', type=create_model(spec.request.body)))

        return params

    @staticmethod
    def _unpack_params(func):
        def wrapper(session: Session, **kwargs):
            params = defaultdict(dict)
            for key, values in kwargs.items():
                group, *path = key.split('_', 1)
                if path:
                    params[group][path[0]] = values
                else:
                    params[group] = values

            return func(session=session, params=params)

        return wrapper
