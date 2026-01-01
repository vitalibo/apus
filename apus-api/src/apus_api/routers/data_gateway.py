from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated, Any

import forge
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm.session import Session

from apus_api import deps, schemas
from apus_api.refl import create_model, path_arg, query_arg, unpack_params

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
            responses={'400': {'model': schemas.ErrorResponse, 'description': 'Validation Error'}},
        )(forge.sign(*self._signature(resource.spec))(unpack_params(self.handle)))

    def handle(self, session: Session, params: dict[str, Any]):
        logging.info('params: %s', params)

        with session.connection() as conn:
            result = conn.execute(text(self.resource.spec.query_template))

        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]  # noqa: SLF001

    @staticmethod
    def _signature(spec: DataGateway):
        params = [
            forge.arg('session', type=Annotated[Session, Depends(deps.get_session(spec.connection))]),
            forge.arg('_', type=Annotated[Session, Depends(deps.strict_query_params)]),
            *[path_arg(x) for x in spec.request.path_parameters.values()],
            *[query_arg(x) for x in spec.request.query_parameters.values() if x.default is None],
        ]

        if spec.request.body is not None:
            params.append(forge.arg('body', type=create_model(spec.request.body)))

        return [
            *params,
            *[query_arg(x) for x in spec.request.query_parameters.values() if x.default is not None],
        ]
