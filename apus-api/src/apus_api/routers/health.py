from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from starlette import status


class HealthRouter(APIRouter):
    """Router for health check endpoint."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, include_in_schema=False)

        self.get('/health', status_code=status.HTTP_200_OK, response_class=PlainTextResponse)(self.health)

    @staticmethod
    async def health():
        return 'up'
