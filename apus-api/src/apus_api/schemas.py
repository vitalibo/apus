from typing import Annotated, Any, ClassVar, Optional

from apus_shared.models import BaseModel
from pydantic import Field


class Details(BaseModel):
    """Error details model."""

    type: str
    msg: str


class Error(BaseModel):
    """Error model."""

    details: list[Details]
    original: Any


class ErrorResponse(BaseModel):
    """FastAPI error response model."""

    status: int
    message: str
    errors: Annotated[Optional[dict[str, Error]], Field(None)]
    request_id: Annotated[str, Field(..., serialization_alias='requestId')]

    BadRequest: ClassVar = {
        'application/json': {
            'schema': {
                'example': {
                    'status': 400,
                    'message': 'Bad Request',
                    'errors': {
                        'query.intParam': {
                            'details': [
                                {
                                    'type': 'int_parsing',
                                    'msg': 'Input should be a valid integer, unable to parse string as an integer',
                                }
                            ],
                            'original': 'abc',
                        }
                    },
                    'requestId': 'e37a362f-75af-4031-ba99-c922206b0f2b',
                }
            }
        }
    }

    Unauthorized: ClassVar = {
        'application/json': {
            'schema': {
                'example': {
                    'status': 401,
                    'message': 'Unauthorized',
                    'requestId': 'e37a362f-75af-4031-ba99-c922206b0f2b',
                }
            }
        }
    }


class AccessTokenResponse(BaseModel):
    """AccessToken response model."""

    access_token: str
    token_type: str
    expires_in: int

    model_config: ClassVar = {
        'json_schema_extra': {
            'example': {
                'access_token': (
                    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.'
                    'eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc3MDUwMDYxMn0.'
                    'z5sTIifGn8dyTrJiKTtNj6a1JS25q3CG7ZkcBhTksqY'  # pragma: allowlist secret
                ),
                'token_type': 'Bearer',
                'expires_in': 3600,
            }
        }
    }
