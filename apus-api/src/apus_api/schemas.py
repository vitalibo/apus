from typing import Annotated, Any, ClassVar, Optional

from pydantic import Field

from apus_shared.models import BaseModel


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

    model_config: ClassVar = {
        'json_schema_extra': {
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
