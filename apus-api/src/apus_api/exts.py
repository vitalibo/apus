from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pyxis.streams import Stream
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from apus_api import schemas

if TYPE_CHECKING:
    from starlette.requests import Request

__all__ = [
    'register',
]


def register(app: FastAPI) -> None:
    """Register FastAPI extensions."""

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(500, internal_server_error_handler)

    app.add_middleware(BaseHTTPMiddleware, dispatch=http_request_id_middleware)
    override_openapi(app)


def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions and return a standardized JSON response."""

    return JSONResponse(
        status_code=exc.status_code,
        content=schemas.ErrorResponse(
            status=exc.status_code,
            message=exc.detail,
            errors=None,
            request_id=request.state.request_id,
        ).model_dump(exclude_none=True, by_alias=True),
    )


def request_validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors and return a standardized JSON response."""

    def key(error):
        return '.'.join(error['loc'])

    def value(errors):
        return schemas.Error(
            details=[schemas.Details(type=error['type'], msg=error['msg']) for error in errors],
            original=errors[0]['input'],
        )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=schemas.ErrorResponse(
            status=status.HTTP_400_BAD_REQUEST,
            message='Bad Request',
            errors=Stream.of(exc.errors()).group_by(key).map_values(value).to_dict(),
            request_id=request.state.request_id,
        ).model_dump(by_alias=True),
    )


def internal_server_error_handler(request: Request, exc: Exception):
    """Handle internal server errors and return a standardized JSON response."""

    logging.exception(exc)  # noqa: LOG004
    return http_exception_handler(
        request,
        StarletteHTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal Server Error'),
    )


async def http_request_id_middleware(request: Request, call_next):
    """Middleware to add X-RequestId header to requests and responses."""

    request_id = request.headers.get('X-Request-Id', str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers['X-Request-Id'] = request_id
    return response


def override_openapi(app: FastAPI) -> None:
    """Override OpenAPI schema generation to remove 422 responses."""

    def wrap():
        if app.openapi_schema:
            return app.openapi_schema

        app.openapi_schema = FastAPI.openapi(app)
        for method_item in app.openapi_schema.get('paths').values():
            for param in method_item.values():
                responses = param.get('responses')
                if '422' in responses:
                    del responses['422']

        response_schemas = app.openapi_schema['components']['schemas']
        for name in ['HTTPValidationError', 'ValidationError']:
            if name in response_schemas:
                del response_schemas[name]
        return app.openapi_schema

    app.openapi = wrap
