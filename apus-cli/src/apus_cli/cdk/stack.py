from apus_api.cdk.stack import ApiStackBuilder  # noqa: F401
from apus_shared.cdk import builder_registry
from aws_cdk import App, Stack


class ApusStack(Stack):
    """Unified CDK stack that dynamically builds resources based on configuration."""

    def __init__(self, scope: App, construct_id: str, resources, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        for builder in builder_registry.builders:
            builder.build(self, resources)
