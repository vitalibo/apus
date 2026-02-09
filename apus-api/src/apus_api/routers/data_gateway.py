from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import forge
from fastapi import APIRouter, Depends
from jinja2 import Template
from sqlalchemy import text
from sqlalchemy.orm.session import Session

from apus_api import deps, schemas
from apus_api.models import Identity
from apus_api.refl import create_model, create_response_model, path_arg, query_arg

if TYPE_CHECKING:
    from apus_shared.models import Resource

    from apus_api.models import DataGateway


class DataGatewayRouter(APIRouter):
    """A router for a Data Gateway."""

    def __init__(self, resource: Resource[DataGateway], identity) -> None:
        super().__init__()
        self.query_template = Template(resource.spec.query_template)
        self.response_model = create_response_model(resource.spec.response)
        {
            'GET': self.get,
            'POST': self.post,
        }[resource.spec.request.http_method](
            path=resource.spec.request.path,
            summary=resource.metadata.labels.get('summary', resource.metadata.name),
            description=resource.metadata.labels.get('description'),
            status_code=resource.spec.response.status_code,
            response_model=self.response_model,
            tags={k[4:]: v for k, v in resource.metadata.annotations.items() if k.startswith('tags/')},
            responses={
                '400': {
                    'model': schemas.ErrorResponse,
                    'description': 'Validation Error',
                    'content': schemas.ErrorResponse.BadRequest,
                },
            },
        )(forge.sign(*self._signature(resource.spec, identity))(self.handle))

    def handle(self, session: Session, **kwargs):
        query = self.query_template.render(**kwargs)

        with session.connection() as conn:
            result = conn.execute(text(query), kwargs)

        rows = result.fetchall()
        return self.response_model.from_rows(
            [dict(row._mapping) for row in rows],  # noqa: SLF001
        )

    @staticmethod
    def _signature(spec: DataGateway, identity):
        params = [
            forge.arg('session', type=Annotated[Session, Depends(deps.get_session(spec.connection))]),
            forge.arg('_', type=Annotated[Session, Depends(deps.strict_query_params)]),
            *[path_arg(x) for x in spec.request.path_parameters.values()],
            *[query_arg(x) for x in spec.request.query_parameters.values() if x.default is None],
        ]

        if spec.authentication is not None:
            params.append(forge.arg('identity', type=Annotated[Identity, Depends(identity)]))

        if spec.request.body is not None:
            params.append(forge.arg('body', type=create_model(spec.request.body)))

        return [
            *params,
            *[query_arg(x) for x in spec.request.query_parameters.values() if x.default is not None],
        ]
