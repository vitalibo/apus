from apus_api.cdk.stack import ApiStackBuilder  # noqa: F401
from apus_shared.cdk import stack
from aws_cdk import Stack


class ApusStack(Stack):
    """Unified CDK stack that dynamically builds resources based on configuration."""

    def __init__(self, scope: Stack, construct_id: str, resources, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        for builder in stack.builders:
            builder.build(self, resources)
