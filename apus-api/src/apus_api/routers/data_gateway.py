from apus_api.models import Resource, DataGateway
from fastapi import APIRouter


class DataGatewayRouter(APIRouter):
    """A router for a Data Gateway."""

    def __init__(self, resource: Resource[DataGateway]) -> None:
        super().__init__()
        self.resource = resource
